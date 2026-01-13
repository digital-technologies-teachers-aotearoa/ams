from wagtail.blocks import RichTextBlock
from wagtail.blocks import StreamBlock
from wagtail.embeds.blocks import EmbedBlock

from ams.cms.blocks.captioned_image_block import CaptionedImageBlock
from ams.cms.blocks.heading_block import HeadingBlock
from ams.cms.blocks.horizontal_rule_block import HorizontalRuleBlock
from ams.cms.blocks.image_carousel_block import ImageCarouselBlock
from ams.cms.blocks.image_grid_block import ImageGridBlock
from ams.cms.blocks.lead_paragraph_block import LeadParagraphBlock


class ContentStreamBlocks(StreamBlock):
    heading_block = HeadingBlock()
    paragraph_block = RichTextBlock(
        icon="pilcrow",
        features=[
            "bold",
            "italic",
            "link",
            "document-link",
            "ol",
            "ul",
            "superscript",
            "subscript",
            "strikethrough",
            "align-left",
            "align-center",
            "align-right",
            "align-justify",
        ],
    )
    lead_paragraph_block = LeadParagraphBlock()
    image_block = CaptionedImageBlock()
    image_grid_block = ImageGridBlock()
    image_carousel_block = ImageCarouselBlock()
    horizontal_rule_block = HorizontalRuleBlock()
    embed_block = EmbedBlock(
        help_text="Insert a URL to embed. For example, https://www.youtube.com/watch?v=V-6m0jW0X9E",
        icon="media",
    )


class ColumnContentStreamBlocks(ContentStreamBlocks):
    class Meta:
        label = "Column content"
        min_num = 0
