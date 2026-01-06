from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import PageChooserBlock
from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock
from wagtail.blocks import URLBlock
from wagtail.images.blocks import ImageBlock


class GridItemBlock(StructBlock):
    """Individual item within an image grid."""

    image = ImageBlock(required=True)
    image_scaling = ChoiceBlock(
        choices=[
            ("fit", "Fit (don't crop, suitable for logos)"),
            ("fill", "Fill (crop to fill, suitable for photos)"),
        ],
        default="center",
        help_text="Alignment of items within grid (if space available)",
    )
    title = CharBlock(
        required=False,
        max_length=255,
        help_text="Title for this grid item (e.g., person's name or item title)",
    )
    subtitle = CharBlock(
        required=False,
        max_length=255,
        help_text="Optional subtitle (e.g., position, role, or item category)",
    )
    description = RichTextBlock(
        required=False,
        features=["bold", "italic", "link"],
        help_text="Optional rich text description",
    )
    link_page = PageChooserBlock(
        required=False,
        help_text="Internal page to link to (takes priority over external URL)",
    )
    link_url = URLBlock(
        required=False,
        help_text="External URL to link to (used if no internal page is selected)",
    )

    class Meta:
        icon = "user"
        label = "Grid Item"


class ImageGridBlock(StructBlock):
    """Grid layout for displaying images with titles, subtitles, and descriptions."""

    columns = ChoiceBlock(
        choices=[
            ("2", "2 columns"),
            ("3", "3 columns"),
            ("4", "4 columns"),
            ("6", "6 columns"),
        ],
        default="3",
        help_text="Number of columns in the grid (responsive on smaller screens)",
    )
    border_style = ChoiceBlock(
        choices=[
            ("none", "None (Square corners)"),
            ("rounded", "Rounded corners"),
            ("circle", "Circle"),
        ],
        default="none",
        required=True,
        help_text="Choose the image border style",
    )
    image_alignment = ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
        ],
        default="center",
        required=True,
        help_text="Alignment of items within grid (if space available)",
    )
    text_alignment = ChoiceBlock(
        choices=[
            ("left", "Left"),
            ("center", "Center"),
        ],
        default="center",
        required=True,
        help_text="Alignment of text",
    )

    items = ListBlock(
        GridItemBlock(),
        min_num=1,
        help_text="Add items to the grid. At least one item is required.",
        collapsed=True,
    )

    class Meta:
        icon = "image"
        label = "Image grid"
        template = "cms/blocks/image_grid_block.html"
