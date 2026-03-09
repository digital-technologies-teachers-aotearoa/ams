import pytest

from ams.entities.models import Entity
from ams.entities.tests.factories import EntityFactory


@pytest.mark.django_db
class TestEntity:
    def test_str(self):
        entity = EntityFactory(name="DTTA")
        assert str(entity) == "DTTA"

    def test_ordering(self):
        e1 = EntityFactory(name="Zebra Corp")
        e2 = EntityFactory(name="Alpha Inc")

        entities = list(Entity.objects.all())
        assert entities == [e2, e1]
