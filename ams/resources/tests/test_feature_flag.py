"""Tests for resources feature flag."""

from http import HTTPStatus

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from wagtailmenus.models import FlatMenuItem
from wagtailmenus.models import MainMenuItem

from ams.resources.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def _resources_disabled(settings):
    settings.RESOURCES_ENABLED = False


@pytest.fixture
def _resources_enabled(settings):
    settings.RESOURCES_ENABLED = True


class TestResourcesURLsEnabled:
    """Resources URLs should be accessible when RESOURCES_ENABLED is True

    Test suite defaults to True.
    """

    def test_resources_home_returns_200(self, client):
        response = client.get("/en/resources/")
        assert response.status_code == HTTPStatus.OK

    def test_resource_detail_returns_200(self, client):
        resource = ResourceFactory(published=True)
        response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("_resources_disabled")
class TestResourcesAdminDisabled:
    """Resources admin should be hidden when RESOURCES_ENABLED is False."""

    def test_resource_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:resources_resource_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_resources_enabled")
class TestResourcesAdminEnabled:
    """Resources admin should be accessible when RESOURCES_ENABLED is True."""

    def test_resource_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:resources_resource_changelist"))
        assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("_resources_disabled")
class TestMenuItemValidationDisabled:
    """Menu items with /resources/ should be rejected when resources are disabled."""

    def test_main_menu_item_rejects_resources_url(self):
        item = MainMenuItem()
        item.link_url = "/en/resources/"
        item.link_text = "Resources"
        with pytest.raises(ValidationError, match="Resources are currently disabled"):
            item.clean()

    def test_flat_menu_item_rejects_resources_url(self):
        item = FlatMenuItem()
        item.link_url = "/en/resources/resource/1/my-resource/"
        item.link_text = "My Resource"
        with pytest.raises(ValidationError, match="Resources are currently disabled"):
            item.clean()

    def test_main_menu_item_allows_non_resources_url(self):
        item = MainMenuItem()
        item.link_url = "/about/"
        item.link_text = "About"
        item.clean()  # Should not raise


class TestMenuItemValidationEnabled:
    """Menu items with /resources/ URLs should be allowed when resources are enabled."""

    def test_main_menu_item_allows_resources_url(self):
        item = MainMenuItem()
        item.link_url = "/en/resources/"
        item.link_text = "Resources"
        item.clean()  # Should not raise

    def test_flat_menu_item_allows_resources_url(self):
        item = FlatMenuItem()
        item.link_url = "/en/resources/resource/1/my-resource/"
        item.link_text = "My Resource"
        item.clean()  # Should not raise
