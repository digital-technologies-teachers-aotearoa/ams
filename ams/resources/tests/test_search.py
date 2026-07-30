import pytest

from ams.entities.tests.factories import EntityFactory
from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag
from ams.resources.tests.factories import ResourceCategoryFactory

pytestmark = pytest.mark.django_db


def _search(client, q, lang="en"):
    response = client.get(f"/{lang}/resources/search/", {"q": q})
    return list(response.context["results"])


class TestSearchUsesTranslatedColumns:
    def test_finds_by_english_name(self, client):
        resource = Resource.objects.create(
            name_en="Firefighting manual",
            description_en="hydrant guide",
            published=True,
        )
        assert resource in _search(client, "firefighting")

    def test_maori_name_found_in_maori_search_but_not_english(self, client):
        # "he" is an English stopword (dropped by the english config) but a common
        # Maori word. It must match in Maori search (simple config, _mi vector) and
        # must NOT match in English search now that the languages are isolated.
        resource = Resource.objects.create(
            name_en="Placeholder",
            name_mi="He pukapuka whakangungu",
            published=True,
        )
        assert resource in _search(client, "he", lang="mi")
        assert resource not in _search(client, "he", lang="en")

    def test_english_only_content_not_found_in_maori_search_by_maori_word(self, client):
        # A word unique to name_mi is found in Maori mode but not in English mode.
        resource = Resource.objects.create(
            name_en="Firefighting manual",
            name_mi="Puna kohatu whakamataku",
            published=True,
        )
        assert resource in _search(client, "puna", lang="mi")
        assert resource not in _search(client, "puna", lang="en")

    def test_english_only_resource_found_in_maori_search_via_fallback(self, client):
        # A resource with no Maori translation still displays its English title in
        # Maori mode (modeltranslation fallback), so it must remain findable in
        # Maori search by that English text.
        resource = Resource.objects.create(
            name_en="Firefighting manual",
            published=True,
        )
        assert resource in _search(client, "firefighting", lang="mi")

    def test_author_name_found_in_both_languages(self, client):
        entity = EntityFactory(name="Zzentity")
        resource = Resource.objects.create(name_en="Tagged resource", published=True)
        resource.author_entities.add(entity)

        assert resource in _search(client, "zzentity", lang="en")
        assert resource in _search(client, "zzentity", lang="mi")

    def test_finds_when_base_column_is_blank(self, client):
        # The production regression: authoritative content lives in name_en and
        # the base column is blank. The old vector read the base column and found
        # nothing.
        resource = Resource.objects.create(name_en="Regression row", published=True)
        Resource.objects.rewrite(False).filter(pk=resource.pk).update(name="")  # noqa: FBT003
        assert resource in _search(client, "regression")

    def test_base_column_content_is_not_indexed(self, client):
        # Writing straight to the base column (bypassing modeltranslation) must not
        # make a row searchable — proves the base column is no longer indexed.
        resource = Resource.objects.create(name_en="Real name", published=True)
        Resource.objects.rewrite(False).filter(pk=resource.pk).update(  # noqa: FBT003
            name="Zzunsearchable",
        )
        assert resource not in _search(client, "zzunsearchable")

    def test_tag_name_indexed_and_rename_refreshes(self, client):
        category = ResourceCategoryFactory()
        tag = ResourceTag.objects.create(category=category, name_en="Aardvark")
        resource = Resource.objects.create(name_en="Tagged resource", published=True)
        resource.tags.add(tag)

        assert resource in _search(client, "aardvark")

        tag.name_en = "Zebra"
        tag.save()

        assert resource not in _search(client, "aardvark")
        assert resource in _search(client, "zebra")

    def test_tag_abbreviation_indexed(self, client):
        # Abbreviations render in the tag badge but were previously never indexed.
        category = ResourceCategoryFactory()
        tag = ResourceTag.objects.create(
            category=category,
            name_en="Continuing professional development",
            abbreviation_en="Zcpd",
        )
        resource = Resource.objects.create(name_en="Tagged resource", published=True)
        resource.tags.add(tag)
        assert resource in _search(client, "zcpd")

    def test_component_name_refreshes_parent_vector(self, client):
        resource = Resource.objects.create(name_en="Unrelated title", published=True)
        ResourceComponent.objects.create(
            resource=resource,
            name_en="Kubernetes deployment guide",
            component_url="https://example.com/",
        )
        assert resource in _search(client, "kubernetes")

    def test_language_tag_with_macron_is_indexed(self, client):
        # Proves the premise behind treating languages as a plain tag category
        # (setup_resource_languages) rather than a dedicated model: tag names
        # are already weighted C in the existing search trigger, so a macron-
        # bearing tag name needs no trigger change to be searchable.
        category = ResourceCategoryFactory(name_en="Language")
        tag = ResourceTag.objects.create(category=category, name_en="Te Reo Māori")
        resource = Resource.objects.create(name_en="Karakia guide", published=True)
        resource.tags.add(tag)
        assert resource in _search(client, "te reo")
