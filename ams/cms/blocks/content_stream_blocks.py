from wagtail.blocks import RichTextBlock
from wagtail.blocks import StreamBlock
from wagtail.embeds.blocks import EmbedBlock

from .captioned_image_block import CaptionedImageBlock
from .heading_block import HeadingBlock
from .horizontal_rule_block import HorizontalRuleBlock
from .image_carousel_block import ImageCarouselBlock
from .image_grid_block import ImageGridBlock


class ContentStreamBlocks(StreamBlock):
    heading_block = HeadingBlock()
    paragraph_block = RichTextBlock(icon="pilcrow")
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
