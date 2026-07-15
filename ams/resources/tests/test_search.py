import pytest

from ams.resources.models import Resource
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag
from ams.resources.tests.factories import ResourceCategoryFactory

pytestmark = pytest.mark.django_db


def _search(client, q):
    response = client.get("/en/resources/search/", {"q": q})
    return list(response.context["results"])


class TestSearchUsesTranslatedColumns:
    def test_finds_by_english_name(self, client):
        resource = Resource.objects.create(
            name_en="Firefighting manual",
            description_en="hydrant guide",
            published=True,
        )
        assert resource in _search(client, "firefighting")

    def test_finds_by_maori_name_that_is_an_english_stopword(self, client):
        # "he" is an English stopword (dropped by the english config) but a common
        # Maori word. The simple-config query branch must still match it.
        resource = Resource.objects.create(
            name_en="Placeholder",
            name_mi="He pukapuka whakangungu",
            published=True,
        )
        assert resource in _search(client, "he")

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
