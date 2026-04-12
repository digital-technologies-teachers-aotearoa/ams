from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0002_resource_search_vector"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Compute the full search vector for a given resource.
                CREATE OR REPLACE FUNCTION resources_resource_compute_search_vector(
                    p_id bigint, p_name text, p_description text
                ) RETURNS tsvector AS $$
                    SELECT
                        setweight(to_tsvector('english', COALESCE(p_name, '')), 'A')
                        || setweight(to_tsvector('english', COALESCE(p_description, '')), 'B')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(c.name, ' ')
                             FROM resources_resourcecomponent c
                             WHERE c.resource_id = p_id), '')), 'B')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(u.first_name || ' ' || u.last_name, ' ')
                             FROM users_user u
                             INNER JOIN resources_resource_author_users m
                                 ON m.user_id = u.id
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(e.name, ' ')
                             FROM entities_entity e
                             INNER JOIN resources_resource_author_entities m
                                 ON m.entity_id = e.id
                             WHERE m.resource_id = p_id), '')), 'C');
                $$ LANGUAGE sql;

                -- Replace the BEFORE INSERT/UPDATE trigger function.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := resources_resource_compute_search_vector(
                        NEW.id, NEW.name, NEW.description
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                -- Trigger on resource row itself (replaces 0002 trigger).
                DROP TRIGGER IF EXISTS resources_resource_search_vector_trigger ON resources_resource;
                CREATE TRIGGER resources_resource_search_vector_trigger
                BEFORE INSERT OR UPDATE OF name, description
                ON resources_resource
                FOR EACH ROW
                EXECUTE FUNCTION resources_resource_search_vector_update();

                -- Refresh search_vector directly when related tables change.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(id, name, description)
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- Trigger on components table.
                CREATE TRIGGER resources_component_search_vector_trigger
                AFTER INSERT OR UPDATE OF name OR DELETE
                ON resources_resourcecomponent
                FOR EACH ROW
                EXECUTE FUNCTION resources_resource_search_vector_refresh();

                -- Refresh for M2M through tables.
                CREATE OR REPLACE FUNCTION resources_resource_m2m_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(id, name, description)
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- Trigger on author_users M2M.
                CREATE TRIGGER resources_author_users_search_vector_trigger
                AFTER INSERT OR DELETE
                ON resources_resource_author_users
                FOR EACH ROW
                EXECUTE FUNCTION resources_resource_m2m_search_vector_refresh();

                -- Trigger on author_entities M2M.
                CREATE TRIGGER resources_author_entities_search_vector_trigger
                AFTER INSERT OR DELETE
                ON resources_resource_author_entities
                FOR EACH ROW
                EXECUTE FUNCTION resources_resource_m2m_search_vector_refresh();

                -- Backfill existing rows.
                UPDATE resources_resource SET name = name;
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS resources_author_entities_search_vector_trigger ON resources_resource_author_entities;
                DROP TRIGGER IF EXISTS resources_author_users_search_vector_trigger ON resources_resource_author_users;
                DROP FUNCTION IF EXISTS resources_resource_m2m_search_vector_refresh();
                DROP TRIGGER IF EXISTS resources_component_search_vector_trigger ON resources_resourcecomponent;
                DROP FUNCTION IF EXISTS resources_resource_search_vector_refresh();
                DROP FUNCTION IF EXISTS resources_resource_compute_search_vector(bigint, text, text);

                -- Restore the original simple trigger function from 0002.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector :=
                        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
                        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                UPDATE resources_resource SET name = name;
            """,
        ),
    ]
