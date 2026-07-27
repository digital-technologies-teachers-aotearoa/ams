# Creates a 3-membership renewal history (past+paid, current+paid,
# future+awaiting payment) for the marketing screenshot of the Integrated
# Billing capability on features.md.
#
# Run via `manage.py shell`, Django's equivalent of a one-off fixture
# script -- Invoice/Account have no usable admin add form (every field is
# readonly, see ams/billing/admin.py), so the ORM is the only way to create
# them. See docs/screenshots/seed-marketing.sh, which pipes this file in.
# Not idempotent across a real reseed -- invoice_number/
# billing_service_invoice_id are unique, so this assumes it's running
# against the freshly-flushed database seed-marketing.sh always provides,
# not a database that already has these rows.

from datetime import date
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from ams.billing.models import Account
from ams.billing.models import Invoice
from ams.memberships.models import IndividualMembership
from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType


def as_aware_datetime(a_date):
    return timezone.make_aware(timezone.datetime.combine(a_date, timezone.datetime.min.time()))

User = get_user_model()

admin = User.objects.filter(is_superuser=True).order_by("id").first()
account, _ = Account.objects.get_or_create(user=admin)

option, _ = MembershipOption.objects.update_or_create(
    name="Standard membership",
    type=MembershipOptionType.INDIVIDUAL,
    defaults={
        "duration": relativedelta(years=1),
        "cost": 150,
        "invoice_reference": "MTA Membership",
        # Excludes this option from the apply-individual picker (the
        # Membership Management marketing screenshot's own three branded
        # options -- see steps/features-marketing.mjs -- must be the only
        # ones shown there), the same "archive rather than delete" pattern
        # the model itself provides for retiring an option that existing
        # memberships still reference. This one exists purely so
        # IndividualMembership rows below have a membership_option to point
        # to; nobody should ever be offered it to sign up for.
        "archived": True,
    },
)

today = date.today()

# (label, start_date, expiry offset, approved?, paid?)
PERIODS = [
    ("MOCK-HIST-PAST", today - relativedelta(years=2), today - relativedelta(years=1), True, True),
    ("MOCK-HIST-CURRENT", today - relativedelta(months=6), today + relativedelta(months=6), True, True),
    ("MOCK-HIST-FUTURE", today + relativedelta(months=1), today + relativedelta(years=1, months=1), False, False),
]

for invoice_number, start_date, expiry_date, approved, paid in PERIODS:
    membership, _ = IndividualMembership.objects.update_or_create(
        user=admin,
        membership_option=option,
        start_date=start_date,
        defaults={
            "expiry_date": expiry_date,
            "created_datetime": as_aware_datetime(start_date),
            "approved_datetime": as_aware_datetime(start_date) if approved else None,
        },
    )
    Invoice.objects.update_or_create(
        invoice_number=invoice_number,
        defaults={
            "account": account,
            "issue_date": start_date,
            "due_date": start_date + timedelta(days=14),
            "paid_date": start_date + timedelta(days=3) if paid else None,
            "amount": option.cost,
            "paid": option.cost if paid else 0,
            "due": 0 if paid else option.cost,
            "billing_service_invoice_id": invoice_number,
            "individual_membership": membership,
        },
    )

print("Marketing billing fixture data ready: 3-period membership history.")
