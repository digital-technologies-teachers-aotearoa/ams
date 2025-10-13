from decimal import Decimal

from django.utils import timezone
from factory import Faker
from factory import LazyFunction
from factory import SubFactory
from factory import Trait
from factory.django import DjangoModelFactory

from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import UserFactory


class AccountFactory(DjangoModelFactory[Account]):
    organisation = None
    user = None

    class Params:
        user_account = Trait(user=SubFactory(UserFactory))
        organisation_account = Trait(organisation=SubFactory(OrganisationFactory))

    class Meta:
        model = Account

    # No special _create needed; Traits handle assignment.


class InvoiceFactory(DjangoModelFactory[Invoice]):
    account = SubFactory(AccountFactory, user_account=True)
    invoice_number = Faker("bothify", text="INV-####")
    issue_date = LazyFunction(timezone.localdate)
    # due date one month from issue
    due_date = LazyFunction(lambda: timezone.localdate() + timezone.timedelta(days=30))
    paid_date = None
    amount = Decimal("100.00")
    paid = Decimal("0.00")
    due = Decimal("100.00")
    billing_service_invoice_id = Faker("uuid4")
    update_needed = False

    class Params:
        unpaid = Trait(paid=Decimal("0.00"), due=Decimal("100.00"), paid_date=None)
        full_payment = Trait(
            paid_date=LazyFunction(timezone.localdate),
            paid=Decimal("100.00"),
            due=Decimal("0.00"),
        )
        half_payment = Trait(
            paid=Decimal("50.00"),
            due=Decimal("50.00"),
        )

    class Meta:
        model = Invoice

    # Traits handle payment states; no custom _create required.
