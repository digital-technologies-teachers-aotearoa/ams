from dateutil.relativedelta import relativedelta
from django.utils import timezone
from factory import Faker
from factory import LazyFunction
from factory import SubFactory
from factory import Trait
from factory.django import DjangoModelFactory

from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.models import OrganisationMembership
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import UserFactory


class MembershipOptionFactory(DjangoModelFactory[MembershipOption]):
    name = Faker("word")
    type = Faker(
        "random_element",
        elements=[t.value for t in MembershipOptionType],
    )
    # Provide a dict that we convert to a relativedelta in _create.
    duration = Faker(
        "random_element",
        elements=[
            {"years": 1},
            {"months": 6},
            {"months": 3},
            {"days": 30},
            {"days": 14},
            {"days": 7},
        ],
    )
    cost = Faker("pydecimal", left_digits=3, right_digits=2, positive=True)

    class Meta:
        model = MembershipOption
        django_get_or_create = ["name", "type"]

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Convert stored duration dict into a relativedelta instance."""
        duration_dict = kwargs.pop("duration", {"months": 12})
        kwargs["duration"] = relativedelta(**duration_dict)
        return super()._create(model_class, *args, **kwargs)


class IndividualMembershipFactory(DjangoModelFactory[IndividualMembership]):
    user = SubFactory(UserFactory)
    membership_option = SubFactory(
        MembershipOptionFactory,
        type=MembershipOptionType.INDIVIDUAL,
    )
    invoice = None
    start_date = LazyFunction(timezone.localdate)
    created_datetime = LazyFunction(timezone.now)
    approved_datetime = None
    cancelled_datetime = None

    class Params:
        approved = Trait(approved_datetime=LazyFunction(timezone.now))
        cancelled = Trait(cancelled_datetime=LazyFunction(timezone.now))
        pending = Trait(approved_datetime=None)
        active = Trait(approved_datetime=LazyFunction(timezone.now))

    class Meta:
        model = IndividualMembership


class OrganisationMembershipFactory(DjangoModelFactory[OrganisationMembership]):
    organisation = SubFactory(OrganisationFactory)
    membership_option = SubFactory(
        MembershipOptionFactory,
        type=MembershipOptionType.ORGANISATION,
    )
    invoice = None
    start_date = LazyFunction(timezone.localdate)
    created_datetime = LazyFunction(timezone.now)
    cancelled_datetime = None

    class Params:
        cancelled = Trait(cancelled_datetime=LazyFunction(timezone.now))
        active = Trait()  # implicit active unless expired or cancelled

    class Meta:
        model = OrganisationMembership
