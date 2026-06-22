from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "resources",
            "0013_resource_description_en_resource_description_mi_and_more",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop the old 3-arg compute function and recreate with _mi support.
                DROP FUNCTION IF EXISTS resources_resource_compute_search_vector(bigint, text, text);

                CREATE OR REPLACE FUNCTION resources_resource_compute_search_vector(
                    p_id bigint,
                    p_name text,
                    p_description text,
                    p_name_mi text DEFAULT '',
                    p_description_mi text DEFAULT ''
                ) RETURNS tsvector AS $$
                    SELECT
                        setweight(to_tsvector('english', COALESCE(p_name, '')), 'A')
                        || setweight(to_tsvector('english', COALESCE(p_description, '')), 'B')
                        || setweight(to_tsvector('simple',  COALESCE(p_name_mi, '')), 'A')
                        || setweight(to_tsvector('simple',  COALESCE(p_description_mi, '')), 'B')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(c.name, ' ')
                             FROM resources_resourcecomponent c
                             WHERE c.resource_id = p_id), '')), 'B')
                        || setweight(to_tsvector('simple', COALESCE(
                            (SELECT string_agg(c.name_mi, ' ')
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
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(t.name, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('simple', COALESCE(
                            (SELECT string_agg(t.name_mi, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C');
                $$ LANGUAGE sql;

                -- Update the row-level trigger to pass _mi columns.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := resources_resource_compute_search_vector(
                        NEW.id, NEW.name, NEW.description,
                        NEW.name_mi, NEW.description_mi
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                -- Recreate trigger to also fire on name_mi / description_mi changes.
                DROP TRIGGER IF EXISTS resources_resource_search_vector_trigger ON resources_resource;
                CREATE TRIGGER resources_resource_search_vector_trigger
                BEFORE INSERT OR UPDATE OF name, description, name_mi, description_mi
                ON resources_resource
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_update();

                -- Update the related-table refresh function to pass _mi columns.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(
                            id, name, description, name_mi, description_mi
                        )
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- Update the M2M refresh function to pass _mi columns.
                CREATE OR REPLACE FUNCTION resources_resource_m2m_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(
                            id, name, description, name_mi, description_mi
                        )
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- Recreate component trigger to also fire on name_mi.
                DROP TRIGGER IF EXISTS resources_component_search_vector_trigger ON resources_resourcecomponent;
                CREATE TRIGGER resources_component_search_vector_trigger
                AFTER INSERT OR UPDATE OF name, name_mi OR DELETE
                ON resources_resourcecomponent
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_refresh();

                -- Backfill: re-compute all search vectors (includes _mi columns, even if empty).
                UPDATE resources_resource SET name = name;
            """,
            reverse_sql="""
                -- Restore the previous 5-arg compute function (without _mi support).
                DROP FUNCTION IF EXISTS resources_resource_compute_search_vector(bigint, text, text, text, text);

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
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(t.name, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C');
                $$ LANGUAGE sql;

                CREATE OR REPLACE FUNCTION resources_resource_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := resources_resource_compute_search_vector(
                        NEW.id, NEW.name, NEW.description
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS resources_resource_search_vector_trigger ON resources_resource;
                CREATE TRIGGER resources_resource_search_vector_trigger
                BEFORE INSERT OR UPDATE OF name, description
                ON resources_resource
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_update();

                CREATE OR REPLACE FUNCTION resources_resource_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(id, name, description)
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                CREATE OR REPLACE FUNCTION resources_resource_m2m_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(id, name, description)
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS resources_component_search_vector_trigger ON resources_resourcecomponent;
                CREATE TRIGGER resources_component_search_vector_trigger
                AFTER INSERT OR UPDATE OF name OR DELETE
                ON resources_resourcecomponent
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_refresh();

                UPDATE resources_resource SET name = name;
            """,
        ),
    ]
