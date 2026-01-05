from wagtail.blocks import CharBlock
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import StructBlock
from wagtail_color_panel.blocks import NativeColorBlock


class TypographyBlock(StructBlock):
    text = CharBlock(required=True)
    size = ChoiceBlock(
        choices=[
            ("1", "Display size 1"),
            ("2", "Display size 2"),
            ("3", "Display size 3"),
            ("4", "Display size 4"),
            ("5", "Display size 5"),
            ("6", "Display size 6"),
        ],
        default="3",
        required=True,
        blank=False,
    )
    colour = NativeColorBlock(
        default="#222222",
        required=True,
        blank=False,
    )
    font_weight = ChoiceBlock(
        choices=[
            ("bold", "Bold weight"),
            ("semibold", "Semibold weight"),
            ("normal", "Normal weight"),
            ("light", "Light weight"),
        ],
        default="bold",
        required=True,
        blank=False,
    )

    class Meta:
        icon = "doc-full"
        collapsed = True


class SubtitleSettingsBlock(TypographyBlock):
    # Override text attribute to not required
    text = CharBlock(required=False)
    position = ChoiceBlock(
        choices=[
            ("before", "Before title"),
            ("after", "After title"),
        ],
        default="after",
        required=True,
        help_text="Where should the subtitle appear relative to the main title?",
    )

    class Meta:
        icon = "pilcrow"
        label = "Subtitle Settings"
        collapsed = True


class TitleBlock(StructBlock):
    title = TypographyBlock(
        label="Title Settings",
        # This forces the editor to fill in the title text
        field_kwargs={"text": {"required": True}},
        help_text="Configure the main heading text and style.",
    )
    subtitle = SubtitleSettingsBlock(
        required=False,
        label="Subtitle Settings",
    )
    alignment = ChoiceBlock(
        choices=[
            ("left", "Left aligned"),
            ("center", "Center aligned"),
        ],
        default="center",
        required=True,
        label="Layout Alignment",
    )

    class Meta:
        icon = "title"
        template = "cms/blocks/title_block.html"
