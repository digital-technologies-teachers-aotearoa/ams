from http import HTTPStatus

import pytest
from django.urls import reverse

from ams.entities.models import Entity
from ams.resources.admin import ResourceAdmin
from ams.resources.admin import ResourceCategoryAdmin
from ams.resources.admin import ResourceForm
from ams.resources.models import Resource
from ams.resources.tests.factories import ResourceCategoryFactory
from ams.resources.tests.factories import ResourceFactory
from ams.resources.tests.factories import ResourceTagFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _form_data(resource):
    return {
        "name": resource.name,
        "description": resource.description,
        "published": resource.published,
        "visibility": resource.visibility,
    }


class TestResourceForm:
    def test_rejects_when_no_authors(self):
        resource = ResourceFactory()
        data = _form_data(resource)
        data["author_entities"] = []
        data["author_users"] = []
        form = ResourceForm(data=data, instance=resource)
        assert not form.is_valid()
        assert "At least one author" in str(form.errors)

    def test_accepts_with_user_only(self):
        resource = ResourceFactory()
        user = UserFactory()
        data = _form_data(resource)
        data["author_entities"] = []
        data["author_users"] = [user.pk]
        form = ResourceForm(data=data, instance=resource)
        assert form.is_valid(), form.errors

    def test_accepts_with_entity_only(self):
        resource = ResourceFactory()
        entity = Entity.objects.create(name="An Entity")
        data = _form_data(resource)
        data["author_entities"] = [entity.pk]
        data["author_users"] = []
        form = ResourceForm(data=data, instance=resource)
        assert form.is_valid(), form.errors

    def test_accepts_with_both(self):
        resource = ResourceFactory()
        user = UserFactory()
        entity = Entity.objects.create(name="Another Entity")
        data = _form_data(resource)
        data["author_entities"] = [entity.pk]
        data["author_users"] = [user.pk]
        form = ResourceForm(data=data, instance=resource)
        assert form.is_valid(), form.errors


class TestResourceAdminViewCount:
    def test_view_count_is_read_only(self):
        assert "view_count" in ResourceAdmin.readonly_fields

    def test_view_count_in_list_display(self):
        assert "view_count" in ResourceAdmin.list_display

    def test_view_count_rendered_on_change_form(self, admin_client):
        resource = ResourceFactory()
        url = reverse("admin:resources_resource_change", args=[resource.pk])
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert b"view_count" in response.content

    def test_view_count_excluded_from_form_fields(self):
        # editable=False on the model field keeps it out of ResourceForm's
        # fields even though the form declares fields = "__all__" — this is
        # what actually makes it "not directly editable" via the admin form,
        # as distinct from being merely listed in readonly_fields.
        assert "view_count" not in ResourceForm.base_fields

    def test_post_with_different_view_count_is_ignored(self, admin_client):
        resource = ResourceFactory()
        user = UserFactory()
        resource.author_users.add(user)
        original_view_count = 5
        Resource.objects.filter(pk=resource.pk).update(
            view_count=original_view_count,
        )
        url = reverse("admin:resources_resource_change", args=[resource.pk])
        data = {
            "name_en": resource.name,
            "name_mi": "",
            "description_en": resource.description,
            "description_mi": "",
            "published": "on" if resource.published else "",
            "visibility": resource.visibility,
            "author_entities": [],
            "author_users": [user.pk],
            "tags": [],
            # Not a real form field (view_count isn't rendered at all), but
            # submitted anyway to prove the admin can't be tricked into
            # accepting it via a hand-crafted POST.
            "view_count": 999,
            "components-TOTAL_FORMS": "1",
            "components-INITIAL_FORMS": "0",
            "components-MIN_NUM_FORMS": "0",
            "components-MAX_NUM_FORMS": "1000",
            "components-0-name_en": "",
            "components-0-name_mi": "",
            "components-0-component_url": "",
            "components-0-id": "",
            "components-0-resource": resource.pk,
            "_save": "Save",
        }
        response = admin_client.post(url, data)
        assert response.status_code == HTTPStatus.FOUND
        resource.refresh_from_db()
        assert resource.view_count == original_view_count


class TestResourceAdminThumbnail:
    def test_thumbnail_in_fieldsets(self):
        fieldset_fields = {
            field
            for _, options in ResourceAdmin.fieldsets
            for field in options["fields"]
        }
        assert "thumbnail" in fieldset_fields

    def test_thumbnail_rendered_on_change_form(self, admin_client):
        resource = ResourceFactory()
        url = reverse("admin:resources_resource_change", args=[resource.pk])
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert b"thumbnail" in response.content


class TestResourceCategoryAdmin:
    def test_category_admin_accessible(self, admin_client):
        ResourceCategoryFactory(name="Test Category")
        url = reverse("admin:resources_resourcecategory_changelist")
        response = admin_client.get(url)
        expected_response_code = 200
        assert response.status_code == expected_response_code

    def test_tag_inline_renders_in_category_admin(self, admin_client):
        category = ResourceCategoryFactory(name="Year Level")
        ResourceTagFactory(name="Level 1", category=category)
        url = reverse("admin:resources_resourcecategory_change", args=[category.pk])
        response = admin_client.get(url)
        expected_response_code = 200
        assert response.status_code == expected_response_code
        assert b"Level 1" in response.content

    def test_gradient_colours_and_tag_style_in_fieldsets(self):
        fieldset_fields = {
            field
            for _, options in ResourceCategoryAdmin.fieldsets
            for field in options["fields"]
        }
        assert "gradient_start_colour" in fieldset_fields
        assert "gradient_end_colour" in fieldset_fields
        assert "tag_style" in fieldset_fields

    def test_gradient_colours_and_tag_style_rendered_on_change_form(
        self,
        admin_client,
    ):
        category = ResourceCategoryFactory(name="Year Level")
        url = reverse("admin:resources_resourcecategory_change", args=[category.pk])
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert b"gradient_start_colour" in response.content
        assert b"gradient_end_colour" in response.content
        assert b"tag_style" in response.content
