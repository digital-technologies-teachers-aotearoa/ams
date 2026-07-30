from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from ams.resources.models import ResourceComponentView
from ams.resources.models import ResourceView
from ams.resources.tests.factories import ResourceComponentFactory
from ams.resources.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


def _view(resource, *, days_ago):
    view = ResourceView.objects.create(resource=resource)
    ResourceView.objects.filter(pk=view.pk).update(
        datetime_viewed=timezone.now() - timedelta(days=days_ago),
    )
    return view


def _component_view(component, *, days_ago):
    view = ResourceComponentView.objects.create(component=component)
    ResourceComponentView.objects.filter(pk=view.pk).update(
        datetime_viewed=timezone.now() - timedelta(days=days_ago),
    )
    return view


class TestPruneResourceViewsCommand:
    def test_deletes_resource_views_older_than_default_retention(self):
        resource = ResourceFactory()
        old = _view(resource, days_ago=401)
        recent = _view(resource, days_ago=1)
        call_command("prune_resource_views", stdout=StringIO())
        remaining = set(ResourceView.objects.values_list("pk", flat=True))
        assert old.pk not in remaining
        assert recent.pk in remaining

    def test_deletes_component_views_older_than_default_retention(self):
        component = ResourceComponentFactory()
        old = _component_view(component, days_ago=401)
        recent = _component_view(component, days_ago=1)
        call_command("prune_resource_views", stdout=StringIO())
        remaining = set(ResourceComponentView.objects.values_list("pk", flat=True))
        assert old.pk not in remaining
        assert recent.pk in remaining

    def test_days_argument_overrides_default(self):
        resource = ResourceFactory()
        view = _view(resource, days_ago=10)
        call_command("prune_resource_views", days=5, stdout=StringIO())
        assert not ResourceView.objects.filter(pk=view.pk).exists()

    def test_view_count_unaffected_by_pruning(self):
        resource = ResourceFactory()
        _view(resource, days_ago=401)
        expected_view_count = 3
        type(resource).objects.filter(pk=resource.pk).update(
            view_count=expected_view_count,
        )
        call_command("prune_resource_views", stdout=StringIO())
        resource.refresh_from_db()
        assert resource.view_count == expected_view_count
