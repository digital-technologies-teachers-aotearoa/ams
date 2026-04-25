import factory

from ams.resources.models import Resource
from ams.resources.models import ResourceCategory
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag


class ResourceCategoryFactory(factory.django.DjangoModelFactory[ResourceCategory]):
    name = factory.Faker("word")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = ResourceCategory


class ResourceTagFactory(factory.django.DjangoModelFactory[ResourceTag]):
    category = factory.SubFactory(ResourceCategoryFactory)
    name = factory.Faker("word")
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = ResourceTag


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

    class Params:
        with_file = factory.Trait(
            component_url="",
            component_file=factory.django.FileField(
                filename="test.pdf",
                data=b"content",
            ),
        )

    class Meta:
        model = ResourceComponent
