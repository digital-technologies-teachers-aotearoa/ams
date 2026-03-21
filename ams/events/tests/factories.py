from decimal import Decimal

import factory
from django.utils import timezone

from ams.events.models import Event
from ams.events.models import Location
from ams.events.models import Region
from ams.events.models import Series
from ams.events.models import Session


class RegionFactory(factory.django.DjangoModelFactory[Region]):
    name = factory.Faker("city")

    class Meta:
        model = Region


class LocationFactory(factory.django.DjangoModelFactory[Location]):
    name = factory.Faker("company")
    street_address = factory.Faker("street_address")
    city = factory.Faker("city")
    region = factory.SubFactory(RegionFactory)
    latitude = factory.LazyFunction(lambda: Decimal("-41.286460"))
    longitude = factory.LazyFunction(lambda: Decimal("174.776236"))

    class Meta:
        model = Location


class SeriesFactory(factory.django.DjangoModelFactory[Series]):
    name = factory.Faker("catch_phrase")
    abbreviation = factory.LazyAttribute(lambda o: o.name[:5].upper())
    description = factory.Faker("paragraph")

    class Meta:
        model = Series


class EventFactory(factory.django.DjangoModelFactory[Event]):
    name = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    published = True
    registration_type = Event.RegistrationType.REGISTER
    registration_link = factory.Faker("url")
    start = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    end = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=2))

    class Meta:
        model = Event
        skip_postgeneration_save = True

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for location in extracted:
                self.locations.add(location)

    @factory.post_generation
    def organisers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for organiser in extracted:
                self.organisers.add(organiser)


class SessionFactory(factory.django.DjangoModelFactory[Session]):
    name = factory.Faker("sentence", nb_words=3)
    event = factory.SubFactory(EventFactory)
    start = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=1))
    end = factory.LazyFunction(
        lambda: timezone.now() + timezone.timedelta(days=1, hours=2),
    )

    class Meta:
        model = Session
