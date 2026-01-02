from django.utils import timezone
from factory import Faker
from factory import LazyFunction
from factory import SubFactory
from factory import Trait
from factory.django import DjangoModelFactory

from ams.organisations.models import Organisation
from ams.organisations.models import OrganisationMember
from ams.users.tests.factories import UserFactory


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
