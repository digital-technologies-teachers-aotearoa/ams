from cms.constants import BackgroundOpacities
from cms.constants import ColourModes
from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import PageChooserBlock
from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock
from wagtail.blocks import URLBlock
from wagtail.images.blocks import ImageBlock
from wagtail_color_panel.blocks import NativeColorBlock


class FullWidthSectionItem(StructBlock):
    """Individual item within a full-width section.

    E.g., a feature, service, or link.
    """

    text = CharBlock(
        required=True,
        max_length=255,
        help_text="Text for this item (e.g., 'Join Us', 'Events')",
    )
    link_page = PageChooserBlock(
        required=False,
        help_text="Internal page to link to (takes priority over external URL)",
    )
    link_url = URLBlock(
        required=False,
        help_text="External URL to link to (used if no internal page is selected)",
    )
    background_image = ImageBlock(
        required=False,
        help_text="Icon or image for this item (PNG/SVG recommended)",
    )
    background_image_opacity = ChoiceBlock(
        choices=BackgroundOpacities.choices,
        default=BackgroundOpacities.OPACITY_15,
        required=True,
        help_text="Opacity level for the item background image",
    )
    background_colour = NativeColorBlock(
        default="#333333",
        help_text="Used if no image is provided",
    )
    colour_mode = ChoiceBlock(
        choices=ColourModes.choices,
        default=ColourModes.DARK,
        required=True,
        help_text="Colour mode to use for the item (determines text colour)",
    )

    class Meta:
        icon = "placeholder"
        label = "Section Item"


class FullWidthSectionBlock(StructBlock):
    """Full-width section that visually extends to page edges with background image."""

    heading = CharBlock(
        required=False,
        max_length=255,
        help_text="Main heading for the section (e.g., 'How Can We Help')",
    )
    text = RichTextBlock(
        required=False,
        features=["bold", "italic"],
        help_text="Optional introductory text below the heading",
    )
    background_image = ImageBlock(
        required=False,
        help_text="Background image for the section (PNG/SVG)",
    )
    background_image_opacity = ChoiceBlock(
        choices=BackgroundOpacities.choices,
        default=BackgroundOpacities.OPACITY_15,
        required=True,
        help_text="Opacity level for the background image",
    )
    colour_mode = ChoiceBlock(
        choices=ColourModes.choices,
        default=ColourModes.DARK,
        required=True,
        help_text="Colour mode to use for the section",
    )
    item_shape = ChoiceBlock(
        choices=[
            ("default", "Default"),
            ("circle", "Circle"),
            ("parallelogram", "Parallelogram"),
        ],
        default="default",
        required=True,
        help_text="Shape style for items",
    )
    items = ListBlock(
        FullWidthSectionItem(),
        min_num=0,
        max_num=6,
        help_text="Add items to display in this section",
    )

    class Meta:
        icon = "image"
        label = "Full Width Section"
        template = "cms/blocks/full_width_section_block.html"
        help_text = "Uses the tertiary colour palette."
