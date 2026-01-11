"""Factory Boy factories for terms app tests."""

from datetime import timedelta

from django.utils import timezone
from factory import Faker
from factory import LazyFunction
from factory import SubFactory
from factory.django import DjangoModelFactory

from ams.terms.models import Term
from ams.terms.models import TermAcceptance
from ams.terms.models import TermVersion
from ams.users.tests.factories import UserFactory


class TermFactory(DjangoModelFactory):
    """Factory for creating Term instances."""

    key = Faker("slug")
    name = Faker("sentence", nb_words=3)
    description = Faker("text")

    class Meta:
        model = Term


class TermVersionFactory(DjangoModelFactory):
    """Factory for creating TermVersion instances."""

    term = SubFactory(TermFactory)
    version = Faker("numerify", text="#.#")
    content = Faker("text", max_nb_chars=500)
    change_log = Faker("text", max_nb_chars=200)
    is_active = True
    date_active = LazyFunction(lambda: timezone.now() - timedelta(days=1))

    class Meta:
        model = TermVersion


class TermAcceptanceFactory(DjangoModelFactory):
    """Factory for creating TermAcceptance instances."""

    user = SubFactory(UserFactory)
    term_version = SubFactory(TermVersionFactory)
    ip_address = Faker("ipv4")
    user_agent = Faker("user_agent")
    source = "web"

    class Meta:
        model = TermAcceptance
