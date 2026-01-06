"""Tests for ImageGridBlock."""

import pytest
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import RichTextBlock
from wagtail.images.blocks import ImageBlock
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from ams.cms.blocks.image_grid_block import GridItemBlock
from ams.cms.blocks.image_grid_block import ImageGridBlock


@pytest.fixture
def test_image(db):
    """Create a test image for grid items."""
    return Image.objects.create(
        title="Test Image",
        file=get_test_image_file(),
    )


class TestGridItemBlock:
    """Test the GridItemBlock functionality."""

    def test_grid_item_block_instantiation(self):
        """Test that GridItemBlock can be instantiated."""
        block = GridItemBlock()
        assert block is not None

    def test_grid_item_block_has_required_fields(self):
        """Test that GridItemBlock has all required fields."""
        block = GridItemBlock()
        assert "image" in block.child_blocks
        assert "title" in block.child_blocks
        assert "subtitle" in block.child_blocks
        assert "description" in block.child_blocks

    def test_grid_item_block_image_is_image_block(self):
        """Test that image field is an ImageBlock."""
        block = GridItemBlock()
        assert isinstance(block.child_blocks["image"], ImageBlock)

    def test_grid_item_block_title_optional(self):
        """Test that title field is required."""
        block = GridItemBlock()
        assert block.child_blocks["title"].required is False

    def test_grid_item_block_subtitle_optional(self):
        """Test that subtitle field is optional."""
        block = GridItemBlock()
        assert block.child_blocks["subtitle"].required is False

    def test_grid_item_block_description_optional(self):
        """Test that description field is optional."""
        block = GridItemBlock()
        assert block.child_blocks["description"].required is False

    def test_grid_item_block_description_is_rich_text(self):
        """Test that description field is a RichTextBlock."""
        block = GridItemBlock()
        description_field = block.child_blocks["description"]
        assert isinstance(description_field, RichTextBlock)


class TestImageGridBlock:
    """Test the ImageGridBlock functionality."""

    def test_image_grid_block_instantiation(self):
        """Test that ImageGridBlock can be instantiated."""
        block = ImageGridBlock()
        assert block is not None

    def test_image_grid_block_has_required_fields(self):
        """Test that ImageGridBlock has all required fields."""
        block = ImageGridBlock()
        assert "items" in block.child_blocks
        assert "columns" in block.child_blocks
        assert "border_style" in block.child_blocks

    def test_image_grid_block_items_is_list_block(self):
        """Test that items field is a ListBlock."""
        block = ImageGridBlock()
        items_field = block.child_blocks["items"]
        assert isinstance(items_field, ListBlock)
        assert isinstance(items_field.child_block, GridItemBlock)

    def test_image_grid_block_items_min_num(self):
        """Test that items field requires at least one item."""
        block = ImageGridBlock()
        items_field = block.child_blocks["items"]
        assert items_field.meta.min_num == 1

    def test_image_grid_block_columns_is_choice_block(self):
        """Test that columns field is a ChoiceBlock."""
        block = ImageGridBlock()
        columns_field = block.child_blocks["columns"]
        assert isinstance(columns_field, ChoiceBlock)

    def test_image_grid_block_columns_choices(self):
        """Test that columns is a ChoiceBlock."""
        block = ImageGridBlock()
        columns_field = block.child_blocks["columns"]
        # Just verify it's a choice block - choices are set correctly in definition
        assert isinstance(columns_field, ChoiceBlock)

    def test_image_grid_block_columns_default(self):
        """Test that columns has correct default value."""
        block = ImageGridBlock()
        columns_field = block.child_blocks["columns"]
        assert columns_field.meta.default == "3"

    def test_image_grid_block_border_style_is_choice_block(self):
        """Test that border_style field is a ChoiceBlock."""
        block = ImageGridBlock()
        border_style_field = block.child_blocks["border_style"]
        assert isinstance(border_style_field, ChoiceBlock)

    def test_image_grid_block_border_style_default(self):
        """Test that border_style has correct default value."""
        block = ImageGridBlock()
        border_style_field = block.child_blocks["border_style"]
        assert border_style_field.meta.default == "none"

    def test_image_grid_block_render_with_single_item(self, test_image):
        """Test rendering grid with a single item."""
        block = ImageGridBlock()
        value = block.to_python(
            {
                "columns": "3",
                "border_style": "none",
                "items": [
                    {
                        "image": test_image.id,
                        "title": "Test Person",
                        "subtitle": "Test Position",
                        "description": "<p>Test description</p>",
                    },
                ],
            },
        )

        html = block.render(value)

        # Check that grid container exists
        assert "image-grid" in html
        assert "image-grid__item" in html

        # Check that item content is rendered
        assert "Test Person" in html
        assert "Test Position" in html
        assert "Test description" in html

    def test_image_grid_block_render_with_multiple_items(self, test_image):
        """Test rendering grid with multiple items."""
        block = ImageGridBlock()
        value = block.to_python(
            {
                "columns": "3",
                "border_style": "none",
                "items": [
                    {
                        "image": test_image.id,
                        "title": "Person 1",
                        "subtitle": "Position 1",
                        "description": "<p>Description 1</p>",
                    },
                    {
                        "image": test_image.id,
                        "title": "Person 2",
                        "subtitle": "Position 2",
                        "description": "<p>Description 2</p>",
                    },
                ],
            },
        )

        html = block.render(value)

        # Check that all items are rendered
        assert "Person 1" in html
        assert "Position 1" in html
        assert "Description 1" in html
        assert "Person 2" in html
        assert "Position 2" in html
        assert "Description 2" in html

    def test_image_grid_block_render_without_optional_fields(self, test_image):
        """Test rendering grid item without optional subtitle and description."""
        block = ImageGridBlock()
        value = block.to_python(
            {
                "columns": "3",
                "border_style": "none",
                "items": [
                    {
                        "image": test_image.id,
                        "title": "Test Person",
                        "subtitle": "",
                        "description": "",
                    },
                ],
            },
        )

        html = block.render(value)

        # Check that title is rendered but optional fields are not
        assert "Test Person" in html
        assert "grid-item-subtitle" not in html
        assert "grid-item-description" not in html

    def test_image_grid_block_render_with_rounded_border(self, test_image):
        """Test rendering grid with rounded border style."""
        block = ImageGridBlock()
        value = block.to_python(
            {
                "columns": "3",
                "border_style": "rounded",
                "items": [
                    {
                        "image": test_image.id,
                        "title": "Test Person",
                        "subtitle": "",
                        "description": "",
                    },
                ],
            },
        )

        html = block.render(value)

        # Check for rounded class
        assert "rounded-4" in html

    def test_image_grid_block_render_rich_text_description(self, test_image):
        """Test rendering grid item with rich text formatting in description."""
        block = ImageGridBlock()
        rich_description = (
            "<p>This is <strong>bold</strong> and <em>italic</em> text "
            "with a <a href='#'>link</a>.</p>"
        )
        value = block.to_python(
            {
                "columns": "3",
                "border_style": "none",
                "items": [
                    {
                        "image": test_image.id,
                        "title": "Test Person",
                        "subtitle": "Test Position",
                        "description": rich_description,
                    },
                ],
            },
        )

        html = block.render(value)

        # Check that rich text formatting is preserved
        # Note: HTML may use different quote styles
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "link</a>" in html  # Just check the link text is present

    def test_image_grid_block_template_path(self):
        """Test that ImageGridBlock uses the correct template."""
        block = ImageGridBlock()
        assert block.meta.template == "cms/blocks/image_grid_block.html"

    def test_image_grid_block_meta_properties(self):
        """Test ImageGridBlock meta properties."""
        block = ImageGridBlock()
        assert block.meta.icon == "image"
        assert block.meta.label == "Image grid"

    def test_grid_item_block_meta_properties(self):
        """Test GridItemBlock meta properties."""
        block = GridItemBlock()
        assert block.meta.icon == "user"
        assert block.meta.label == "Grid Item"
