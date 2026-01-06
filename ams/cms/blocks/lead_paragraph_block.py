from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock


class LeadParagraphBlock(StructBlock):
    text = RichTextBlock(features=["bold", "italic", "link"], required=True)

    class Meta:
        icon = "pilcrow"
        template = "cms/blocks/lead_paragraph_block.html"
