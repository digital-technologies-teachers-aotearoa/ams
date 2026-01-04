from dateutil.relativedelta import relativedelta
from django.utils import timezone
from factory import Faker
from factory import LazyAttribute
from factory import LazyFunction
from factory import SubFactory
from factory import Trait
from factory.django import DjangoModelFactory

from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.models import OrganisationMembership
from ams.organisations.tests.factories import OrganisationFactory
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
    max_seats = None
    archived = False

    class Meta:
        model = MembershipOption
        django_get_or_create = ["name", "type"]

    class Params:
        individual = Trait(type=MembershipOptionType.INDIVIDUAL)
        organisation = Trait(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

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
    expiry_date = LazyAttribute(lambda o: o.start_date + o.membership_option.duration)

    class Params:
        approved = Trait(approved_datetime=LazyFunction(timezone.now))
        cancelled = Trait(cancelled_datetime=LazyFunction(timezone.now))
        pending = Trait(approved_datetime=None)
        active = Trait(approved_datetime=LazyFunction(timezone.now))
        # Start date sufficiently in the past so that expiry_date < today
        expired = Trait(
            start_date=LazyFunction(
                lambda: timezone.localdate() - timezone.timedelta(days=500),
            ),
        )
        # Start date in future => status should be pending
        future = Trait(
            start_date=LazyFunction(
                lambda: timezone.localdate() + timezone.timedelta(days=30),
            ),
        )

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
    approved_datetime = None
    cancelled_datetime = None
    expiry_date = LazyAttribute(lambda o: o.start_date + o.membership_option.duration)
    seats = 1

    class Params:
        approved = Trait(approved_datetime=LazyFunction(timezone.now))
        cancelled = Trait(cancelled_datetime=LazyFunction(timezone.now))
        pending = Trait(approved_datetime=None)
        active = Trait(approved_datetime=LazyFunction(timezone.now))
        expired = Trait(
            start_date=LazyFunction(
                lambda: timezone.localdate() - timezone.timedelta(days=500),
            ),
        )
        future = Trait(
            start_date=LazyFunction(
                lambda: timezone.localdate() + timezone.timedelta(days=30),
            ),
        )

    class Meta:
        model = OrganisationMembership
