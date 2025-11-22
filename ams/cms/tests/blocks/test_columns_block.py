"""Tests for CMS blocks."""

from typing import get_args

import pytest
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import StructBlockValidationError

from ams.cms.blocks.columns_block import COLUMNS_METADATA
from ams.cms.blocks.columns_block import ColumnsBlock
from ams.cms.blocks.columns_block import ColumnValues

# Constants for testing
MIN_COLUMNS = min(get_args(ColumnValues))
MAX_COLUMNS = max(get_args(ColumnValues))


class TestColumnsBlock:
    """Test the ColumnsBlock functionality."""

    def test_columns_block_instantiation(self):
        """Test that ColumnsBlock can be instantiated."""
        block = ColumnsBlock()
        assert block is not None

    def test_columns_block_has_layout_choices(self):
        """Test that ColumnsBlock has the expected layout choices."""
        block = ColumnsBlock()
        layout_field = block.child_blocks["layout"]

        # Check that the layout field is a ChoiceBlock
        assert isinstance(layout_field, ChoiceBlock)

    def test_columns_block_has_columns_field(self):
        """Test that ColumnsBlock has a columns ListBlock field."""
        block = ColumnsBlock()
        assert "columns" in block.child_blocks
        columns_field = block.child_blocks["columns"]
        assert isinstance(columns_field, ListBlock)

    def test_columns_block_columns_are_stream_blocks(self):
        """Test that column fields are StreamBlocks."""
        block = ColumnsBlock()
        columns_field = block.child_blocks["columns"]
        column_block = columns_field.child_block

        # Check that it has the expected child blocks
        assert "heading_block" in column_block.child_blocks
        assert "paragraph_block" in column_block.child_blocks
        assert "image_block" in column_block.child_blocks
        assert "embed_block" in column_block.child_blocks

    def test_columns_block_render_with_2_equal_layout(self):
        """Test rendering with 2 equal columns layout."""
        block = ColumnsBlock()
        value = block.to_python(
            {
                "layout": "2-equal",
                "columns": [[], []],
            },
        )

        html = block.render(value)
        assert "col-12 col-md-6" in html
        assert "row" in html

    def test_columns_block_render_with_3_equal_layout(self):
        """Test rendering with 3 equal columns layout."""
        block = ColumnsBlock()
        value = block.to_python(
            {
                "layout": "3-equal",
                "columns": [[], [], []],
            },
        )

        html = block.render(value)
        assert "col-12 col-md-4" in html

    def test_columns_block_render_with_2_thirds_1_third_layout(self):
        """Test rendering with 2/3 + 1/3 layout."""
        block = ColumnsBlock()
        value = block.to_python(
            {
                "layout": "2-thirds-1-third",
                "columns": [[], []],
            },
        )

        html = block.render(value)
        assert "col-12 col-md-8" in html
        assert "col-12 col-md-4" in html

    def test_columns_block_min_max_columns(self):
        """Test that columns have min/max constraints."""
        block = ColumnsBlock()
        columns_field = block.child_blocks["columns"]

        # Check min and max constraints
        assert columns_field.meta.min_num == MIN_COLUMNS
        assert columns_field.meta.max_num == MAX_COLUMNS

    def test_columns_metadata_structure(self):
        """Test that COLUMNS_METADATA has the correct structure."""
        # Check that COLUMNS_METADATA is not empty
        assert len(COLUMNS_METADATA) > 0

        # Check each entry has the required fields with correct types
        for key, metadata in COLUMNS_METADATA.items():
            assert isinstance(key, str), f"Key '{key}' must be a string"
            assert isinstance(metadata, dict), f"Metadata for '{key}' must be a dict"
            assert "name" in metadata, f"Metadata for '{key}' missing 'name' field"
            assert "columns" in metadata, (
                f"Metadata for '{key}' missing 'columns' field"
            )
            assert isinstance(
                metadata["name"],
                str,
            ), f"'name' for '{key}' must be a string"
            assert isinstance(
                metadata["columns"],
                int,
            ), f"'columns' for '{key}' must be an int"
            assert metadata["columns"] >= MIN_COLUMNS, (
                f"'columns' for '{key}' must be >= {MIN_COLUMNS}"
            )
            assert metadata["columns"] <= MAX_COLUMNS, (
                f"'columns' for '{key}' must be <= {MAX_COLUMNS}"
            )

    def test_columns_block_below_minimum_columns(self):
        """Test that validation passes with correct column count."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "2-equal",
                    "columns": [
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                    ],
                },
            )
        assert "columns" in excinfo.value.block_errors

    def test_columns_block_over_maximum_columns(self):
        """Test that validation passes with correct column count."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "2-equal",
                    "columns": [
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                    ],
                },
            )
        assert "columns" in excinfo.value.block_errors

    def test_columns_block_as_2_equal_valid(self):
        """Test validation passes with correct column count for 2-equal."""
        block = ColumnsBlock()
        block.clean(
            {
                "layout": "2-equal",
                "columns": [
                    [
                        {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 2</p>"},
                    ],
                ],
            },
        )

    def test_columns_block_as_2_equal_invalid_columns(self):
        """Test validation fails with incorrect column count for 2-equal."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "2-equal",
                    "columns": [
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                        [
                            {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                        ],
                    ],
                },
            )
        error_dict = excinfo.value.block_errors
        assert "columns" in error_dict
        assert "requires exactly 2 column(s)" in str(error_dict["columns"])

    def test_columns_block_as_3_equal_valid(self):
        """Test validation passes with correct column count for 3-equal."""
        block = ColumnsBlock()
        block.clean(
            {
                "layout": "3-equal",
                "columns": [
                    [
                        {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 2</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 3</p>"},
                    ],
                ],
            },
        )

    def test_columns_block_as_3_equal_invalid_columns(self):
        """Test validation fails with incorrect column count for 3-equal."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "3-equal",
                    "columns": [
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 1</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 2</p>",
                            },
                        ],
                    ],
                },
            )
        error_dict = excinfo.value.block_errors
        assert "columns" in error_dict
        assert "requires exactly 3 column(s)" in str(error_dict["columns"])

    def test_columns_block_as_4_equal_valid(self):
        """Test validation passes with correct column count for 4-equal."""
        block = ColumnsBlock()
        block.clean(
            {
                "layout": "4-equal",
                "columns": [
                    [
                        {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 2</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 3</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 4</p>"},
                    ],
                ],
            },
        )

    def test_columns_block_as_4_equal_invalid_columns(self):
        """Test validation fails with incorrect column count for 4-equal."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "4-equal",
                    "columns": [
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 1</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 2</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 3</p>",
                            },
                        ],
                    ],
                },
            )
        error_dict = excinfo.value.block_errors
        assert "columns" in error_dict
        assert "requires exactly 4 column(s)" in str(error_dict["columns"])

    def test_columns_block_as_2_thirds_1_third_valid(self):
        """Test validation passes with correct column count for 2-thirds-1-third."""
        block = ColumnsBlock()
        block.clean(
            {
                "layout": "2-thirds-1-third",
                "columns": [
                    [
                        {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 2</p>"},
                    ],
                ],
            },
        )

    def test_columns_block_as_2_thirds_1_third_invalid_columns(self):
        """Test validation fails with incorrect column count for 2-thirds-1-third."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "2-thirds-1-third",
                    "columns": [
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 1</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 2</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 3</p>",
                            },
                        ],
                    ],
                },
            )
        error_dict = excinfo.value.block_errors
        assert "columns" in error_dict
        assert "requires exactly 2 column(s)" in str(error_dict["columns"])

    def test_columns_block_as_1_third_2_thirds_valid(self):
        """Test validation passes with correct column count for 1-third-2-thirds."""
        block = ColumnsBlock()
        block.clean(
            {
                "layout": "1-third-2-thirds",
                "columns": [
                    [
                        {"type": "paragraph_block", "value": "<p>Content 1</p>"},
                    ],
                    [
                        {"type": "paragraph_block", "value": "<p>Content 2</p>"},
                    ],
                ],
            },
        )

    def test_columns_block_as_1_third_2_thirds_invalid_columns(self):
        """Test validation fails with incorrect column count for 1-third-2-thirds."""
        block = ColumnsBlock()
        with pytest.raises(StructBlockValidationError) as excinfo:
            block.clean(
                {
                    "layout": "1-third-2-thirds",
                    "columns": [
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 1</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 2</p>",
                            },
                        ],
                        [
                            {
                                "type": "paragraph_block",
                                "value": "<p>Content 3</p>",
                            },
                        ],
                    ],
                },
            )
        error_dict = excinfo.value.block_errors
        assert "columns" in error_dict
        assert "requires exactly 2 column(s)" in str(error_dict["columns"])
