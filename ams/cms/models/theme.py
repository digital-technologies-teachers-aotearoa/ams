from django.db import models
from django.forms.models import model_to_dict
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
    Theme color variants (bg_subtle, border_subtle, text_emphasis) are
    auto-derived from base colors using color_utils.derive_theme_variants().

    Full version history is stored in ThemeSettingsRevision model.
    """

    # Cache version for efficient cache invalidation
    cache_version = models.IntegerField(
        default=1,
        editable=False,
        help_text="Auto-incremented on save to invalidate cached CSS",
    )

    # ==== NAVBAR SETTINGS ====
    navbar_bg_color = ColorField(
        default="#f8f9fa",
        verbose_name="Navbar background color",
        help_text=mark_safe(
            "Background color for the navigation bar.<br>"
            "Default: <code>#f8f9fa</code> (light gray)",
        ),
    )
    # ==== FOOTER SETTINGS ====
    footer_bg_color = ColorField(
        default="#f8f9fa",
        verbose_name="Footer background color",
        help_text=mark_safe(
            "Background color for the footer.<br>"
            "Default: <code>#f8f9fa</code> (light gray)",
        ),
    )
    # ==== BODY COLORS ====
    body_color = ColorField(
        default="#212529",
        verbose_name="Body text color",
        help_text=mark_safe(
            "Default foreground color for text.<br>Default: <code>#212529</code>",
        ),
    )
    body_bg = ColorField(
        default="#ffffff",
        verbose_name="Body background",
        help_text=mark_safe(
            "Default background for body.<br>Default: <code>#ffffff</code>",
        ),
    )

    # ==== THEME COLORS ====
    primary_color = ColorField(
        default="#0d6efd",
        verbose_name="Primary",
        help_text=mark_safe(
            "Main theme color for hyperlinks, focus styles, and active "
            "states.<br>Default: <code>#0d6efd</code>",
        ),
    )
    success_color = ColorField(
        default="#198754",
        verbose_name="Success",
        help_text=mark_safe(
            "Theme color for positive or successful actions.<br>"
            "Default: <code>#198754</code>",
        ),
    )
    danger_color = ColorField(
        default="#dc3545",
        verbose_name="Danger",
        help_text=mark_safe(
            "Theme color for errors and dangerous actions.<br>"
            "Default: <code>#dc3545</code>",
        ),
    )
    warning_color = ColorField(
        default="#ffc107",
        verbose_name="Warning",
        help_text=mark_safe(
            "Theme color for non-destructive warning messages.<br>"
            "Default: <code>#ffc107</code>",
        ),
    )
    info_color = ColorField(
        default="#0dcaf0",
        verbose_name="Info",
        help_text=mark_safe(
            "Theme color for neutral and informative content.<br>"
            "Default: <code>#0dcaf0</code>",
        ),
    )

    # ==== LINK COLORS ====
    link_color = ColorField(
        default="#0d6efd",
        verbose_name="Link color",
        help_text=mark_safe(
            "Default hyperlink color.<br>Default: <code>#0d6efd</code>",
        ),
    )
    link_hover_color = ColorField(
        default="#0a58ca",
        verbose_name="Link hover color",
        help_text=mark_safe(
            "Hyperlink hover color.<br>Default: <code>#0a58ca</code>",
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

    # ==== CUSTOM CSS OVERRIDES ====
    custom_css = models.TextField(
        blank=True,
        default="",
        verbose_name="Custom CSS",
        help_text=mark_safe(
            "<strong>WARNING:</strong> Direct CSS overrides can break site layout "
            "and styling. Use with caution. Invalid CSS may cause display issues. "
            "This field accepts pure CSS code that will be injected into all pages.",
        ),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        NativeColorPanel("navbar_bg_color"),
                    ],
                ),
            ],
            "Navbar",
            help_text="Background color for the navigation bar.",
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        NativeColorPanel("footer_bg_color"),
                    ],
                ),
            ],
            "Footer",
            help_text="Background color for the footer.",
        ),
        MultiFieldPanel(
            [
                NativeColorPanel("primary_color"),
                NativeColorPanel("success_color"),
                NativeColorPanel("danger_color"),
                NativeColorPanel("warning_color"),
                NativeColorPanel("info_color"),
            ],
            "Brand Colors",
            help_text=(
                "Theme colors used throughout the site. "
                "Subtle backgrounds, borders, and text emphasis variants "
                "are auto-derived from these base colors."
            ),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        NativeColorPanel("body_color"),
                        NativeColorPanel("body_bg"),
                    ],
                ),
                FieldRowPanel(
                    [
                        NativeColorPanel("link_color"),
                        NativeColorPanel("link_hover_color"),
                    ],
                ),
            ],
            "Body & Links",
            help_text="Default text/background colors and hyperlink colors.",
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
        MultiFieldPanel(
            [
                FieldRowPanel(["custom_css"]),
            ],
            "Advanced: Custom CSS Overrides",
            help_text=mark_safe(
                "<strong style='color: #dc3545;'>DANGER ZONE:</strong> "
                "Custom CSS can override all theme settings and break site design. "
                "Only use if you understand CSS and are prepared to troubleshoot "
                "potential conflicts. Changes apply immediately to all site pages.",
            ),
            classname="collapsed",
        ),
    ]

    def save(self, *args, **kwargs):
        """Save settings and create a revision snapshot."""
        self.cache_version += 1
        super().save(*args, **kwargs)
        # Create a revision snapshot after saving
        ThemeSettingsRevision.objects.create(
            settings=self,
            data=model_to_dict(self, exclude=["id", "site", "cache_version"]),
        )

    class Meta:
        verbose_name = "Theme Settings"


class ThemeSettingsRevision(models.Model):
    """Historical snapshot of ThemeSettings.

    Stores every saved version of theme settings for audit trail and potential rollback.
    """

    settings = models.ForeignKey(
        ThemeSettings,
        on_delete=models.CASCADE,
        related_name="revisions",
        help_text="The theme settings this revision belongs to",
    )
    data = models.JSONField(
        help_text="Snapshot of all theme settings at the time of save",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this revision was created",
        db_index=True,
    )

    class Meta:
        verbose_name = "Theme Settings Revision"
        verbose_name_plural = "Theme Settings Revisions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["settings", "-created_at"]),
        ]

    def __str__(self):
        return f"Revision from {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
