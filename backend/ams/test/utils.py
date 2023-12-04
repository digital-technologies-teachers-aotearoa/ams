import re
from typing import Any, List, Optional

from django.http.response import HttpResponse


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
