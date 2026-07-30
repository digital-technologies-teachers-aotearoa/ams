from io import StringIO

import pytest
from django.core.management import call_command

from ams.resources.models import ResourceCategory

pytestmark = pytest.mark.django_db


class TestSetupResourceLanguagesCommand:
    def test_creates_language_category(self):
        call_command("setup_resource_languages", stdout=StringIO())
        assert ResourceCategory.objects.filter(slug="language").exists()

    def test_creates_three_seed_tags(self):
        call_command("setup_resource_languages", stdout=StringIO())
        category = ResourceCategory.objects.get(slug="language")
        expected_tag_count = 2
        assert category.tags.count() == expected_tag_count
        abbreviations = set(category.tags.values_list("abbreviation", flat=True))
        assert abbreviations == {"EN", "MI"}

    def test_second_run_is_a_no_op(self):
        call_command("setup_resource_languages", stdout=StringIO())
        category = ResourceCategory.objects.get(slug="language")
        category.name = "Renamed Language Category"
        category.save()
        renamed_tag = category.tags.first()
        renamed_tag.name = "Custom Language"
        renamed_tag.save()

        call_command("setup_resource_languages", stdout=StringIO())

        category.refresh_from_db()
        renamed_tag.refresh_from_db()
        assert category.name == "Renamed Language Category"
        assert renamed_tag.name == "Custom Language"

    def test_deleted_tag_is_not_recreated_on_second_run(self):
        call_command("setup_resource_languages", stdout=StringIO())
        category = ResourceCategory.objects.get(slug="language")
        category.tags.first().delete()
        remaining_after_delete = category.tags.count()

        call_command("setup_resource_languages", stdout=StringIO())

        assert category.tags.count() == remaining_after_delete

    def test_noop_when_resources_disabled(self, settings):
        settings.RESOURCES_ENABLED = False
        call_command("setup_resource_languages", stdout=StringIO())
        assert not ResourceCategory.objects.filter(slug="language").exists()

    def test_idempotent_call_count_matches_categories(self):
        call_command("setup_resource_languages", stdout=StringIO())
        call_command("setup_resource_languages", stdout=StringIO())
        assert ResourceCategory.objects.filter(slug="language").count() == 1
