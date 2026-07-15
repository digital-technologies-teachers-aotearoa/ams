from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("resources", "0014_search_vector_mi"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Repoint the compute function at the translated (_en/_mi) columns.
                -- The base columns are a modeltranslation implementation detail
                -- (they mirror whichever language was active on the last save), so
                -- the English half now reads _en and the Maori half reads _mi.
                -- Parameter names change (_en), so drop before recreating.
                DROP FUNCTION IF EXISTS resources_resource_compute_search_vector(bigint, text, text, text, text);

                CREATE OR REPLACE FUNCTION resources_resource_compute_search_vector(
                    p_id bigint,
                    p_name_en text,
                    p_description_en text,
                    p_name_mi text DEFAULT '',
                    p_description_mi text DEFAULT ''
                ) RETURNS tsvector AS $$
                    SELECT
                        setweight(to_tsvector('english', COALESCE(p_name_en, '')), 'A')
                        || setweight(to_tsvector('english', COALESCE(p_description_en, '')), 'B')
                        || setweight(to_tsvector('simple',  COALESCE(p_name_mi, '')), 'A')
                        || setweight(to_tsvector('simple',  COALESCE(p_description_mi, '')), 'B')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(c.name_en, ' ')
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
                            (SELECT string_agg(t.name_en, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('simple', COALESCE(
                            (SELECT string_agg(t.name_mi, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('english', COALESCE(
                            (SELECT string_agg(t.abbreviation_en, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C')
                        || setweight(to_tsvector('simple', COALESCE(
                            (SELECT string_agg(t.abbreviation_mi, ' ')
                             FROM resources_resourcetag t
                             INNER JOIN resources_resource_tags m
                                 ON m.resourcetag_id = t.id
                             WHERE m.resource_id = p_id), '')), 'C');
                $$ LANGUAGE sql;

                -- Pass _en/_mi columns from the row-level trigger.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_update()
                RETURNS trigger AS $$
                BEGIN
                    NEW.search_vector := resources_resource_compute_search_vector(
                        NEW.id, NEW.name_en, NEW.description_en,
                        NEW.name_mi, NEW.description_mi
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                -- Fire on _en/_mi changes instead of the base columns.
                DROP TRIGGER IF EXISTS resources_resource_search_vector_trigger ON resources_resource;
                CREATE TRIGGER resources_resource_search_vector_trigger
                BEFORE INSERT OR UPDATE OF name_en, description_en, name_mi, description_mi
                ON resources_resource
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_update();

                -- Related-table refresh function passes _en/_mi columns.
                CREATE OR REPLACE FUNCTION resources_resource_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(
                            id, name_en, description_en, name_mi, description_mi
                        )
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- M2M refresh function passes _en/_mi columns.
                CREATE OR REPLACE FUNCTION resources_resource_m2m_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource SET search_vector =
                        resources_resource_compute_search_vector(
                            id, name_en, description_en, name_mi, description_mi
                        )
                    WHERE id = COALESCE(NEW.resource_id, OLD.resource_id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                -- Fire the component trigger on _en/_mi changes.
                DROP TRIGGER IF EXISTS resources_component_search_vector_trigger ON resources_resourcecomponent;
                CREATE TRIGGER resources_component_search_vector_trigger
                AFTER INSERT OR UPDATE OF name_en, name_mi OR DELETE
                ON resources_resourcecomponent
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_refresh();

                -- New: refresh dependent resources when a tag's name or abbreviation
                -- changes. The existing tag trigger is on the M2M through table and
                -- only fires on membership changes, so renaming a tag previously left
                -- stale text indexed on every resource carrying it.
                CREATE OR REPLACE FUNCTION resources_resourcetag_search_vector_refresh()
                RETURNS trigger AS $$
                BEGIN
                    UPDATE resources_resource r
                    SET search_vector = resources_resource_compute_search_vector(
                        r.id, r.name_en, r.description_en, r.name_mi, r.description_mi
                    )
                    FROM resources_resource_tags m
                    WHERE m.resource_id = r.id
                      AND m.resourcetag_id = COALESCE(NEW.id, OLD.id);
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS resources_resourcetag_search_vector_trigger ON resources_resourcetag;
                CREATE TRIGGER resources_resourcetag_search_vector_trigger
                AFTER UPDATE OF name_en, name_mi, abbreviation_en, abbreviation_mi
                ON resources_resourcetag
                FOR EACH ROW EXECUTE FUNCTION resources_resourcetag_search_vector_refresh();

                -- Re-index every row from the correct columns. name is no longer in
                -- the trigger's UPDATE OF list, so touch name_en instead.
                UPDATE resources_resource SET name_en = name_en;
            """,
            reverse_sql="""
                -- Restore the 0014 compute function reading the base columns.
                DROP FUNCTION IF EXISTS resources_resource_compute_search_vector(bigint, text, text, text, text);

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

                DROP TRIGGER IF EXISTS resources_resource_search_vector_trigger ON resources_resource;
                CREATE TRIGGER resources_resource_search_vector_trigger
                BEFORE INSERT OR UPDATE OF name, description, name_mi, description_mi
                ON resources_resource
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_update();

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

                DROP TRIGGER IF EXISTS resources_component_search_vector_trigger ON resources_resourcecomponent;
                CREATE TRIGGER resources_component_search_vector_trigger
                AFTER INSERT OR UPDATE OF name, name_mi OR DELETE
                ON resources_resourcecomponent
                FOR EACH ROW EXECUTE FUNCTION resources_resource_search_vector_refresh();

                -- Drop the tag-rename trigger and its function added in this migration.
                DROP TRIGGER IF EXISTS resources_resourcetag_search_vector_trigger ON resources_resourcetag;
                DROP FUNCTION IF EXISTS resources_resourcetag_search_vector_refresh();

                UPDATE resources_resource SET name = name;
            """,
        ),
    ]
