"""Tests for events feature flag."""

from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtailmenus.models import FlatMenuItem
from wagtailmenus.models import MainMenuItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def _events_disabled(settings):
    settings.EVENTS_ENABLED = False


class TestEventsURLsEnabled:
    """Events URLs should be accessible when EVENTS_ENABLED is True (test default)."""

    def test_events_home_returns_200(self, client):
        response = client.get("/en/events/")
        assert response.status_code == HTTPStatus.OK

    def test_events_upcoming_returns_200(self, client):
        response = client.get("/en/events/upcoming/")
        assert response.status_code == HTTPStatus.OK

    def test_events_past_returns_200(self, client):
        response = client.get("/en/events/past/")
        assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("_events_disabled")
class TestEventsAdminDisabled:
    """Events admin should be hidden when EVENTS_ENABLED is False."""

    def test_event_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:events_event_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_region_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:events_region_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_location_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:events_location_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_series_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:events_series_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestEventsAdminEnabled:
    """Events admin should be accessible when EVENTS_ENABLED is True (test default)."""

    def test_event_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:events_event_changelist"))
        assert response.status_code == HTTPStatus.OK

    def test_region_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:events_region_changelist"))
        assert response.status_code == HTTPStatus.OK

    def test_location_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:events_location_changelist"))
        assert response.status_code == HTTPStatus.OK

    def test_series_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:events_series_changelist"))
        assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("_events_disabled")
class TestMenuItemValidationDisabled:
    """Menu items with /events/ URLs should be rejected when events are disabled."""

    def test_main_menu_item_rejects_events_url(self):
        item = MainMenuItem()
        item.link_url = "/en/events/"
        item.link_text = "Events"
        with pytest.raises(ValidationError, match="Events are currently disabled"):
            item.clean()

    def test_flat_menu_item_rejects_events_url(self):
        item = FlatMenuItem()
        item.link_url = "/en/events/upcoming/"
        item.link_text = "Upcoming"
        with pytest.raises(ValidationError, match="Events are currently disabled"):
            item.clean()

    def test_main_menu_item_allows_non_events_url(self):
        item = MainMenuItem()
        item.link_url = "/about/"
        item.link_text = "About"
        item.clean()  # Should not raise


class TestMenuItemValidationEnabled:
    """Menu items with /events/ URLs should be allowed when events are enabled."""

    def test_main_menu_item_allows_events_url(self):
        item = MainMenuItem()
        item.link_url = "/en/events/"
        item.link_text = "Events"
        item.clean()  # Should not raise

    def test_flat_menu_item_allows_events_url(self):
        item = FlatMenuItem()
        item.link_url = "/en/events/upcoming/"
        item.link_text = "Upcoming"
        item.clean()  # Should not raise
