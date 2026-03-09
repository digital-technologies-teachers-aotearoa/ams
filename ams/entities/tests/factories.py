import factory

from ams.entities.models import Entity


class EntityFactory(factory.django.DjangoModelFactory[Entity]):
    name = factory.Faker("company")
    url = factory.Faker("url")

    class Meta:
        model = Entity
