from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class CaptionedImageBlock(StructBlock):
    image = ImageBlock(required=True)
    image_scaling = ChoiceBlock(
        choices=[
            ("fit", "Fit (don't crop, suitable for logos)"),
            ("fill", "Fill square (crop to fill, suitable for photos)"),
        ],
        default="center",
        help_text="Alignment of items within grid (if space available)",
    )
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
