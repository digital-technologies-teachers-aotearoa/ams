from django.db import models
from wagtail.admin.panels import FieldRowPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.models import register_setting
from wagtail_color_panel.edit_handlers import NativeColorPanel
from wagtail_color_panel.fields import ColorField


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
    body_color_light = ColorField(
        default="#212529",
        verbose_name="Body text color (light)",
        help_text="Light mode: Default foreground color for text",
    )
    body_bg_light = ColorField(
        default="#ffffff",
        verbose_name="Body background (light)",
        help_text="Light mode: Default background for body",
    )
    body_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Body text color (dark)",
        help_text="Dark mode: Default foreground color for text",
    )
    body_bg_dark = ColorField(
        default="#212529",
        verbose_name="Body background (dark)",
        help_text="Dark mode: Default background for body",
    )
    # ==== SECONDARY COLORS ====
    # Use color for lighter text. Use bg for dividers and disabled states
    secondary_color_light = ColorField(
        default="#6c757d",
        verbose_name="Secondary text (light)",
        help_text="Light mode: Lighter text color option",
    )
    secondary_bg_light = ColorField(
        default="#e9ecef",
        verbose_name="Secondary background (light)",
        help_text="Light mode: For dividers and disabled states",
    )
    secondary_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Secondary text (dark)",
        help_text="Dark mode: Lighter text color option",
    )
    secondary_bg_dark = ColorField(
        default="#343a40",
        verbose_name="Secondary background (dark)",
        help_text="Dark mode: For dividers and disabled states",
    )
    # ==== TERTIARY COLORS ====
    # Use color for even lighter text. Use bg for hover states, accents, and wells
    tertiary_color_light = ColorField(
        default="#6c757d",
        verbose_name="Tertiary text (light)",
        help_text="Light mode: Even lighter text color option",
    )
    tertiary_bg_light = ColorField(
        default="#f8f9fa",
        verbose_name="Tertiary background (light)",
        help_text="Light mode: For hover states, accents, and wells",
    )
    tertiary_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Tertiary text (dark)",
        help_text="Dark mode: Even lighter text color option",
    )
    tertiary_bg_dark = ColorField(
        default="#2b3035",
        verbose_name="Tertiary background (dark)",
        help_text="Dark mode: For hover states, accents, and wells",
    )
    # ==== EMPHASIS COLOR ====
    # For higher contrast text. Not applicable for backgrounds
    emphasis_color_light = ColorField(
        default="#000000",
        verbose_name="Emphasis color (light)",
        help_text="Light mode: For higher contrast text",
    )
    emphasis_color_dark = ColorField(
        default="#ffffff",
        verbose_name="Emphasis color (dark)",
        help_text="Dark mode: For higher contrast text",
    )
    # ==== BORDER COLOR ====
    # For component borders, dividers, and rules
    border_color_light = ColorField(
        default="#dee2e6",
        verbose_name="Border color (light)",
        help_text="Light mode: For component borders, dividers, and rules",
    )
    border_color_dark = ColorField(
        default="#495057",
        verbose_name="Border color (dark)",
        help_text="Dark mode: For component borders, dividers, and rules",
    )
    # ==== PRIMARY THEME COLOR ====
    # Main theme color, used for hyperlinks, focus styles, and active states
    primary_color = ColorField(
        default="#0d6efd",
        verbose_name="Primary",
        help_text="Main theme color for hyperlinks, focus styles, and active states",
    )
    primary_bg_subtle_light = ColorField(
        default="#cfe2ff",
        verbose_name="Primary subtle background (light)",
        help_text="Light mode: Subtle primary background",
    )
    primary_border_subtle_light = ColorField(
        default="#9ec5fe",
        verbose_name="Primary subtle border (light)",
        help_text="Light mode: Subtle primary border",
    )
    primary_text_emphasis_light = ColorField(
        default="#052c65",
        verbose_name="Primary text emphasis (light)",
        help_text="Light mode: Emphasized primary text",
    )
    primary_bg_subtle_dark = ColorField(
        default="#031633",
        verbose_name="Primary subtle background (dark)",
        help_text="Dark mode: Subtle primary background",
    )
    primary_border_subtle_dark = ColorField(
        default="#084298",
        verbose_name="Primary subtle border (dark)",
        help_text="Dark mode: Subtle primary border",
    )
    primary_text_emphasis_dark = ColorField(
        default="#6ea8fe",
        verbose_name="Primary text emphasis (dark)",
        help_text="Dark mode: Emphasized primary text",
    )
    # ==== SUCCESS THEME COLOR ====
    # Theme color used for positive or successful actions and information
    success_color = ColorField(
        default="#198754",
        verbose_name="Success",
        help_text="Theme color for positive or successful actions",
    )
    success_bg_subtle_light = ColorField(
        default="#d1e7dd",
        verbose_name="Success subtle background (light)",
        help_text="Light mode: Subtle success background",
    )
    success_border_subtle_light = ColorField(
        default="#a3cfbb",
        verbose_name="Success subtle border (light)",
        help_text="Light mode: Subtle success border",
    )
    success_text_emphasis_light = ColorField(
        default="#0a3622",
        verbose_name="Success text emphasis (light)",
        help_text="Light mode: Emphasized success text",
    )
    success_bg_subtle_dark = ColorField(
        default="#051b11",
        verbose_name="Success subtle background (dark)",
        help_text="Dark mode: Subtle success background",
    )
    success_border_subtle_dark = ColorField(
        default="#0f5132",
        verbose_name="Success subtle border (dark)",
        help_text="Dark mode: Subtle success border",
    )
    success_text_emphasis_dark = ColorField(
        default="#75b798",
        verbose_name="Success text emphasis (dark)",
        help_text="Dark mode: Emphasized success text",
    )
    # ==== DANGER THEME COLOR ====
    # Theme color used for errors and dangerous actions
    danger_color = ColorField(
        default="#dc3545",
        verbose_name="Danger",
        help_text="Theme color for errors and dangerous actions",
    )
    danger_bg_subtle_light = ColorField(
        default="#f8d7da",
        verbose_name="Danger subtle background (light)",
        help_text="Light mode: Subtle danger background",
    )
    danger_border_subtle_light = ColorField(
        default="#f1aeb5",
        verbose_name="Danger subtle border (light)",
        help_text="Light mode: Subtle danger border",
    )
    danger_text_emphasis_light = ColorField(
        default="#58151c",
        verbose_name="Danger text emphasis (light)",
        help_text="Light mode: Emphasized danger text",
    )
    danger_bg_subtle_dark = ColorField(
        default="#2c0b0e",
        verbose_name="Danger subtle background (dark)",
        help_text="Dark mode: Subtle danger background",
    )
    danger_border_subtle_dark = ColorField(
        default="#842029",
        verbose_name="Danger subtle border (dark)",
        help_text="Dark mode: Subtle danger border",
    )
    danger_text_emphasis_dark = ColorField(
        default="#ea868f",
        verbose_name="Danger text emphasis (dark)",
        help_text="Dark mode: Emphasized danger text",
    )
    # ==== WARNING THEME COLOR ====
    # Theme color used for non-destructive warning messages
    warning_color = ColorField(
        default="#ffc107",
        verbose_name="Warning",
        help_text="Theme color for non-destructive warning messages",
    )
    warning_bg_subtle_light = ColorField(
        default="#fff3cd",
        verbose_name="Warning subtle background (light)",
        help_text="Light mode: Subtle warning background",
    )
    warning_border_subtle_light = ColorField(
        default="#ffe69c",
        verbose_name="Warning subtle border (light)",
        help_text="Light mode: Subtle warning border",
    )
    warning_text_emphasis_light = ColorField(
        default="#664d03",
        verbose_name="Warning text emphasis (light)",
        help_text="Light mode: Emphasized warning text",
    )
    warning_bg_subtle_dark = ColorField(
        default="#332701",
        verbose_name="Warning subtle background (dark)",
        help_text="Dark mode: Subtle warning background",
    )
    warning_border_subtle_dark = ColorField(
        default="#997404",
        verbose_name="Warning subtle border (dark)",
        help_text="Dark mode: Subtle warning border",
    )
    warning_text_emphasis_dark = ColorField(
        default="#ffda6a",
        verbose_name="Warning text emphasis (dark)",
        help_text="Dark mode: Emphasized warning text",
    )
    # ==== INFO THEME COLOR ====
    # Theme color used for neutral and informative content
    info_color = ColorField(
        default="#0dcaf0",
        verbose_name="Info",
        help_text="Theme color for neutral and informative content",
    )
    info_bg_subtle_light = ColorField(
        default="#cff4fc",
        verbose_name="Info subtle background (light)",
        help_text="Light mode: Subtle info background",
    )
    info_border_subtle_light = ColorField(
        default="#9eeaf9",
        verbose_name="Info subtle border (light)",
        help_text="Light mode: Subtle info border",
    )
    info_text_emphasis_light = ColorField(
        default="#055160",
        verbose_name="Info text emphasis (light)",
        help_text="Light mode: Emphasized info text",
    )
    info_bg_subtle_dark = ColorField(
        default="#032830",
        verbose_name="Info subtle background (dark)",
        help_text="Dark mode: Subtle info background",
    )
    info_border_subtle_dark = ColorField(
        default="#087990",
        verbose_name="Info subtle border (dark)",
        help_text="Dark mode: Subtle info border",
    )
    info_text_emphasis_dark = ColorField(
        default="#6edff6",
        verbose_name="Info text emphasis (dark)",
        help_text="Dark mode: Emphasized info text",
    )
    # ==== LIGHT THEME COLOR ====
    # Additional theme option for less contrasting colors
    light_color = ColorField(
        default="#f8f9fa",
        verbose_name="Light",
        help_text="Additional theme option for less contrasting colors",
    )
    light_bg_subtle_light = ColorField(
        default="#fcfcfd",
        verbose_name="Light subtle background (light)",
        help_text="Light mode: Subtle light background",
    )
    light_border_subtle_light = ColorField(
        default="#e9ecef",
        verbose_name="Light subtle border (light)",
        help_text="Light mode: Subtle light border",
    )
    light_text_emphasis_light = ColorField(
        default="#495057",
        verbose_name="Light text emphasis (light)",
        help_text="Light mode: Emphasized light text",
    )
    light_bg_subtle_dark = ColorField(
        default="#343a40",
        verbose_name="Light subtle background (dark)",
        help_text="Dark mode: Subtle light background",
    )
    light_border_subtle_dark = ColorField(
        default="#495057",
        verbose_name="Light subtle border (dark)",
        help_text="Dark mode: Subtle light border",
    )
    light_text_emphasis_dark = ColorField(
        default="#f8f9fa",
        verbose_name="Light text emphasis (dark)",
        help_text="Dark mode: Emphasized light text",
    )
    # ==== DARK THEME COLOR ====
    # Additional theme option for higher contrasting colors
    dark_color = ColorField(
        default="#212529",
        verbose_name="Dark",
        help_text="Additional theme option for higher contrasting colors",
    )
    dark_bg_subtle_light = ColorField(
        default="#ced4da",
        verbose_name="Dark subtle background (light)",
        help_text="Light mode: Subtle dark background",
    )
    dark_border_subtle_light = ColorField(
        default="#adb5bd",
        verbose_name="Dark subtle border (light)",
        help_text="Light mode: Subtle dark border",
    )
    dark_text_emphasis_light = ColorField(
        default="#495057",
        verbose_name="Dark text emphasis (light)",
        help_text="Light mode: Emphasized dark text",
    )
    dark_bg_subtle_dark = ColorField(
        default="#1a1d20",
        verbose_name="Dark subtle background (dark)",
        help_text="Dark mode: Subtle dark background",
    )
    dark_border_subtle_dark = ColorField(
        default="#343a40",
        verbose_name="Dark subtle border (dark)",
        help_text="Dark mode: Subtle dark border",
    )
    dark_text_emphasis_dark = ColorField(
        default="#dee2e6",
        verbose_name="Dark text emphasis (dark)",
        help_text="Dark mode: Emphasized dark text",
    )
    # ==== LINK COLORS ====
    link_color_light = ColorField(
        default="#0d6efd",
        verbose_name="Link color (light)",
        help_text="Light mode: Default hyperlink color",
    )
    link_hover_color_light = ColorField(
        default="#0a58ca",
        verbose_name="Link hover color (light)",
        help_text="Light mode: Hyperlink hover color",
    )
    link_color_dark = ColorField(
        default="#6ea8fe",
        verbose_name="Link color (dark)",
        help_text="Dark mode: Default hyperlink color",
    )
    link_hover_color_dark = ColorField(
        default="#8bb9fe",
        verbose_name="Link hover color (dark)",
        help_text="Dark mode: Hyperlink hover color",
    )
    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        NativeColorPanel("body_color_light"),
                        NativeColorPanel("body_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("body_bg_light"),
                        NativeColorPanel("body_bg_dark"),
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
                        NativeColorPanel("secondary_color_light"),
                        NativeColorPanel("secondary_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("secondary_bg_light"),
                        NativeColorPanel("secondary_bg_dark"),
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
                        NativeColorPanel("tertiary_color_light"),
                        NativeColorPanel("tertiary_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("tertiary_bg_light"),
                        NativeColorPanel("tertiary_bg_dark"),
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
                        NativeColorPanel("emphasis_color_light"),
                        NativeColorPanel("emphasis_color_dark"),
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
                        NativeColorPanel("border_color_light"),
                        NativeColorPanel("border_color_dark"),
                    ],
                ),
            ],
            "Border",
            help_text="For component borders, dividers, and rules.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("primary_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("primary_bg_subtle_light"),
                        NativeColorPanel("primary_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("primary_border_subtle_light"),
                        NativeColorPanel("primary_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("primary_text_emphasis_light"),
                        NativeColorPanel("primary_text_emphasis_dark"),
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
                NativeColorPanel("success_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("success_bg_subtle_light"),
                        NativeColorPanel("success_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("success_border_subtle_light"),
                        NativeColorPanel("success_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("success_text_emphasis_light"),
                        NativeColorPanel("success_text_emphasis_dark"),
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
                NativeColorPanel("danger_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("danger_bg_subtle_light"),
                        NativeColorPanel("danger_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("danger_border_subtle_light"),
                        NativeColorPanel("danger_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("danger_text_emphasis_light"),
                        NativeColorPanel("danger_text_emphasis_dark"),
                    ],
                ),
            ],
            "Danger",
            help_text="Theme color used for errors and dangerous actions.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("warning_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("warning_bg_subtle_light"),
                        NativeColorPanel("warning_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("warning_border_subtle_light"),
                        NativeColorPanel("warning_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("warning_text_emphasis_light"),
                        NativeColorPanel("warning_text_emphasis_dark"),
                    ],
                ),
            ],
            "Warning",
            help_text="Theme color used for non-destructive warning messages.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("info_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("info_bg_subtle_light"),
                        NativeColorPanel("info_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("info_border_subtle_light"),
                        NativeColorPanel("info_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("info_text_emphasis_light"),
                        NativeColorPanel("info_text_emphasis_dark"),
                    ],
                ),
            ],
            "Info",
            help_text="Theme color used for neutral and informative content.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("light_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("light_bg_subtle_light"),
                        NativeColorPanel("light_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("light_border_subtle_light"),
                        NativeColorPanel("light_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("light_text_emphasis_light"),
                        NativeColorPanel("light_text_emphasis_dark"),
                    ],
                ),
            ],
            "Light",
            help_text="Additional theme option for less contrasting colors.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("dark_color"),
                FieldRowPanel(
                    [
                        NativeColorPanel("dark_bg_subtle_light"),
                        NativeColorPanel("dark_bg_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("dark_border_subtle_light"),
                        NativeColorPanel("dark_border_subtle_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("dark_text_emphasis_light"),
                        NativeColorPanel("dark_text_emphasis_dark"),
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
                        NativeColorPanel("link_color_light"),
                        NativeColorPanel("link_color_dark"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("link_hover_color_light"),
                        NativeColorPanel("link_hover_color_dark"),
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
