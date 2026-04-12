import pytest

from ams.entities.models import Entity
from ams.resources.admin import ResourceForm
from ams.resources.tests.factories import ResourceFactory
from ams.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _form_data(resource):
    return {
        "name": resource.name,
        "description": resource.description,
        "published": resource.published,
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
