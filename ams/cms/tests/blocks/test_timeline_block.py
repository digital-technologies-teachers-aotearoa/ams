"""Tests for TimelineBlock."""

import pytest
from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import RichTextBlock
from wagtail.images.blocks import ImageBlock
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Collection

from ams.cms.blocks.timeline_block import TimelineBlock
from ams.cms.blocks.timeline_block import TimelineItemBlock


@pytest.fixture
def test_image(db):
    """Create a test image for timeline items."""
    return Image.objects.create(
        title="Test Image",
        file=get_test_image_file(),
        collection=Collection.get_first_root_node(),
    )


class TestTimelineItemBlock:
    """Test the TimelineItemBlock field structure."""

    def test_instantiation(self):
        """Test that TimelineItemBlock can be instantiated."""
        block = TimelineItemBlock()
        assert block is not None

    def test_has_all_fields(self):
        """Test that all four fields are present."""
        block = TimelineItemBlock()
        assert "date" in block.child_blocks
        assert "heading" in block.child_blocks
        assert "body" in block.child_blocks
        assert "image" in block.child_blocks

    def test_date_is_required(self):
        """Test that date field is required."""
        block = TimelineItemBlock()
        assert block.child_blocks["date"].required is True

    def test_date_max_length(self):
        """Test that date field has correct max length."""
        block = TimelineItemBlock()
        expected_length = 100
        assert block.child_blocks["date"].field.max_length == expected_length

    def test_date_is_char_block(self):
        """Test that date field is a CharBlock."""
        block = TimelineItemBlock()
        assert isinstance(block.child_blocks["date"], CharBlock)

    def test_heading_is_optional(self):
        """Test that heading field is optional."""
        block = TimelineItemBlock()
        assert block.child_blocks["heading"].required is False

    def test_body_is_optional(self):
        """Test that body field is optional."""
        block = TimelineItemBlock()
        assert block.child_blocks["body"].required is False

    def test_body_is_rich_text_block(self):
        """Test that body field is a RichTextBlock."""
        block = TimelineItemBlock()
        assert isinstance(block.child_blocks["body"], RichTextBlock)

    def test_body_has_list_features(self):
        """Test that body supports ordered and unordered lists."""
        block = TimelineItemBlock()
        features = block.child_blocks["body"].features
        assert "ol" in features
        assert "ul" in features

    def test_image_is_optional(self):
        """Test that image field is optional."""
        block = TimelineItemBlock()
        assert block.child_blocks["image"].required is False

    def test_image_is_image_block(self):
        """Test that image field is an ImageBlock."""
        block = TimelineItemBlock()
        assert isinstance(block.child_blocks["image"], ImageBlock)

    def test_meta_properties(self):
        """Test TimelineItemBlock meta properties."""
        block = TimelineItemBlock()
        assert block.meta.icon == "date"
        assert block.meta.label == "Timeline event"


class TestTimelineBlock:
    """Test the TimelineBlock functionality."""

    def test_instantiation(self):
        """Test that TimelineBlock can be instantiated."""
        block = TimelineBlock()
        assert block is not None

    def test_has_required_fields(self):
        """Test that style and items fields are present."""
        block = TimelineBlock()
        assert "style" in block.child_blocks
        assert "items" in block.child_blocks

    def test_style_is_choice_block(self):
        """Test that style field is a ChoiceBlock."""
        block = TimelineBlock()
        assert isinstance(block.child_blocks["style"], ChoiceBlock)

    def test_style_default_is_plain(self):
        """Test that the default style is plain text."""
        block = TimelineBlock()
        assert block.child_blocks["style"].meta.default == "plain"

    def test_items_is_list_block(self):
        """Test that items field is a ListBlock of TimelineItemBlocks."""
        block = TimelineBlock()
        items_field = block.child_blocks["items"]
        assert isinstance(items_field, ListBlock)
        assert isinstance(items_field.child_block, TimelineItemBlock)

    def test_items_min_num(self):
        """Test that items requires at least one event."""
        block = TimelineBlock()
        items_field = block.child_blocks["items"]
        assert items_field.meta.min_num == 1

    def test_meta_properties(self):
        """Test TimelineBlock meta properties."""
        block = TimelineBlock()
        assert block.meta.icon == "list-ul"
        assert block.meta.label == "Timeline"
        assert block.meta.template == "cms/blocks/timeline_block.html"

    def test_render_plain_style(self):
        """Test that plain style renders dates and headings in HTML."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "plain",
                "items": [
                    {
                        "date": "1850",
                        "heading": "First Event",
                        "body": "<p>Something happened.</p>",
                        "image": None,
                    },
                    {
                        "date": "1900",
                        "heading": "Second Event",
                        "body": "<p>More things happened.</p>",
                        "image": None,
                    },
                ],
            },
        )

        html = block.render(value)

        assert "1850" in html
        assert "First Event" in html
        assert "Something happened." in html
        assert "1900" in html
        assert "Second Event" in html

    def test_render_plain_style_does_not_use_card_class(self):
        """Test that plain style does not render the Bootstrap card class."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "plain",
                "items": [
                    {
                        "date": "1892",
                        "heading": "An Event",
                        "body": "",
                        "image": None,
                    },
                ],
            },
        )

        html = block.render(value)

        assert 'class="card"' not in html

    def test_render_card_style_uses_card_class(self, test_image):
        """Test that card style renders the Bootstrap card class."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "card",
                "items": [
                    {
                        "date": "1892",
                        "heading": "Card Event",
                        "body": "<p>With card styling.</p>",
                        "image": None,
                    },
                ],
            },
        )

        html = block.render(value)

        assert "card" in html
        assert "1892" in html
        assert "Card Event" in html

    def test_render_card_style_with_image(self, test_image):
        """Test that card style renders an image when provided."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "card",
                "items": [
                    {
                        "date": "1920",
                        "heading": "Event with Image",
                        "body": "<p>Has a photo.</p>",
                        "image": test_image.id,
                    },
                ],
            },
        )

        html = block.render(value)

        assert "card-img-top" in html
        assert "1920" in html
        assert "Event with Image" in html

    def test_render_optional_heading_omitted(self):
        """Test that omitting heading does not leave an empty heading element."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "plain",
                "items": [
                    {
                        "date": "1776",
                        "heading": "",
                        "body": "<p>Body only.</p>",
                        "image": None,
                    },
                ],
            },
        )

        html = block.render(value)

        assert "1776" in html
        assert "<h4" not in html

    def test_render_multiple_items(self):
        """Test that all items appear in the rendered output."""
        block = TimelineBlock()
        value = block.to_python(
            {
                "style": "plain",
                "items": [
                    {"date": "Year 1", "heading": "Event 1", "body": "", "image": None},
                    {"date": "Year 2", "heading": "Event 2", "body": "", "image": None},
                    {"date": "Year 3", "heading": "Event 3", "body": "", "image": None},
                ],
            },
        )

        html = block.render(value)

        assert "Year 1" in html
        assert "Year 2" in html
        assert "Year 3" in html
        assert "Event 1" in html
        assert "Event 2" in html
        assert "Event 3" in html
