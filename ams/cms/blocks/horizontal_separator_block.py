from wagtail.blocks import ChoiceBlock
from wagtail.blocks import StructBlock
from wagtail.images.blocks import ImageBlock
from wagtail.models import Site

from ams.cms.models.theme import ThemeSettings


class HorizontalSeparatorBlock(StructBlock):
    separator_type = ChoiceBlock(
        choices=[
            ("default", "Use site default"),
            ("line", "Line"),
            ("image", "Tiled image"),
            ("centered", "Centered image"),
        ],
        default="default",
        label="Separator type",
    )
    separator_image = ImageBlock(
        required=False,
        label="Separator image",
        help_text=(
            "Overrides the site-default image."
            " Used when type is 'Tiled image' or 'Centered image'."
        ),
    )
    separator_width = ChoiceBlock(
        choices=[
            ("default", "Use site default"),
            ("content", "Content width"),
            ("full", "Full window width"),
        ],
        default="default",
        label="Separator width",
        help_text=(
            "Note: 'Full window width' may not render correctly inside column blocks."
        ),
    )

    @classmethod
    def construct_from_lookup(cls, lookup, child_blocks=None):
        # Old StaticBlock migrations stored no child_blocks; construct with defaults
        if child_blocks is None:
            return cls()
        return super().construct_from_lookup(lookup, child_blocks)

    def to_python(self, value):
        if value is None:
            value = {}
        return super().to_python(value)

    def bulk_to_python(self, values):
        return super().bulk_to_python([{} if v is None else v for v in values])

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        request = parent_context.get("request") if parent_context else None
        theme = None
        if request:
            site = Site.find_for_request(request)
            if site:
                theme = ThemeSettings.for_site(site)

        eff_type = value.get("separator_type", "default")
        if eff_type == "default":
            eff_type = getattr(theme, "separator_type", None) or "line"

        eff_width = value.get("separator_width", "default")
        if eff_width == "default":
            eff_width = getattr(theme, "separator_width", None) or "content"

        eff_image = value.get("separator_image")
        if not eff_image and theme:
            eff_image = theme.separator_image

        context["effective_type"] = eff_type
        context["effective_width"] = eff_width
        context["effective_image"] = eff_image
        return context

    class Meta:
        label = "Horizontal separator"
        icon = "minus"
        template = "cms/blocks/horizontal_separator_block.html"
        help_text = "Inserts a horizontal separator (line or tiled image)."
