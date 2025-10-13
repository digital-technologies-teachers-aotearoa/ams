from collections.abc import Sequence
from typing import Any

from factory import Faker
from factory import SubFactory
from factory import Trait
from factory import post_generation
from factory.django import DjangoModelFactory

from ams.users.models import Organisation
from ams.users.models import OrganisationMember
from ams.users.models import OrganisationType
from ams.users.models import User


class UserFactory(DjangoModelFactory[User]):
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")

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


class OrganisationTypeFactory(DjangoModelFactory[OrganisationType]):
    # Faker doesn't expose 'unique.word' as a single provider string; emulate uniqueness
    name = Faker("word")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Ensure uniqueness by appending a sequence number if collision occurs
        base_name = kwargs.get("name") or Faker("word").evaluate(
            None,
            None,
            extra={"locale": None},
        )
        candidate = base_name
        counter = 1
        while OrganisationType.objects.filter(name=candidate).exists():
            candidate = f"{base_name}-{counter}"
            counter += 1
        kwargs["name"] = candidate
        return super()._create(model_class, *args, **kwargs)

    class Meta:
        model = OrganisationType
        django_get_or_create = ["name"]


class OrganisationFactory(DjangoModelFactory[Organisation]):
    name = Faker("company")
    type = SubFactory(OrganisationTypeFactory)
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
    created_datetime = Faker("date_time_this_year")
    accepted_datetime = None
    is_admin = False

    class Params:
        invite = Trait(user=None)
        accepted = Trait(accepted_datetime=Faker("date_time_this_year"))
        admin = Trait(is_admin=True)

    class Meta:
        model = OrganisationMember
