from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.blocks import RichTextBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock


class TimelineItemBlock(StructBlock):
    date = CharBlock(
        max_length=100,
        help_text="Date label for this event (e.g. '1892', 'March 1945', '1850-1900')",
    )
    heading = CharBlock(
        required=False,
        max_length=255,
        help_text="Optional heading for this event",
    )
    body = RichTextBlock(
        required=False,
        features=["bold", "italic", "link", "ol", "ul"],
        help_text="Content for this event",
    )
    image = ImageBlock(
        required=False,
        help_text="Optional image — displayed at the top of the card (card style only)",
    )

    class Meta:
        icon = "date"
        label = "Timeline event"


class TimelineBlock(StructBlock):
    style = ChoiceBlock(
        choices=[
            ("plain", "Plain text"),
            ("card", "Cards (with optional image)"),
        ],
        default="plain",
        help_text="Choose how each event is displayed",
    )
    items = ListBlock(
        TimelineItemBlock(),
        min_num=1,
        help_text="Add events to the timeline. At least one event is required.",
        collapsed=True,
    )

    class Meta:
        icon = "list-ul"
        label = "Timeline"
        template = "cms/blocks/timeline_block.html"
