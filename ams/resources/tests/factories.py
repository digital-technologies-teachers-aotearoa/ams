import factory

from ams.resources.models import Resource
from ams.resources.models import ResourceComponent


class ResourceFactory(factory.django.DjangoModelFactory[Resource]):
    name = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    published = True

    class Meta:
        model = Resource


class ResourceComponentFactory(factory.django.DjangoModelFactory[ResourceComponent]):
    name = factory.Faker("sentence", nb_words=3)
    resource = factory.SubFactory(ResourceFactory)
    component_url = "https://example.com/"

    class Meta:
        model = ResourceComponent
