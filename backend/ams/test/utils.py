import re
from typing import Any, List, Optional

from django.contrib.auth.models import User
from django.http.response import HttpResponse

from ams.users.models import Organisation, OrganisationType


def parse_response_table_rows(response: HttpResponse, table_index: Optional[int] = None) -> List[List[Any]]:
    if table_index is not None:
        table = response.context["tables"][table_index]
    else:
        table = response.context["table"]

    rows = []
    for row in table.rows:
        row_cells = [cell for cell in row.cells]

        # Parse the link titles in the action cell
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
