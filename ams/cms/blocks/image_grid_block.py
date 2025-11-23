from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class GridItemBlock(StructBlock):
    """Individual item within an image grid."""

    image = ImageBlock(required=True)
    title = CharBlock(
        required=True,
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
        required=False,
        help_text="Choose the image border style",
    )

    items = ListBlock(
        GridItemBlock(),
        min_num=1,
        help_text="Add items to the grid. At least one item is required.",
    )

    class Meta:
        icon = "image"
        label = "Image grid"
        template = "cms/blocks/image_grid_block.html"
