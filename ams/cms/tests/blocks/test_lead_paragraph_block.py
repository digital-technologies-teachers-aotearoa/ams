"""Tests for LeadParagraphBlock."""

from ams.cms.blocks.lead_paragraph_block import LeadParagraphBlock


class TestLeadParagraphBlock:
    """Test the LeadParagraphBlock functionality."""

    def test_lead_paragraph_block_instantiation(self):
        """Test that LeadParagraphBlock can be instantiated."""
        block = LeadParagraphBlock()
        assert block is not None

    def test_lead_paragraph_block_has_text_field(self):
        """Test that LeadParagraphBlock has text field."""
        block = LeadParagraphBlock()
        assert "text" in block.child_blocks

    def test_lead_paragraph_block_text_field_required(self):
        """Test that text field is required."""
        block = LeadParagraphBlock()
        text_field = block.child_blocks["text"]
        assert text_field.required is True

    def test_lead_paragraph_block_text_field_has_alignment_features(self):
        """Test that the text field includes alignment features."""
        block = LeadParagraphBlock()
        text_field = block.child_blocks["text"]

        # Verify all alignment features are present
        assert "align-left" in text_field.features
        assert "align-center" in text_field.features
        assert "align-right" in text_field.features
        assert "align-justify" in text_field.features

    def test_lead_paragraph_block_text_field_has_other_features(self):
        """Test that the text field retains existing features."""
        block = LeadParagraphBlock()
        text_field = block.child_blocks["text"]

        # Verify existing features are still present
        assert "bold" in text_field.features
        assert "italic" in text_field.features
        assert "link" in text_field.features

    def test_lead_paragraph_block_render_with_text(self):
        """Test rendering block with text."""
        block = LeadParagraphBlock()
        value = block.to_python(
            {
                "text": "<p>This is a lead paragraph with some content.</p>",
            },
        )

        html = block.render(value)

        # Check that the text content is rendered
        assert "This is a lead paragraph with some content." in html
        assert "lead-paragraph" in html

    def test_lead_paragraph_block_render_with_formatted_text(self):
        """Test rendering block with formatted text."""
        block = LeadParagraphBlock()
        value = block.to_python(
            {
                "text": "<p><b>Bold text</b> and <i>italic text</i>.</p>",
            },
        )

        html = block.render(value)

        # Check that formatted content is preserved
        assert "Bold text" in html
        assert "italic text" in html

    def test_lead_paragraph_block_meta_properties(self):
        """Test block meta properties."""
        block = LeadParagraphBlock()
        assert block.meta.icon == "pilcrow"
        assert block.meta.template == "cms/blocks/lead_paragraph_block.html"
