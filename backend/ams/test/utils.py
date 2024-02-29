import re
from datetime import timedelta
from typing import Any, List, Optional, Tuple

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.utils import timezone

from ams.billing.models import Account, Invoice
from ams.users.models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
    OrganisationMembership,
    OrganisationType,
    UserMembership,
)


def parse_response_table_rows(response: HttpResponse, table_index: Optional[int] = None) -> List[List[Any]]:
    if table_index is not None:
        table = response.context["tables"][table_index]
    else:
        table = response.context["table"]

    rows = []
    for row in table.rows:
        row_cells = [cell for cell in row.cells]

        # Parse the link titles in the action cell
        if table.columns[len(table.columns) - 1].name == "actions":
            action_cell = row_cells.pop()
            action_titles = re.findall(r'<(?:button|a)[^>]*title="(.*?)"[^>]*>', action_cell)
            row_cells.append(",".join(action_titles))

        rows.append(row_cells)
    return rows


def any_user() -> User:
    user: User = User.objects.create_user(
        username="anyuser", is_staff=False, first_name="Jane", last_name="Smith", email="user@example.com"
    )
    return user


def any_membership_option(
    name: str = "any membership option",
    type: Tuple[str, Any] = MembershipOptionType.INDIVIDUAL,
    duration: str = "P1M",
    cost: str = "1.00",
) -> MembershipOption:
    membership_option: MembershipOption = MembershipOption.objects.create(
        name=name, type=type, duration=duration, cost=cost
    )
    return membership_option


def any_user_membership(
    user: Optional[User] = None, membership_option: Optional[MembershipOption] = None
) -> UserMembership:
    if not user:
        user = any_user()

    if not membership_option:
        membership_option = any_membership_option()

    start = timezone.localtime() - timedelta(days=7)

    user_membership: UserMembership = UserMembership.objects.create(
        user=user,
        membership_option=membership_option,
        created_datetime=start,
        start_date=start.date(),
        approved_datetime=start + timedelta(days=1),
    )

    return user_membership


def any_organisation_type(name: str = "Any Organisation Type") -> OrganisationType:
    organisation_type: OrganisationType = OrganisationType.objects.get_or_create(name=name)[0]
    return organisation_type


def any_organisation(organisation_type: Optional[OrganisationType] = None) -> Organisation:
    if not organisation_type:
        organisation_type = any_organisation_type()

    organisation: Organisation = Organisation.objects.create(
        type=organisation_type,
        name="Any Organisation",
        telephone="555-12345",
        contact_name="John Smith",
        email="john@example.com",
        street_address="123 Main Street",
        suburb="Some Suburb",
        city="Capital City",
        postal_address="PO BOX 1234",
        postal_suburb="Some Suburb",
        postal_city="Capital City",
        postal_code="8080",
    )
    return organisation


def any_organisation_membership(
    organisation: Optional[Organisation] = None, membership_option: Optional[MembershipOption] = None
) -> OrganisationMembership:
    if not organisation:
        organisation = any_organisation()

    if not membership_option:
        membership_option = any_membership_option(type=MembershipOptionType.ORGANISATION)

    start = timezone.localtime() - timedelta(days=7)

    organisation_membership: OrganisationMembership = OrganisationMembership.objects.create(
        organisation=organisation,
        membership_option=membership_option,
        created_datetime=start,
        start_date=start.date(),
    )

    return organisation_membership


def any_user_account(user: Optional[User] = None) -> Account:
    if not user:
        user = any_user()

    account: Account = Account.objects.create(user=user)
    return account


def any_organisation_account(organisation: Optional[Organisation] = None) -> Account:
    if not organisation:
        organisation = any_organisation()

    account: Account = Account.objects.create(organisation=organisation)
    return account


def any_invoice(account: Optional[Account] = None, invoice_number: str = "INV-1234") -> Invoice:
    if not account:
        account = any_user_account()

    invoice: Invoice = Invoice.objects.create(
        account=account,
        invoice_number=invoice_number,
        billing_service_invoice_id=None,
        issue_date=timezone.localdate(),
        due_date=timezone.localdate() + timedelta(days=30),
        amount=100,
        paid=0,
        due=0,
    )
    return invoice
