from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0004_resourcecategory_resourcetag_resource_tags"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Extend the search vector to include tag names (weight C).
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

                -- Trigger on tags M2M.
                CREATE TRIGGER resources_tags_search_vector_trigger
                AFTER INSERT OR DELETE
                ON resources_resource_tags
                FOR EACH ROW
                EXECUTE FUNCTION resources_resource_m2m_search_vector_refresh();

                -- Backfill existing rows.
                UPDATE resources_resource SET name = name;
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS resources_tags_search_vector_trigger ON resources_resource_tags;

                -- Restore the 0003 version of the compute function (without tags).
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

                UPDATE resources_resource SET name = name;
            """,
        ),
    ]
