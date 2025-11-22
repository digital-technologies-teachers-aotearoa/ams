from typing import Literal
from typing import TypedDict

from django.core.exceptions import ValidationError
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import StructBlock
from wagtail.blocks import StructBlockValidationError

from ams.cms.blocks.content_stream_blocks import ColumnContentStreamBlocks

ColumnValues = Literal[2, 3, 4]


class ColumnMetadata(TypedDict):
    """Type definition for column layout metadata."""

    name: str
    columns: ColumnValues


COLUMNS_METADATA: dict[str, ColumnMetadata] = {
    "2-equal": {"name": "2 Columns (Equal)", "columns": 2},
    "3-equal": {"name": "3 Columns (Equal)", "columns": 3},
    "4-equal": {"name": "4 Columns (Equal)", "columns": 4},
    "2-thirds-1-third": {"name": "2 Columns (2/3 + 1/3)", "columns": 2},
    "1-third-2-thirds": {"name": "2 Columns (1/3 + 2/3)", "columns": 2},
}


class ColumnsBlock(StructBlock):
    """Block for creating responsive multi-column layouts."""

    layout = ChoiceBlock(
        choices=[(key, meta["name"]) for key, meta in COLUMNS_METADATA.items()],
        default="2-equal",
        help_text=(
            "Select the column layout, then add the appropriate number of "
            "columns below."
        ),
    )

    columns = ListBlock(
        ColumnContentStreamBlocks(),
        min_num=2,
        max_num=4,
        help_text=(
            "Add columns here. Number of columns should match your layout choice."
        ),
    )

    def clean(self, value):
        cleaned_data = super().clean(value)
        layout = cleaned_data.get("layout")
        columns = cleaned_data.get("columns", [])
        column_metadata = COLUMNS_METADATA.get(layout)
        expected_count = column_metadata.get("columns")
        actual_count = len(columns)

        if expected_count and actual_count != expected_count:
            error_msg = (
                f"Layout '{column_metadata.get('name')}' requires exactly "
                f"{expected_count} column(s), but {actual_count} column(s) were "
                "provided."
            )
            raise StructBlockValidationError(
                block_errors={"columns": ValidationError(error_msg)},
            )
        return cleaned_data

    class Meta:
        icon = "grip"
        template = "cms/blocks/columns_block.html"
        label = "Columns"
