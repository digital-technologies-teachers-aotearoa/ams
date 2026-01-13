"""Tests for FullWidthSectionBlock."""

from ams.cms.blocks.full_width_section_block import FullWidthSectionBlock


class TestFullWidthSectionBlock:
    """Test the FullWidthSectionBlock functionality."""

    def test_full_width_section_block_instantiation(self):
        """Test that FullWidthSectionBlock can be instantiated."""
        block = FullWidthSectionBlock()
        assert block is not None

    def test_full_width_section_block_has_required_fields(self):
        """Test that FullWidthSectionBlock has all required fields."""
        block = FullWidthSectionBlock()
        assert "heading" in block.child_blocks
        assert "text" in block.child_blocks
        assert "background_image" in block.child_blocks
        assert "background_image_opacity" in block.child_blocks
        assert "colour_mode" in block.child_blocks
        assert "item_shape" in block.child_blocks
        assert "items" in block.child_blocks

    def test_full_width_section_block_text_field_has_alignment_features(self):
        """Test that the text field includes alignment features."""
        block = FullWidthSectionBlock()
        text_field = block.child_blocks["text"]

        # Verify all alignment features are present
        assert "align-left" in text_field.features
        assert "align-center" in text_field.features
        assert "align-right" in text_field.features
        assert "align-justify" in text_field.features

    def test_full_width_section_block_text_field_has_existing_features(self):
        """Test that the text field retains existing features."""
        block = FullWidthSectionBlock()
        text_field = block.child_blocks["text"]

        # Verify existing features are still present
        assert "bold" in text_field.features
        assert "italic" in text_field.features

    def test_full_width_section_block_text_field_optional(self):
        """Test that text field is optional."""
        block = FullWidthSectionBlock()
        text_field = block.child_blocks["text"]
        assert text_field.required is False

    def test_full_width_section_block_render_with_text(self):
        """Test rendering block with text."""
        block = FullWidthSectionBlock()
        value = block.to_python(
            {
                "heading": "Test Heading",
                "text": "<p>Test paragraph</p>",
                "background_image": None,
                "background_image_opacity": "15",
                "colour_mode": "dark",
                "item_shape": "default",
                "items": [],
            },
        )

        html = block.render(value)

        # Check that the text content is rendered
        assert "Test Heading" in html
        assert "Test paragraph" in html
        assert "full-width-section" in html

    def test_full_width_section_block_render_without_text(self):
        """Test rendering block without text."""
        block = FullWidthSectionBlock()
        value = block.to_python(
            {
                "heading": "Test Heading",
                "text": "",
                "background_image": None,
                "background_image_opacity": "15",
                "colour_mode": "dark",
                "item_shape": "default",
                "items": [],
            },
        )

        html = block.render(value)

        # Check that heading is rendered but intro section is not
        assert "Test Heading" in html
        assert "full-width-section__intro" not in html

    def test_full_width_section_block_meta_properties(self):
        """Test block meta properties."""
        block = FullWidthSectionBlock()
        assert block.meta.icon == "image"
        assert block.meta.label == "Full Width Section"
        assert block.meta.template == "cms/blocks/full_width_section_block.html"
