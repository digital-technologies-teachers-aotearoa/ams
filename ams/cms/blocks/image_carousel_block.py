from wagtail.blocks import BooleanBlock
from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import IntegerBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class CarouselSlideBlock(StructBlock):
    """Individual slide within a carousel."""

    image = ImageBlock(required=True)
    caption = CharBlock(
        required=False,
        help_text="Optional caption displayed on the slide",
    )
    attribution = CharBlock(
        required=False,
        help_text="Optional attribution for the image",
    )

    class Meta:
        icon = "image"
        label = "Slide"


class ImageCarouselBlock(StructBlock):
    """Bootstrap 5 image carousel with configurable options."""

    slides = ListBlock(
        CarouselSlideBlock(),
        min_num=1,
        help_text="Add images to the carousel. At least one image is required.",
    )

    # Carousel behavior options
    show_indicators = BooleanBlock(
        required=False,
        default=True,
        help_text="Show slide indicators (dots) at the bottom of the carousel",
    )

    show_controls = BooleanBlock(
        required=False,
        default=True,
        help_text="Show previous/next navigation arrows",
    )

    transition_type = ChoiceBlock(
        choices=[
            ("slide", "Slide"),
            ("fade", "Fade"),
        ],
        default="slide",
        help_text="Choose the transition effect between slides",
    )

    auto_advance = BooleanBlock(
        required=False,
        default=True,
        help_text="Automatically cycle through slides",
    )

    interval = IntegerBlock(
        required=False,
        default=5000,
        min_value=1000,
        max_value=30000,
        help_text=(
            "Time between slides in milliseconds (1000 = 1 second). "
            "Only applies if auto-advance is enabled."
        ),
    )

    border_style = ChoiceBlock(
        choices=[
            ("none", "None (Square corners)"),
            ("rounded", "Rounded corners"),
        ],
        default="none",
        required=False,
        help_text="Choose the image border style for all slides",
    )

    class Meta:
        icon = "image"
        label = "Image Carousel"
        template = "cms/blocks/image_carousel_block.html"
