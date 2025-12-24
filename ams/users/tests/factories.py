from collections.abc import Sequence
from typing import Any

from django.utils import timezone
from factory import Faker
from factory import LazyFunction
from factory import SubFactory
from factory import Trait
from factory import post_generation
from factory.django import DjangoModelFactory

from ams.users.models import Organisation
from ams.users.models import OrganisationMember
from ams.users.models import User


class UserFactory(DjangoModelFactory[User]):
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    username = Faker("user_name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Save again the instance if creating and at least one hook ran."""
        if create and results and not cls._meta.skip_postgeneration_save:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        model = User
        django_get_or_create = ["email"]


class OrganisationFactory(DjangoModelFactory[Organisation]):
    name = Faker("company")
    telephone = Faker("phone_number")
    email = Faker("company_email")
    contact_name = Faker("name")
    postal_address = Faker("street_address")
    postal_suburb = Faker("city_suffix")
    postal_city = Faker("city")
    postal_code = Faker("postcode")
    street_address = Faker("street_address")
    suburb = Faker("city_suffix")
    city = Faker("city")

    class Meta:
        model = Organisation


class OrganisationMemberFactory(DjangoModelFactory[OrganisationMember]):
    user = SubFactory(UserFactory)
    organisation = SubFactory(OrganisationFactory)
    invite_email = Faker("email")
    created_datetime = LazyFunction(timezone.now)
    accepted_datetime = None
    role = OrganisationMember.Role.MEMBER

    class Params:
        invite = Trait(user=None)
        accepted = Trait(accepted_datetime=LazyFunction(timezone.now))
        admin = Trait(role=OrganisationMember.Role.ADMIN)

    class Meta:
        model = OrganisationMember
