from io import StringIO

import pytest
from django.core.management import call_command

from ams.resources.models import Resource

pytestmark = pytest.mark.django_db


class TestCreateSampleResourcesCommandThumbnails:
    def test_adds_thumbnails_to_most_but_not_all_resources(self, file_storage):
        call_command("create_sample_resources", stdout=StringIO())
        total = Resource.objects.count()
        with_thumbnail = Resource.objects.exclude(thumbnail="").count()
        without_thumbnail = total - with_thumbnail

        assert with_thumbnail > 0
        assert without_thumbnail > 0
        # Roughly 75% coverage — not an exact assertion, since the skip
        # pattern is deterministic by position, not a literal percentage.
        assert with_thumbnail / total > 0.5  # noqa: PLR2004

    def test_second_run_does_not_change_existing_thumbnails(self, file_storage):
        call_command("create_sample_resources", stdout=StringIO())
        first_run_thumbnails = dict(
            Resource.objects.exclude(thumbnail="").values_list("name", "thumbnail"),
        )

        call_command("create_sample_resources", stdout=StringIO())
        second_run_thumbnails = dict(
            Resource.objects.exclude(thumbnail="").values_list("name", "thumbnail"),
        )

        assert second_run_thumbnails == first_run_thumbnails
