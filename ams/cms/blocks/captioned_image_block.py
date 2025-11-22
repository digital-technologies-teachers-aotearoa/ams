from wagtail.blocks import CharBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class CaptionedImageBlock(StructBlock):
    image = ImageBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)

    class Meta:
        icon = "image"
        template = "cms/blocks/captioned_image_block.html"
