from http import HTTPStatus

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def _resources_disabled(settings):
    settings.RESOURCES_ENABLED = False


@pytest.fixture
def _resources_enabled(settings):
    settings.RESOURCES_ENABLED = True


@pytest.mark.usefixtures("_resources_disabled")
class TestResourcesAdminDisabled:
    def test_resource_changelist_forbidden(self, admin_client):
        response = admin_client.get(reverse("admin:resources_resource_changelist"))
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.usefixtures("_resources_enabled")
class TestResourcesAdminEnabled:
    def test_resource_changelist_accessible(self, admin_client):
        response = admin_client.get(reverse("admin:resources_resource_changelist"))
        assert response.status_code == HTTPStatus.OK
