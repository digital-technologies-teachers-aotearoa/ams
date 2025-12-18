from django.db import models
from django.utils.safestring import mark_safe
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
        help_text=mark_safe(
            "Light mode: Default foreground color for text.<br>"
            "Default: <code>#212529</code>",
        ),
    )
    body_bg_light = ColorField(
        default="#ffffff",
        verbose_name="Body background (light)",
        help_text=mark_safe(
            "Light mode: Default background for body.<br>Default: <code>#ffffff</code>",
        ),
    )
    body_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Body text color (dark)",
        help_text=mark_safe(
            "Dark mode: Default foreground color for text.<br>"
            "Default: <code>#dee2e6</code>",
        ),
    )
    body_bg_dark = ColorField(
        default="#212529",
        verbose_name="Body background (dark)",
        help_text=mark_safe(
            "Dark mode: Default background for body.<br>Default: <code>#212529</code>",
        ),
    )
    # ==== SECONDARY COLORS ====
    # Use color for lighter text. Use bg for dividers and disabled states
    secondary_color_light = ColorField(
        default="#6c757d",
        verbose_name="Secondary text (light)",
        help_text=mark_safe(
            "Light mode: Lighter text color option.<br>Default: <code>#6c757d</code>",
        ),
    )
    secondary_bg_light = ColorField(
        default="#e9ecef",
        verbose_name="Secondary background (light)",
        help_text=mark_safe(
            "Light mode: For dividers and disabled states.<br>"
            "Default: <code>#e9ecef</code>",
        ),
    )
    secondary_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Secondary text (dark)",
        help_text=mark_safe(
            "Dark mode: Lighter text color option.<br>Default: <code>#dee2e6</code>",
        ),
    )
    secondary_bg_dark = ColorField(
        default="#343a40",
        verbose_name="Secondary background (dark)",
        help_text=mark_safe(
            "Dark mode: For dividers and disabled states.<br>"
            "Default: <code>#343a40</code>",
        ),
    )
    # ==== TERTIARY COLORS ====
    # Use color for even lighter text. Use bg for hover states, accents, and wells
    tertiary_color_light = ColorField(
        default="#6c757d",
        verbose_name="Tertiary text (light)",
        help_text=mark_safe(
            "Light mode: Even lighter text color option.<br>"
            "Default: <code>#6c757d</code>",
        ),
    )
    tertiary_bg_light = ColorField(
        default="#f8f9fa",
        verbose_name="Tertiary background (light)",
        help_text=mark_safe(
            "Light mode: For hover states, accents, and wells.<br>"
            "Default: <code>#f8f9fa</code>",
        ),
    )
    tertiary_color_dark = ColorField(
        default="#dee2e6",
        verbose_name="Tertiary text (dark)",
        help_text=mark_safe(
            "Dark mode: Even lighter text color option.<br>"
            "Default: <code>#dee2e6</code>",
        ),
    )
    tertiary_bg_dark = ColorField(
        default="#2b3035",
        verbose_name="Tertiary background (dark)",
        help_text=mark_safe(
            "Dark mode: For hover states, accents, and wells.<br>"
            "Default: <code>#2b3035</code>",
        ),
    )
    # ==== EMPHASIS COLOR ====
    # For higher contrast text. Not applicable for backgrounds
    emphasis_color_light = ColorField(
        default="#000000",
        verbose_name="Emphasis color (light)",
        help_text=mark_safe(
            "Light mode: For higher contrast text.<br>Default: <code>#000000</code>",
        ),
    )
    emphasis_color_dark = ColorField(
        default="#ffffff",
        verbose_name="Emphasis color (dark)",
        help_text=mark_safe(
            "Dark mode: For higher contrast text.<br>Default: <code>#ffffff</code>",
        ),
    )
    # ==== BORDER COLOR ====
    # For component borders, dividers, and rules
    border_color_light = ColorField(
        default="#dee2e6",
        verbose_name="Border color (light)",
        help_text=mark_safe(
            "Light mode: For component borders, dividers, and rules.<br>"
            "Default: <code>#dee2e6</code>",
        ),
    )
    border_color_dark = ColorField(
        default="#495057",
        verbose_name="Border color (dark)",
        help_text=mark_safe(
            "Dark mode: For component borders, dividers, and rules.<br>"
            "Default: <code>#495057</code>",
        ),
    )
    # ==== PRIMARY THEME COLOR ====
    # Main theme color, used for hyperlinks, focus styles, and active states
    primary_color = ColorField(
        default="#0d6efd",
        verbose_name="Primary",
        help_text=mark_safe(
            "Main theme color for hyperlinks, focus styles, and active "
            "states.<br>Default: <code>#0d6efd</code>",
        ),
    )
    primary_bg_subtle_light = ColorField(
        default="#cfe2ff",
        verbose_name="Primary subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle primary background.<br>Default: <code>#cfe2ff</code>",
        ),
    )
    primary_border_subtle_light = ColorField(
        default="#9ec5fe",
        verbose_name="Primary subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle primary border.<br>Default: <code>#9ec5fe</code>",
        ),
    )
    primary_text_emphasis_light = ColorField(
        default="#052c65",
        verbose_name="Primary text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized primary text.<br>Default: <code>#052c65</code>",
        ),
    )
    primary_bg_subtle_dark = ColorField(
        default="#031633",
        verbose_name="Primary subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle primary background.<br>Default: <code>#031633</code>",
        ),
    )
    primary_border_subtle_dark = ColorField(
        default="#084298",
        verbose_name="Primary subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle primary border.<br>Default: <code>#084298</code>",
        ),
    )
    primary_text_emphasis_dark = ColorField(
        default="#6ea8fe",
        verbose_name="Primary text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized primary text.<br>Default: <code>#6ea8fe</code>",
        ),
    )
    # ==== SUCCESS THEME COLOR ====
    # Theme color used for positive or successful actions and information
    success_color = ColorField(
        default="#198754",
        verbose_name="Success",
        help_text=mark_safe(
            "Theme color for positive or successful actions.<br>"
            "Default: <code>#198754</code>",
        ),
    )
    success_bg_subtle_light = ColorField(
        default="#d1e7dd",
        verbose_name="Success subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle success background.<br>Default: <code>#d1e7dd</code>",
        ),
    )
    success_border_subtle_light = ColorField(
        default="#a3cfbb",
        verbose_name="Success subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle success border.<br>Default: <code>#a3cfbb</code>",
        ),
    )
    success_text_emphasis_light = ColorField(
        default="#0a3622",
        verbose_name="Success text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized success text.<br>Default: <code>#0a3622</code>",
        ),
    )
    success_bg_subtle_dark = ColorField(
        default="#051b11",
        verbose_name="Success subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle success background.<br>Default: <code>#051b11</code>",
        ),
    )
    success_border_subtle_dark = ColorField(
        default="#0f5132",
        verbose_name="Success subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle success border.<br>Default: <code>#0f5132</code>",
        ),
    )
    success_text_emphasis_dark = ColorField(
        default="#75b798",
        verbose_name="Success text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized success text.<br>Default: <code>#75b798</code>",
        ),
    )
    # ==== DANGER THEME COLOR ====
    # Theme color used for errors and dangerous actions
    danger_color = ColorField(
        default="#dc3545",
        verbose_name="Danger",
        help_text=mark_safe(
            "Theme color for errors and dangerous actions.<br>"
            "Default: <code>#dc3545</code>",
        ),
    )
    danger_bg_subtle_light = ColorField(
        default="#f8d7da",
        verbose_name="Danger subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle danger background.<br>Default: <code>#f8d7da</code>",
        ),
    )
    danger_border_subtle_light = ColorField(
        default="#f1aeb5",
        verbose_name="Danger subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle danger border.<br>Default: <code>#f1aeb5</code>",
        ),
    )
    danger_text_emphasis_light = ColorField(
        default="#58151c",
        verbose_name="Danger text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized danger text.<br>Default: <code>#58151c</code>",
        ),
    )
    danger_bg_subtle_dark = ColorField(
        default="#2c0b0e",
        verbose_name="Danger subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle danger background.<br>Default: <code>#2c0b0e</code>",
        ),
    )
    danger_border_subtle_dark = ColorField(
        default="#842029",
        verbose_name="Danger subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle danger border.<br>Default: <code>#842029</code>",
        ),
    )
    danger_text_emphasis_dark = ColorField(
        default="#ea868f",
        verbose_name="Danger text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized danger text.<br>Default: <code>#ea868f</code>",
        ),
    )
    # ==== WARNING THEME COLOR ====
    # Theme color used for non-destructive warning messages
    warning_color = ColorField(
        default="#ffc107",
        verbose_name="Warning",
        help_text=mark_safe(
            "Theme color for non-destructive warning messages.<br>"
            "Default: <code>#ffc107</code>",
        ),
    )
    warning_bg_subtle_light = ColorField(
        default="#fff3cd",
        verbose_name="Warning subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle warning background.<br>Default: <code>#fff3cd</code>",
        ),
    )
    warning_border_subtle_light = ColorField(
        default="#ffe69c",
        verbose_name="Warning subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle warning border.<br>Default: <code>#ffe69c</code>",
        ),
    )
    warning_text_emphasis_light = ColorField(
        default="#664d03",
        verbose_name="Warning text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized warning text.<br>Default: <code>#664d03</code>",
        ),
    )
    warning_bg_subtle_dark = ColorField(
        default="#332701",
        verbose_name="Warning subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle warning background.<br>Default: <code>#332701</code>",
        ),
    )
    warning_border_subtle_dark = ColorField(
        default="#997404",
        verbose_name="Warning subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle warning border.<br>Default: <code>#997404</code>",
        ),
    )
    warning_text_emphasis_dark = ColorField(
        default="#ffda6a",
        verbose_name="Warning text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized warning text.<br>Default: <code>#ffda6a</code>",
        ),
    )
    # ==== INFO THEME COLOR ====
    # Theme color used for neutral and informative content
    info_color = ColorField(
        default="#0dcaf0",
        verbose_name="Info",
        help_text=mark_safe(
            "Theme color for neutral and informative content.<br>"
            "Default: <code>#0dcaf0</code>",
        ),
    )
    info_bg_subtle_light = ColorField(
        default="#cff4fc",
        verbose_name="Info subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle info background.<br>Default: <code>#cff4fc</code>",
        ),
    )
    info_border_subtle_light = ColorField(
        default="#9eeaf9",
        verbose_name="Info subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle info border.<br>Default: <code>#9eeaf9</code>",
        ),
    )
    info_text_emphasis_light = ColorField(
        default="#055160",
        verbose_name="Info text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized info text.<br>Default: <code>#055160</code>",
        ),
    )
    info_bg_subtle_dark = ColorField(
        default="#032830",
        verbose_name="Info subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle info background.<br>Default: <code>#032830</code>",
        ),
    )
    info_border_subtle_dark = ColorField(
        default="#087990",
        verbose_name="Info subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle info border.<br>Default: <code>#087990</code>",
        ),
    )
    info_text_emphasis_dark = ColorField(
        default="#6edff6",
        verbose_name="Info text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized info text.<br>Default: <code>#6edff6</code>",
        ),
    )
    # ==== LIGHT THEME COLOR ====
    # Additional theme option for less contrasting colors
    light_color = ColorField(
        default="#f8f9fa",
        verbose_name="Light",
        help_text=mark_safe(
            "Additional theme option for less contrasting colors.<br>"
            "Default: <code>#f8f9fa</code>",
        ),
    )
    light_bg_subtle_light = ColorField(
        default="#fcfcfd",
        verbose_name="Light subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle light background.<br>Default: <code>#fcfcfd</code>",
        ),
    )
    light_border_subtle_light = ColorField(
        default="#e9ecef",
        verbose_name="Light subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle light border.<br>Default: <code>#e9ecef</code>",
        ),
    )
    light_text_emphasis_light = ColorField(
        default="#495057",
        verbose_name="Light text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized light text.<br>Default: <code>#495057</code>",
        ),
    )
    light_bg_subtle_dark = ColorField(
        default="#343a40",
        verbose_name="Light subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle light background.<br>Default: <code>#343a40</code>",
        ),
    )
    light_border_subtle_dark = ColorField(
        default="#495057",
        verbose_name="Light subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle light border.<br>Default: <code>#495057</code>",
        ),
    )
    light_text_emphasis_dark = ColorField(
        default="#f8f9fa",
        verbose_name="Light text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized light text.<br>Default: <code>#f8f9fa</code>",
        ),
    )
    # ==== DARK THEME COLOR ====
    # Additional theme option for higher contrasting colors
    dark_color = ColorField(
        default="#212529",
        verbose_name="Dark",
        help_text=mark_safe(
            "Additional theme option for higher contrasting colors.<br>"
            "Default: <code>#212529</code>",
        ),
    )
    dark_bg_subtle_light = ColorField(
        default="#ced4da",
        verbose_name="Dark subtle background (light)",
        help_text=mark_safe(
            "Light mode: Subtle dark background.<br>Default: <code>#ced4da</code>",
        ),
    )
    dark_border_subtle_light = ColorField(
        default="#adb5bd",
        verbose_name="Dark subtle border (light)",
        help_text=mark_safe(
            "Light mode: Subtle dark border.<br>Default: <code>#adb5bd</code>",
        ),
    )
    dark_text_emphasis_light = ColorField(
        default="#495057",
        verbose_name="Dark text emphasis (light)",
        help_text=mark_safe(
            "Light mode: Emphasized dark text.<br>Default: <code>#495057</code>",
        ),
    )
    dark_bg_subtle_dark = ColorField(
        default="#1a1d20",
        verbose_name="Dark subtle background (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle dark background.<br>Default: <code>#1a1d20</code>",
        ),
    )
    dark_border_subtle_dark = ColorField(
        default="#343a40",
        verbose_name="Dark subtle border (dark)",
        help_text=mark_safe(
            "Dark mode: Subtle dark border.<br>Default: <code>#343a40</code>",
        ),
    )
    dark_text_emphasis_dark = ColorField(
        default="#dee2e6",
        verbose_name="Dark text emphasis (dark)",
        help_text=mark_safe(
            "Dark mode: Emphasized dark text.<br>Default: <code>#dee2e6</code>",
        ),
    )
    # ==== LINK COLORS ====
    link_color_light = ColorField(
        default="#0d6efd",
        verbose_name="Link color (light)",
        help_text=mark_safe(
            "Light mode: Default hyperlink color.<br>Default: <code>#0d6efd</code>",
        ),
    )
    link_hover_color_light = ColorField(
        default="#0a58ca",
        verbose_name="Link hover color (light)",
        help_text=mark_safe(
            "Light mode: Hyperlink hover color.<br>Default: <code>#0a58ca</code>",
        ),
    )
    link_color_dark = ColorField(
        default="#6ea8fe",
        verbose_name="Link color (dark)",
        help_text=mark_safe(
            "Dark mode: Default hyperlink color.<br>Default: <code>#6ea8fe</code>",
        ),
    )
    link_hover_color_dark = ColorField(
        default="#8bb9fe",
        verbose_name="Link hover color (dark)",
        help_text=mark_safe(
            "Dark mode: Hyperlink hover color.<br>Default: <code>#8bb9fe</code>",
        ),
    )
    # ==== FONT SETTINGS ====
    font_sans_serif = models.CharField(
        max_length=500,
        default=(
            'system-ui, -apple-system, "Segoe UI", Roboto, '
            '"Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, '
            'sans-serif, "Apple Color Emoji", "Segoe UI Emoji", '
            '"Segoe UI Symbol", "Noto Color Emoji"'
        ),
        verbose_name="Sans-serif font stack",
        help_text=mark_safe(
            "Sans-serif font stack for the site.<br>"
            'Default: system-ui, -apple-system, "Segoe UI", Roboto, '
            '"Helvetica Neue", "Noto Sans", "Liberation Sans", Arial, '
            'sans-serif, "Apple Color Emoji", "Segoe UI Emoji", '
            '"Segoe UI Symbol", "Noto Color Emoji"',
        ),
    )
    font_monospace = models.CharField(
        max_length=500,
        default=(
            "SFMono-Regular, Menlo, Monaco, Consolas, "
            '"Liberation Mono", "Courier New", monospace'
        ),
        verbose_name="Monospace font stack",
        help_text=mark_safe(
            "Default monospace font stack for code and pre elements.<br>"
            "Default: SFMono-Regular, Menlo, Monaco, Consolas, "
            '"Liberation Mono", "Courier New", monospace',
        ),
    )
    body_font_family = models.CharField(
        max_length=100,
        default="var(--bs-font-sans-serif)",
        verbose_name="Body font family",
        help_text=mark_safe(
            "Font family for body text. Typically references --bs-font-sans-serif.<br>"
            "Default: <code>var(--bs-font-sans-serif)</code>",
        ),
    )
    body_font_size = models.CharField(
        max_length=50,
        default="1rem",
        verbose_name="Body font size",
        help_text=mark_safe(
            "Base font size for body text.<br>Default: <code>1rem</code>",
        ),
    )
    body_font_weight = models.CharField(
        max_length=50,
        default="400",
        verbose_name="Body font weight",
        help_text=mark_safe(
            "Font weight for body text.<br>Default: <code>400</code>",
        ),
    )
    body_line_height = models.CharField(
        max_length=50,
        default="1.5",
        verbose_name="Body line height",
        help_text=mark_safe(
            "Line height for body text.<br>Default: <code>1.5</code>",
        ),
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
        MultiFieldPanel(
            [
                FieldRowPanel(["font_sans_serif"]),
                FieldRowPanel(["font_monospace"]),
                FieldRowPanel(["body_font_family"]),
                FieldRowPanel(
                    [
                        "body_font_size",
                        "body_font_weight",
                        "body_line_height",
                    ],
                ),
            ],
            "Fonts",
            help_text="Typography settings for font families, sizes, and spacing.",
        ),
    ]

    def save(self, *args, **kwargs):
        """Increment CSS version on save to invalidate cached CSS."""
        self.css_version += 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Theme Settings"
