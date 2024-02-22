import re
from datetime import timedelta
from typing import Any, List, Optional, Tuple

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.utils import timezone

from ams.users.models import (
    MembershipOption,
    MembershipOptionType,
    Organisation,
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


def any_organisation() -> Organisation:
    organisation: Organisation = Organisation.objects.create(
        type=OrganisationType.objects.create(name="Any Organisation Type"),
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
