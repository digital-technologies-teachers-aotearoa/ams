from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class CaptionedImageBlock(StructBlock):
    image = ImageBlock(required=True)
    caption = CharBlock(required=False)
    attribution = CharBlock(required=False)
    border_style = ChoiceBlock(
        choices=[
            ("none", "None (Square corners)"),
            ("rounded", "Rounded corners"),
            ("circle", "Circle"),
        ],
        default="none",
        required=False,
        help_text="Choose the image border style",
    )

    class Meta:
        icon = "image"
        template = "cms/blocks/captioned_image_block.html"
