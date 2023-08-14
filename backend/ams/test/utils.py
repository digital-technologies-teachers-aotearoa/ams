import re
from typing import Any, List

from django.http.response import HttpResponse


def parse_response_table_rows(response: HttpResponse) -> List[List[Any]]:
    rows = []
    for row in response.context["table"].rows:
        row_cells = [cell for cell in row.cells]

        # Parse the link titles in the action cell
        action_cell = row_cells.pop()
        action_titles = re.findall(r'<a[^>]*title="(.*?)"[^>]*>', action_cell)
        row_cells.append(",".join(action_titles))

        rows.append(row_cells)
    return rows
