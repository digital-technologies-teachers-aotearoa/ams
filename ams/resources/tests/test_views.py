from http import HTTPStatus
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ams.resources.tests.factories import ResourceComponentFactory
from ams.resources.tests.factories import ResourceFactory

pytestmark = pytest.mark.django_db


class TestResourceHomeView:
    def test_get(self, client):
        response = client.get("/en/resources/")
        assert response.status_code == HTTPStatus.OK

    def test_shows_only_published(self, client):
        published = ResourceFactory(published=True)
        unpublished = ResourceFactory(published=False)
        response = client.get("/en/resources/")
        resources = list(response.context["resources"])
        assert published in resources
        assert unpublished not in resources

    def test_resource_count_in_context(self, client):
        ResourceFactory.create_batch(3, published=True)
        ResourceFactory(published=False)
        response = client.get("/en/resources/")
        expected_component_count = 3
        assert response.context["resource_count"] == expected_component_count

    def test_component_count_in_context(self, client):
        resource = ResourceFactory(published=True)
        ResourceComponentFactory(
            resource=resource,
            component_url="https://a.example.com/",
        )
        ResourceComponentFactory(
            resource=resource,
            component_url="https://b.example.com/",
        )
        # Component on unpublished resource should not be counted
        unpublished = ResourceFactory(published=False)
        ResourceComponentFactory(
            resource=unpublished,
            component_url="https://c.example.com/",
        )
        response = client.get("/en/resources/")
        expected_component_count = 2
        assert response.context["component_count"] == expected_component_count

    def test_caps_at_10_resources(self, client):
        ResourceFactory.create_batch(15, published=True)
        response = client.get("/en/resources/")
        expected_component_count = 10
        assert len(response.context["resources"]) == expected_component_count


class TestResourceDetailView:
    def test_get_with_slug(self, client):
        resource = ResourceFactory(published=True)
        response = client.get(resource.get_absolute_url())
        assert response.status_code == HTTPStatus.OK

    def test_redirect_without_slug(self, client):
        resource = ResourceFactory(published=True)
        response = client.get(f"/en/resources/resource/{resource.pk}/")
        assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
        assert resource.get_absolute_url() in response.url

    def test_unpublished_returns_404(self, client):
        resource = ResourceFactory(published=False)
        response = client.get(resource.get_absolute_url(), follow=True)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_components_of_in_context(self, client):
        parent = ResourceFactory(published=True)
        child = ResourceFactory(published=True)
        ResourceComponentFactory(resource=parent, component_resource=child)
        response = client.get(child.get_absolute_url())
        components_of = list(response.context["components_of"])
        assert len(components_of) == 1
        assert components_of[0].resource == parent

    def test_components_of_excludes_unpublished_parent(self, client):
        unpublished_parent = ResourceFactory(published=False)
        child = ResourceFactory(published=True)
        ResourceComponentFactory(resource=unpublished_parent, component_resource=child)
        response = client.get(child.get_absolute_url())
        assert list(response.context["components_of"]) == []


class TestResourceComponentDownloadView:
    def test_nonexistent_component_returns_404(self, client):
        response = client.get("/en/resources/component/99999/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_unpublished_resource_returns_404(self, client):
        resource = ResourceFactory(published=False)
        component = ResourceComponentFactory(
            resource=resource,
            component_url="https://example.com/",
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_url_component_returns_404(self, client):
        resource = ResourceFactory(published=True)
        component = ResourceComponentFactory(
            resource=resource,
            component_url="https://example.com/",
        )
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_post_returns_405(self, client):
        response = client.post("/en/resources/component/1/download/")
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_recursive_component_returns_404(self, client):
        parent = ResourceFactory(published=True)
        child = ResourceFactory(published=True)
        component = ResourceComponentFactory(resource=parent, component_resource=child)
        response = client.get(f"/en/resources/component/{component.pk}/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_file_component_redirects_to_presigned_url(self, client):
        resource = ResourceFactory(published=True)
        component = ResourceComponentFactory(resource=resource, component_url="")
        presigned_url = "https://s3.example.com/resources/1/file.pdf?Signature=abc"

        mock_component = MagicMock()
        mock_component.resource.published = True
        mock_component.component_file.__bool__ = MagicMock(return_value=True)
        mock_component.component_file.url = presigned_url

        with patch("ams.resources.views.ResourceComponent.objects") as mock_manager:
            mock_manager.select_related.return_value.filter.return_value.first.return_value = mock_component  # noqa: E501
            response = client.get(f"/en/resources/component/{component.pk}/download/")

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == presigned_url
