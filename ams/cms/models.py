from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.db import models
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.models import register_setting
from wagtail.documents.models import AbstractDocument
from wagtail.documents.models import Document
from wagtail.fields import StreamField
from wagtail.models import Page

from ams.cms.blocks import ContentAndLayoutStreamBlocks
from ams.cms.validators import validate_hex_color
from ams.utils.permissions import user_has_active_membership
from ams.utils.reserved_paths import get_reserved_paths_set


class HomePage(Page):
    body = StreamField(
        ContentAndLayoutStreamBlocks(),
        blank=True,
        use_json_field=True,
        help_text="Content for the home page.",
    )

    # Metadata
    content_panels = [*Page.content_panels, "body"]
    template = "cms/pages/home.html"


class ContentPage(Page):
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_MEMBERS = "members"
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_MEMBERS, "Members only"),
    ]

    body = StreamField(
        ContentAndLayoutStreamBlocks(),
        blank=True,
        use_json_field=True,
        help_text="Content for this page.",
    )

    visibility = models.CharField(
        max_length=16,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        help_text=(
            "Who can view this page: everyone or only members with active membership.",
        ),
    )

    # Metadata
    content_panels = [
        *Page.content_panels,
        FieldPanel("visibility"),
        FieldPanel("body"),
    ]
    template = "cms/pages/content.html"
    parent_page_types = ["cms.HomePage", "cms.ContentPage"]
    subpage_types = ["cms.ContentPage"]
    show_in_menus = True

    def serve(self, request, *args, **kwargs):
        """Override serve to enforce visibility restrictions."""
        if self.visibility == self.VISIBILITY_MEMBERS:
            if not user_has_active_membership(request.user):
                return HttpResponseForbidden(
                    "This page is only available to members with an active membership.",
                )
        return super().serve(request, *args, **kwargs)

    def clean(self):
        """Validate that the page slug doesn't conflict with reserved URLs."""
        super().clean()

        reserved_paths = get_reserved_paths_set()
        # Only check direct children of HomePage for reserved slug conflicts
        if (
            self.get_parent()
            and self.get_parent().specific.__class__.__name__ == "HomePage"
            and self.slug in reserved_paths
        ):
            raise ValidationError(
                {
                    "slug": f'The slug "{self.slug}" is reserved for application URLs. '
                    f"Please choose a different slug. Reserved slugs are: "
                    f"{', '.join(sorted(reserved_paths))}",
                },
            )


@register_setting
class SiteSettings(BaseSiteSetting):
    language = models.CharField(
        max_length=10,
        verbose_name="Language",
        blank=True,
        choices=settings.LANGUAGES,
    )

    panels = [
        FieldPanel("language"),
    ]


@register_setting
class AssociationSettings(BaseSiteSetting):
    association_short_name = models.CharField(
        max_length=255,
        verbose_name="Association short name",
        blank=True,
    )
    association_long_name = models.CharField(
        max_length=255,
        verbose_name="Association long name",
        blank=True,
    )
    association_logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Association logo",
    )
    association_favicon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Association favicon",
    )
    use_logo_in_navbar = models.BooleanField(
        default=False,
        verbose_name="Use logo in navbar",
        help_text="If not set, the association short name will be used in the navbar.",
    )
    use_logo_in_footer = models.BooleanField(
        default=False,
        verbose_name="Use logo in footer",
        help_text="If not set, the association short name will be used in the footer.",
    )
    linkedin_url = models.URLField(
        verbose_name="LinkedIn URL",
        blank=True,
        help_text="If set, a link will appear in the footer.",
    )
    facebook_url = models.URLField(
        verbose_name="Facebook URL",
        blank=True,
        help_text="If set, a link will appear in the footer.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("association_short_name"),
                FieldPanel("association_long_name"),
            ],
            "Name",
        ),
        MultiFieldPanel(
            [
                FieldPanel("association_logo"),
                FieldPanel("use_logo_in_navbar"),
                FieldPanel("use_logo_in_footer"),
                FieldPanel("association_favicon"),
            ],
            "Images",
        ),
        MultiFieldPanel(
            [
                FieldPanel("linkedin_url"),
                FieldPanel("facebook_url"),
            ],
            "Social networks",
        ),
    ]


@register_setting
class ThemeSettings(BaseSiteSetting):
    """Theme customization settings for Bootstrap CSS variables.

    Allows customization of colors and appearance without code deployment.
    Organized to match Bootstrap 5.3 color documentation.
    Changes are cached for performance.
    """

    # Version tracking for cache invalidation
    css_version = models.IntegerField(
        default=1,
        editable=False,
        help_text="Auto-incremented on save to invalidate cached CSS",
    )

    # ==== BODY COLORS ====
    # Default foreground (color) and background, including components
    body_color_light = models.CharField(
        max_length=7,
        default="#212529",
        validators=[validate_hex_color],
        verbose_name="Body text color (light)",
        help_text="Light mode: Default foreground color for text",
    )
    body_bg_light = models.CharField(
        max_length=7,
        default="#ffffff",
        validators=[validate_hex_color],
        verbose_name="Body background (light)",
        help_text="Light mode: Default background for body",
    )
    body_color_dark = models.CharField(
        max_length=7,
        default="#dee2e6",
        validators=[validate_hex_color],
        verbose_name="Body text color (dark)",
        help_text="Dark mode: Default foreground color for text",
    )
    body_bg_dark = models.CharField(
        max_length=7,
        default="#212529",
        validators=[validate_hex_color],
        verbose_name="Body background (dark)",
        help_text="Dark mode: Default background for body",
    )
    # ==== SECONDARY COLORS ====
    # Use color for lighter text. Use bg for dividers and disabled states
    secondary_color_light = models.CharField(
        max_length=7,
        default="#6c757d",
        validators=[validate_hex_color],
        verbose_name="Secondary text (light)",
        help_text="Light mode: Lighter text color option",
    )
    secondary_bg_light = models.CharField(
        max_length=7,
        default="#e9ecef",
        validators=[validate_hex_color],
        verbose_name="Secondary background (light)",
        help_text="Light mode: For dividers and disabled states",
    )
    secondary_color_dark = models.CharField(
        max_length=7,
        default="#dee2e6",
        validators=[validate_hex_color],
        verbose_name="Secondary text (dark)",
        help_text="Dark mode: Lighter text color option",
    )
    secondary_bg_dark = models.CharField(
        max_length=7,
        default="#343a40",
        validators=[validate_hex_color],
        verbose_name="Secondary background (dark)",
        help_text="Dark mode: For dividers and disabled states",
    )
    # ==== TERTIARY COLORS ====
    # Use color for even lighter text. Use bg for hover states, accents, and wells
    tertiary_color_light = models.CharField(
        max_length=7,
        default="#6c757d",
        validators=[validate_hex_color],
        verbose_name="Tertiary text (light)",
        help_text="Light mode: Even lighter text color option",
    )
    tertiary_bg_light = models.CharField(
        max_length=7,
        default="#f8f9fa",
        validators=[validate_hex_color],
        verbose_name="Tertiary background (light)",
        help_text="Light mode: For hover states, accents, and wells",
    )
    tertiary_color_dark = models.CharField(
        max_length=7,
        default="#dee2e6",
        validators=[validate_hex_color],
        verbose_name="Tertiary text (dark)",
        help_text="Dark mode: Even lighter text color option",
    )
    tertiary_bg_dark = models.CharField(
        max_length=7,
        default="#2b3035",
        validators=[validate_hex_color],
        verbose_name="Tertiary background (dark)",
        help_text="Dark mode: For hover states, accents, and wells",
    )
    # ==== EMPHASIS COLOR ====
    # For higher contrast text. Not applicable for backgrounds
    emphasis_color_light = models.CharField(
        max_length=7,
        default="#000000",
        validators=[validate_hex_color],
        verbose_name="Emphasis color (light)",
        help_text="Light mode: For higher contrast text",
    )
    emphasis_color_dark = models.CharField(
        max_length=7,
        default="#ffffff",
        validators=[validate_hex_color],
        verbose_name="Emphasis color (dark)",
        help_text="Dark mode: For higher contrast text",
    )
    # ==== BORDER COLOR ====
    # For component borders, dividers, and rules
    border_color_light = models.CharField(
        max_length=7,
        default="#dee2e6",
        validators=[validate_hex_color],
        verbose_name="Border color (light)",
        help_text="Light mode: For component borders, dividers, and rules",
    )
    border_color_dark = models.CharField(
        max_length=7,
        default="#495057",
        validators=[validate_hex_color],
        verbose_name="Border color (dark)",
        help_text="Dark mode: For component borders, dividers, and rules",
    )
    # ==== PRIMARY THEME COLOR ====
    # Main theme color, used for hyperlinks, focus styles, and active states
    primary_color = models.CharField(
        max_length=7,
        default="#0d6efd",
        validators=[validate_hex_color],
        verbose_name="Primary",
        help_text="Main theme color for hyperlinks, focus styles, and active states",
    )
    primary_bg_subtle_light = models.CharField(
        max_length=7,
        default="#cfe2ff",
        validators=[validate_hex_color],
        verbose_name="Primary subtle background (light)",
        help_text="Light mode: Subtle primary background",
    )
    primary_border_subtle_light = models.CharField(
        max_length=7,
        default="#9ec5fe",
        validators=[validate_hex_color],
        verbose_name="Primary subtle border (light)",
        help_text="Light mode: Subtle primary border",
    )
    primary_text_emphasis_light = models.CharField(
        max_length=7,
        default="#052c65",
        validators=[validate_hex_color],
        verbose_name="Primary text emphasis (light)",
        help_text="Light mode: Emphasized primary text",
    )
    primary_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#031633",
        validators=[validate_hex_color],
        verbose_name="Primary subtle background (dark)",
        help_text="Dark mode: Subtle primary background",
    )
    primary_border_subtle_dark = models.CharField(
        max_length=7,
        default="#084298",
        validators=[validate_hex_color],
        verbose_name="Primary subtle border (dark)",
        help_text="Dark mode: Subtle primary border",
    )
    primary_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#6ea8fe",
        validators=[validate_hex_color],
        verbose_name="Primary text emphasis (dark)",
        help_text="Dark mode: Emphasized primary text",
    )
    # ==== SUCCESS THEME COLOR ====
    # Theme color used for positive or successful actions and information
    success_color = models.CharField(
        max_length=7,
        default="#198754",
        validators=[validate_hex_color],
        verbose_name="Success",
        help_text="Theme color for positive or successful actions",
    )
    success_bg_subtle_light = models.CharField(
        max_length=7,
        default="#d1e7dd",
        validators=[validate_hex_color],
        verbose_name="Success subtle background (light)",
        help_text="Light mode: Subtle success background",
    )
    success_border_subtle_light = models.CharField(
        max_length=7,
        default="#a3cfbb",
        validators=[validate_hex_color],
        verbose_name="Success subtle border (light)",
        help_text="Light mode: Subtle success border",
    )
    success_text_emphasis_light = models.CharField(
        max_length=7,
        default="#0a3622",
        validators=[validate_hex_color],
        verbose_name="Success text emphasis (light)",
        help_text="Light mode: Emphasized success text",
    )
    success_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#051b11",
        validators=[validate_hex_color],
        verbose_name="Success subtle background (dark)",
        help_text="Dark mode: Subtle success background",
    )
    success_border_subtle_dark = models.CharField(
        max_length=7,
        default="#0f5132",
        validators=[validate_hex_color],
        verbose_name="Success subtle border (dark)",
        help_text="Dark mode: Subtle success border",
    )
    success_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#75b798",
        validators=[validate_hex_color],
        verbose_name="Success text emphasis (dark)",
        help_text="Dark mode: Emphasized success text",
    )
    # ==== DANGER THEME COLOR ====
    # Theme color used for errors and dangerous actions
    danger_color = models.CharField(
        max_length=7,
        default="#dc3545",
        validators=[validate_hex_color],
        verbose_name="Danger",
        help_text="Theme color for errors and dangerous actions",
    )
    danger_bg_subtle_light = models.CharField(
        max_length=7,
        default="#f8d7da",
        validators=[validate_hex_color],
        verbose_name="Danger subtle background (light)",
        help_text="Light mode: Subtle danger background",
    )
    danger_border_subtle_light = models.CharField(
        max_length=7,
        default="#f1aeb5",
        validators=[validate_hex_color],
        verbose_name="Danger subtle border (light)",
        help_text="Light mode: Subtle danger border",
    )
    danger_text_emphasis_light = models.CharField(
        max_length=7,
        default="#58151c",
        validators=[validate_hex_color],
        verbose_name="Danger text emphasis (light)",
        help_text="Light mode: Emphasized danger text",
    )
    danger_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#2c0b0e",
        validators=[validate_hex_color],
        verbose_name="Danger subtle background (dark)",
        help_text="Dark mode: Subtle danger background",
    )
    danger_border_subtle_dark = models.CharField(
        max_length=7,
        default="#842029",
        validators=[validate_hex_color],
        verbose_name="Danger subtle border (dark)",
        help_text="Dark mode: Subtle danger border",
    )
    danger_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#ea868f",
        validators=[validate_hex_color],
        verbose_name="Danger text emphasis (dark)",
        help_text="Dark mode: Emphasized danger text",
    )
    # ==== WARNING THEME COLOR ====
    # Theme color used for non-destructive warning messages
    warning_color = models.CharField(
        max_length=7,
        default="#ffc107",
        validators=[validate_hex_color],
        verbose_name="Warning",
        help_text="Theme color for non-destructive warning messages",
    )
    warning_bg_subtle_light = models.CharField(
        max_length=7,
        default="#fff3cd",
        validators=[validate_hex_color],
        verbose_name="Warning subtle background (light)",
        help_text="Light mode: Subtle warning background",
    )
    warning_border_subtle_light = models.CharField(
        max_length=7,
        default="#ffe69c",
        validators=[validate_hex_color],
        verbose_name="Warning subtle border (light)",
        help_text="Light mode: Subtle warning border",
    )
    warning_text_emphasis_light = models.CharField(
        max_length=7,
        default="#664d03",
        validators=[validate_hex_color],
        verbose_name="Warning text emphasis (light)",
        help_text="Light mode: Emphasized warning text",
    )
    warning_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#332701",
        validators=[validate_hex_color],
        verbose_name="Warning subtle background (dark)",
        help_text="Dark mode: Subtle warning background",
    )
    warning_border_subtle_dark = models.CharField(
        max_length=7,
        default="#997404",
        validators=[validate_hex_color],
        verbose_name="Warning subtle border (dark)",
        help_text="Dark mode: Subtle warning border",
    )
    warning_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#ffda6a",
        validators=[validate_hex_color],
        verbose_name="Warning text emphasis (dark)",
        help_text="Dark mode: Emphasized warning text",
    )
    # ==== INFO THEME COLOR ====
    # Theme color used for neutral and informative content
    info_color = models.CharField(
        max_length=7,
        default="#0dcaf0",
        validators=[validate_hex_color],
        verbose_name="Info",
        help_text="Theme color for neutral and informative content",
    )
    info_bg_subtle_light = models.CharField(
        max_length=7,
        default="#cff4fc",
        validators=[validate_hex_color],
        verbose_name="Info subtle background (light)",
        help_text="Light mode: Subtle info background",
    )
    info_border_subtle_light = models.CharField(
        max_length=7,
        default="#9eeaf9",
        validators=[validate_hex_color],
        verbose_name="Info subtle border (light)",
        help_text="Light mode: Subtle info border",
    )
    info_text_emphasis_light = models.CharField(
        max_length=7,
        default="#055160",
        validators=[validate_hex_color],
        verbose_name="Info text emphasis (light)",
        help_text="Light mode: Emphasized info text",
    )
    info_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#032830",
        validators=[validate_hex_color],
        verbose_name="Info subtle background (dark)",
        help_text="Dark mode: Subtle info background",
    )
    info_border_subtle_dark = models.CharField(
        max_length=7,
        default="#087990",
        validators=[validate_hex_color],
        verbose_name="Info subtle border (dark)",
        help_text="Dark mode: Subtle info border",
    )
    info_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#6edff6",
        validators=[validate_hex_color],
        verbose_name="Info text emphasis (dark)",
        help_text="Dark mode: Emphasized info text",
    )
    # ==== LIGHT THEME COLOR ====
    # Additional theme option for less contrasting colors
    light_color = models.CharField(
        max_length=7,
        default="#f8f9fa",
        validators=[validate_hex_color],
        verbose_name="Light",
        help_text="Additional theme option for less contrasting colors",
    )
    light_bg_subtle_light = models.CharField(
        max_length=7,
        default="#fcfcfd",
        validators=[validate_hex_color],
        verbose_name="Light subtle background (light)",
        help_text="Light mode: Subtle light background",
    )
    light_border_subtle_light = models.CharField(
        max_length=7,
        default="#e9ecef",
        validators=[validate_hex_color],
        verbose_name="Light subtle border (light)",
        help_text="Light mode: Subtle light border",
    )
    light_text_emphasis_light = models.CharField(
        max_length=7,
        default="#495057",
        validators=[validate_hex_color],
        verbose_name="Light text emphasis (light)",
        help_text="Light mode: Emphasized light text",
    )
    light_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#343a40",
        validators=[validate_hex_color],
        verbose_name="Light subtle background (dark)",
        help_text="Dark mode: Subtle light background",
    )
    light_border_subtle_dark = models.CharField(
        max_length=7,
        default="#495057",
        validators=[validate_hex_color],
        verbose_name="Light subtle border (dark)",
        help_text="Dark mode: Subtle light border",
    )
    light_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#f8f9fa",
        validators=[validate_hex_color],
        verbose_name="Light text emphasis (dark)",
        help_text="Dark mode: Emphasized light text",
    )
    # ==== DARK THEME COLOR ====
    # Additional theme option for higher contrasting colors
    dark_color = models.CharField(
        max_length=7,
        default="#212529",
        validators=[validate_hex_color],
        verbose_name="Dark",
        help_text="Additional theme option for higher contrasting colors",
    )
    dark_bg_subtle_light = models.CharField(
        max_length=7,
        default="#ced4da",
        validators=[validate_hex_color],
        verbose_name="Dark subtle background (light)",
        help_text="Light mode: Subtle dark background",
    )
    dark_border_subtle_light = models.CharField(
        max_length=7,
        default="#adb5bd",
        validators=[validate_hex_color],
        verbose_name="Dark subtle border (light)",
        help_text="Light mode: Subtle dark border",
    )
    dark_text_emphasis_light = models.CharField(
        max_length=7,
        default="#495057",
        validators=[validate_hex_color],
        verbose_name="Dark text emphasis (light)",
        help_text="Light mode: Emphasized dark text",
    )
    dark_bg_subtle_dark = models.CharField(
        max_length=7,
        default="#1a1d20",
        validators=[validate_hex_color],
        verbose_name="Dark subtle background (dark)",
        help_text="Dark mode: Subtle dark background",
    )
    dark_border_subtle_dark = models.CharField(
        max_length=7,
        default="#343a40",
        validators=[validate_hex_color],
        verbose_name="Dark subtle border (dark)",
        help_text="Dark mode: Subtle dark border",
    )
    dark_text_emphasis_dark = models.CharField(
        max_length=7,
        default="#dee2e6",
        validators=[validate_hex_color],
        verbose_name="Dark text emphasis (dark)",
        help_text="Dark mode: Emphasized dark text",
    )
    # ==== LINK COLORS ====
    link_color_light = models.CharField(
        max_length=7,
        default="#0d6efd",
        validators=[validate_hex_color],
        verbose_name="Link color (light)",
        help_text="Light mode: Default hyperlink color",
    )
    link_hover_color_light = models.CharField(
        max_length=7,
        default="#0a58ca",
        validators=[validate_hex_color],
        verbose_name="Link hover color (light)",
        help_text="Light mode: Hyperlink hover color",
    )
    link_color_dark = models.CharField(
        max_length=7,
        default="#6ea8fe",
        validators=[validate_hex_color],
        verbose_name="Link color (dark)",
        help_text="Dark mode: Default hyperlink color",
    )
    link_hover_color_dark = models.CharField(
        max_length=7,
        default="#8bb9fe",
        validators=[validate_hex_color],
        verbose_name="Link hover color (dark)",
        help_text="Dark mode: Hyperlink hover color",
    )
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("body_color_light"),
                FieldPanel("body_bg_light"),
                FieldPanel("body_color_dark"),
                FieldPanel("body_bg_dark"),
            ],
            "Body",
            help_text=(
                "Default foreground (color) and background, including components."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("secondary_color_light"),
                FieldPanel("secondary_bg_light"),
                FieldPanel("secondary_color_dark"),
                FieldPanel("secondary_bg_dark"),
            ],
            "Secondary",
            help_text=(
                "Use color for lighter text. Use bg for dividers and disabled states."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("tertiary_color_light"),
                FieldPanel("tertiary_bg_light"),
                FieldPanel("tertiary_color_dark"),
                FieldPanel("tertiary_bg_dark"),
            ],
            "Tertiary",
            help_text=(
                "Use color for even lighter text. "
                "Use bg for hover states, accents, and wells."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("emphasis_color_light"),
                FieldPanel("emphasis_color_dark"),
            ],
            "Emphasis",
            help_text="For higher contrast text. Not applicable for backgrounds.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("border_color_light"),
                FieldPanel("border_color_dark"),
            ],
            "Border",
            help_text="For component borders, dividers, and rules.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("primary_color"),
                FieldPanel("primary_bg_subtle_light"),
                FieldPanel("primary_border_subtle_light"),
                FieldPanel("primary_text_emphasis_light"),
                FieldPanel("primary_bg_subtle_dark"),
                FieldPanel("primary_border_subtle_dark"),
                FieldPanel("primary_text_emphasis_dark"),
            ],
            "Primary",
            help_text=(
                "Main theme color, used for hyperlinks, focus styles, "
                "and component and form active states."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("success_color"),
                FieldPanel("success_bg_subtle_light"),
                FieldPanel("success_border_subtle_light"),
                FieldPanel("success_text_emphasis_light"),
                FieldPanel("success_bg_subtle_dark"),
                FieldPanel("success_border_subtle_dark"),
                FieldPanel("success_text_emphasis_dark"),
            ],
            "Success",
            help_text=(
                "Theme color used for positive or successful actions and information."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("danger_color"),
                FieldPanel("danger_bg_subtle_light"),
                FieldPanel("danger_border_subtle_light"),
                FieldPanel("danger_text_emphasis_light"),
                FieldPanel("danger_bg_subtle_dark"),
                FieldPanel("danger_border_subtle_dark"),
                FieldPanel("danger_text_emphasis_dark"),
            ],
            "Danger",
            help_text="Theme color used for errors and dangerous actions.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("warning_color"),
                FieldPanel("warning_bg_subtle_light"),
                FieldPanel("warning_border_subtle_light"),
                FieldPanel("warning_text_emphasis_light"),
                FieldPanel("warning_bg_subtle_dark"),
                FieldPanel("warning_border_subtle_dark"),
                FieldPanel("warning_text_emphasis_dark"),
            ],
            "Warning",
            help_text="Theme color used for non-destructive warning messages.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("info_color"),
                FieldPanel("info_bg_subtle_light"),
                FieldPanel("info_border_subtle_light"),
                FieldPanel("info_text_emphasis_light"),
                FieldPanel("info_bg_subtle_dark"),
                FieldPanel("info_border_subtle_dark"),
                FieldPanel("info_text_emphasis_dark"),
            ],
            "Info",
            help_text="Theme color used for neutral and informative content.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("light_color"),
                FieldPanel("light_bg_subtle_light"),
                FieldPanel("light_border_subtle_light"),
                FieldPanel("light_text_emphasis_light"),
                FieldPanel("light_bg_subtle_dark"),
                FieldPanel("light_border_subtle_dark"),
                FieldPanel("light_text_emphasis_dark"),
            ],
            "Light",
            help_text="Additional theme option for less contrasting colors.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("dark_color"),
                FieldPanel("dark_bg_subtle_light"),
                FieldPanel("dark_border_subtle_light"),
                FieldPanel("dark_text_emphasis_light"),
                FieldPanel("dark_bg_subtle_dark"),
                FieldPanel("dark_border_subtle_dark"),
                FieldPanel("dark_text_emphasis_dark"),
            ],
            "Dark",
            help_text="Additional theme option for higher contrasting colors.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("link_color_light"),
                FieldPanel("link_hover_color_light"),
                FieldPanel("link_color_dark"),
                FieldPanel("link_hover_color_dark"),
            ],
            "Links",
            help_text="Colors for hyperlinks in light and dark modes.",
        ),
    ]

    def save(self, *args, **kwargs):
        """Increment CSS version on save to invalidate cached CSS."""
        self.css_version += 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Theme Settings"


class AMSDocument(AbstractDocument):
    """Custom Document model that stores to private storage."""

    file = models.FileField(
        storage=storages["private"],
        upload_to="documents",
        verbose_name=_("file"),
    )

    admin_form_fields = Document.admin_form_fields
