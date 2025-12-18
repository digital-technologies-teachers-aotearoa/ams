from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import FieldRowPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.models import register_setting

from ams.cms.validators import validate_hex_color


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
                FieldRowPanel(
                    [
                        FieldPanel("body_color_light"),
                        FieldPanel("body_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("body_bg_light"),
                        FieldPanel("body_bg_dark"),
                    ],
                ),
            ],
            "Body",
            help_text=(
                "Default foreground (color) and background, including components."
            ),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("secondary_color_light"),
                        FieldPanel("secondary_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("secondary_bg_light"),
                        FieldPanel("secondary_bg_dark"),
                    ],
                ),
            ],
            "Secondary",
            help_text=(
                "Use color for lighter text. Use bg for dividers and disabled states."
            ),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("tertiary_color_light"),
                        FieldPanel("tertiary_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("tertiary_bg_light"),
                        FieldPanel("tertiary_bg_dark"),
                    ],
                ),
            ],
            "Tertiary",
            help_text=(
                "Use color for even lighter text. "
                "Use bg for hover states, accents, and wells."
            ),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("emphasis_color_light"),
                        FieldPanel("emphasis_color_dark"),
                    ],
                ),
            ],
            "Emphasis",
            help_text="For higher contrast text. Not applicable for backgrounds.",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("border_color_light"),
                        FieldPanel("border_color_dark"),
                    ],
                ),
            ],
            "Border",
            help_text="For component borders, dividers, and rules.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("primary_color"),
                FieldRowPanel(
                    [
                        FieldPanel("primary_bg_subtle_light"),
                        FieldPanel("primary_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("primary_border_subtle_light"),
                        FieldPanel("primary_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("primary_text_emphasis_light"),
                        FieldPanel("primary_text_emphasis_dark"),
                    ],
                ),
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
                FieldRowPanel(
                    [
                        FieldPanel("success_bg_subtle_light"),
                        FieldPanel("success_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("success_border_subtle_light"),
                        FieldPanel("success_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("success_text_emphasis_light"),
                        FieldPanel("success_text_emphasis_dark"),
                    ],
                ),
            ],
            "Success",
            help_text=(
                "Theme color used for positive or successful actions and information."
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("danger_color"),
                FieldRowPanel(
                    [
                        FieldPanel("danger_bg_subtle_light"),
                        FieldPanel("danger_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("danger_border_subtle_light"),
                        FieldPanel("danger_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("danger_text_emphasis_light"),
                        FieldPanel("danger_text_emphasis_dark"),
                    ],
                ),
            ],
            "Danger",
            help_text="Theme color used for errors and dangerous actions.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("warning_color"),
                FieldRowPanel(
                    [
                        FieldPanel("warning_bg_subtle_light"),
                        FieldPanel("warning_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("warning_border_subtle_light"),
                        FieldPanel("warning_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("warning_text_emphasis_light"),
                        FieldPanel("warning_text_emphasis_dark"),
                    ],
                ),
            ],
            "Warning",
            help_text="Theme color used for non-destructive warning messages.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("info_color"),
                FieldRowPanel(
                    [
                        FieldPanel("info_bg_subtle_light"),
                        FieldPanel("info_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("info_border_subtle_light"),
                        FieldPanel("info_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("info_text_emphasis_light"),
                        FieldPanel("info_text_emphasis_dark"),
                    ],
                ),
            ],
            "Info",
            help_text="Theme color used for neutral and informative content.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("light_color"),
                FieldRowPanel(
                    [
                        FieldPanel("light_bg_subtle_light"),
                        FieldPanel("light_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("light_border_subtle_light"),
                        FieldPanel("light_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("light_text_emphasis_light"),
                        FieldPanel("light_text_emphasis_dark"),
                    ],
                ),
            ],
            "Light",
            help_text="Additional theme option for less contrasting colors.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("dark_color"),
                FieldRowPanel(
                    [
                        FieldPanel("dark_bg_subtle_light"),
                        FieldPanel("dark_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("dark_border_subtle_light"),
                        FieldPanel("dark_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("dark_text_emphasis_light"),
                        FieldPanel("dark_text_emphasis_dark"),
                    ],
                ),
            ],
            "Dark",
            help_text="Additional theme option for higher contrasting colors.",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("link_color_light"),
                        FieldPanel("link_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        FieldPanel("link_hover_color_light"),
                        FieldPanel("link_hover_color_dark"),
                    ],
                ),
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
