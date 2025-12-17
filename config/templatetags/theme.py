"""Template tags for theme customization."""

from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
from wagtail.models import Site

from ams.cms.models import ThemeSettings

register = template.Library()


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (e.g., "#ffffff" or "#fff")

    Returns:
        Tuple of (r, g, b) integers
    """
    hex_color = hex_color.lstrip("#")

    # Handle 3-digit hex codes
    if len(hex_color) == 3:  # noqa: PLR2004
        hex_color = "".join([c * 2 for c in hex_color])

    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def generate_theme_css(theme_settings):
    """Generate CSS custom properties from theme settings.

    Args:
        theme_settings: ThemeSettings model instance

    Returns:
        String containing CSS with custom properties
    """
    if not theme_settings:
        return ""

    # Helper to convert and format RGB
    def rgb_str(hex_color):
        r, g, b = hex_to_rgb(hex_color)
        return f"{r}, {g}, {b}"

    # Build light mode CSS
    light_css = f"""
:root,
[data-bs-theme="light"] {{
  /* Body */
  --bs-body-color: {theme_settings.body_color_light};
  --bs-body-color-rgb: {rgb_str(theme_settings.body_color_light)};
  --bs-body-bg: {theme_settings.body_bg_light};
  --bs-body-bg-rgb: {rgb_str(theme_settings.body_bg_light)};

  /* Secondary */
  --bs-secondary-color: {theme_settings.secondary_color_light};
  --bs-secondary-color-rgb: {rgb_str(theme_settings.secondary_color_light)};
  --bs-secondary-bg: {theme_settings.secondary_bg_light};
  --bs-secondary-bg-rgb: {rgb_str(theme_settings.secondary_bg_light)};

  /* Tertiary */
  --bs-tertiary-color: {theme_settings.tertiary_color_light};
  --bs-tertiary-color-rgb: {rgb_str(theme_settings.tertiary_color_light)};
  --bs-tertiary-bg: {theme_settings.tertiary_bg_light};
  --bs-tertiary-bg-rgb: {rgb_str(theme_settings.tertiary_bg_light)};

  /* Emphasis */
  --bs-emphasis-color: {theme_settings.emphasis_color_light};
  --bs-emphasis-color-rgb: {rgb_str(theme_settings.emphasis_color_light)};

  /* Border */
  --bs-border-color: {theme_settings.border_color_light};
  --bs-border-color-rgb: {rgb_str(theme_settings.border_color_light)};

  /* Primary */
  --bs-primary: {theme_settings.primary_color};
  --bs-primary-rgb: {rgb_str(theme_settings.primary_color)};
  --bs-primary-bg-subtle: {theme_settings.primary_bg_subtle_light};
  --bs-primary-border-subtle: {theme_settings.primary_border_subtle_light};
  --bs-primary-text-emphasis: {theme_settings.primary_text_emphasis_light};

  /* Success */
  --bs-success: {theme_settings.success_color};
  --bs-success-rgb: {rgb_str(theme_settings.success_color)};
  --bs-success-bg-subtle: {theme_settings.success_bg_subtle_light};
  --bs-success-border-subtle: {theme_settings.success_border_subtle_light};
  --bs-success-text-emphasis: {theme_settings.success_text_emphasis_light};

  /* Danger */
  --bs-danger: {theme_settings.danger_color};
  --bs-danger-rgb: {rgb_str(theme_settings.danger_color)};
  --bs-danger-bg-subtle: {theme_settings.danger_bg_subtle_light};
  --bs-danger-border-subtle: {theme_settings.danger_border_subtle_light};
  --bs-danger-text-emphasis: {theme_settings.danger_text_emphasis_light};

  /* Warning */
  --bs-warning: {theme_settings.warning_color};
  --bs-warning-rgb: {rgb_str(theme_settings.warning_color)};
  --bs-warning-bg-subtle: {theme_settings.warning_bg_subtle_light};
  --bs-warning-border-subtle: {theme_settings.warning_border_subtle_light};
  --bs-warning-text-emphasis: {theme_settings.warning_text_emphasis_light};

  /* Info */
  --bs-info: {theme_settings.info_color};
  --bs-info-rgb: {rgb_str(theme_settings.info_color)};
  --bs-info-bg-subtle: {theme_settings.info_bg_subtle_light};
  --bs-info-border-subtle: {theme_settings.info_border_subtle_light};
  --bs-info-text-emphasis: {theme_settings.info_text_emphasis_light};

  /* Light */
  --bs-light: {theme_settings.light_color};
  --bs-light-rgb: {rgb_str(theme_settings.light_color)};
  --bs-light-bg-subtle: {theme_settings.light_bg_subtle_light};
  --bs-light-border-subtle: {theme_settings.light_border_subtle_light};
  --bs-light-text-emphasis: {theme_settings.light_text_emphasis_light};

  /* Dark */
  --bs-dark: {theme_settings.dark_color};
  --bs-dark-rgb: {rgb_str(theme_settings.dark_color)};
  --bs-dark-bg-subtle: {theme_settings.dark_bg_subtle_light};
  --bs-dark-border-subtle: {theme_settings.dark_border_subtle_light};
  --bs-dark-text-emphasis: {theme_settings.dark_text_emphasis_light};

  /* Links */
  --bs-link-color: {theme_settings.link_color_light};
  --bs-link-color-rgb: {rgb_str(theme_settings.link_color_light)};
  --bs-link-hover-color: {theme_settings.link_hover_color_light};
  --bs-link-hover-color-rgb: {rgb_str(theme_settings.link_hover_color_light)};
}}

[data-bs-theme="dark"] {{
  /* Body */
  --bs-body-color: {theme_settings.body_color_dark};
  --bs-body-color-rgb: {rgb_str(theme_settings.body_color_dark)};
  --bs-body-bg: {theme_settings.body_bg_dark};
  --bs-body-bg-rgb: {rgb_str(theme_settings.body_bg_dark)};

  /* Secondary */
  --bs-secondary-color: {theme_settings.secondary_color_dark};
  --bs-secondary-color-rgb: {rgb_str(theme_settings.secondary_color_dark)};
  --bs-secondary-bg: {theme_settings.secondary_bg_dark};
  --bs-secondary-bg-rgb: {rgb_str(theme_settings.secondary_bg_dark)};

  /* Tertiary */
  --bs-tertiary-color: {theme_settings.tertiary_color_dark};
  --bs-tertiary-color-rgb: {rgb_str(theme_settings.tertiary_color_dark)};
  --bs-tertiary-bg: {theme_settings.tertiary_bg_dark};
  --bs-tertiary-bg-rgb: {rgb_str(theme_settings.tertiary_bg_dark)};

  /* Emphasis */
  --bs-emphasis-color: {theme_settings.emphasis_color_dark};
  --bs-emphasis-color-rgb: {rgb_str(theme_settings.emphasis_color_dark)};

  /* Border */
  --bs-border-color: {theme_settings.border_color_dark};
  --bs-border-color-rgb: {rgb_str(theme_settings.border_color_dark)};

  /* Primary */
  --bs-primary-bg-subtle: {theme_settings.primary_bg_subtle_dark};
  --bs-primary-border-subtle: {theme_settings.primary_border_subtle_dark};
  --bs-primary-text-emphasis: {theme_settings.primary_text_emphasis_dark};

  /* Success */
  --bs-success-bg-subtle: {theme_settings.success_bg_subtle_dark};
  --bs-success-border-subtle: {theme_settings.success_border_subtle_dark};
  --bs-success-text-emphasis: {theme_settings.success_text_emphasis_dark};

  /* Danger */
  --bs-danger-bg-subtle: {theme_settings.danger_bg_subtle_dark};
  --bs-danger-border-subtle: {theme_settings.danger_border_subtle_dark};
  --bs-danger-text-emphasis: {theme_settings.danger_text_emphasis_dark};

  /* Warning */
  --bs-warning-bg-subtle: {theme_settings.warning_bg_subtle_dark};
  --bs-warning-border-subtle: {theme_settings.warning_border_subtle_dark};
  --bs-warning-text-emphasis: {theme_settings.warning_text_emphasis_dark};

  /* Info */
  --bs-info-bg-subtle: {theme_settings.info_bg_subtle_dark};
  --bs-info-border-subtle: {theme_settings.info_border_subtle_dark};
  --bs-info-text-emphasis: {theme_settings.info_text_emphasis_dark};

  /* Light */
  --bs-light-bg-subtle: {theme_settings.light_bg_subtle_dark};
  --bs-light-border-subtle: {theme_settings.light_border_subtle_dark};
  --bs-light-text-emphasis: {theme_settings.light_text_emphasis_dark};

  /* Dark */
  --bs-dark-bg-subtle: {theme_settings.dark_bg_subtle_dark};
  --bs-dark-border-subtle: {theme_settings.dark_border_subtle_dark};
  --bs-dark-text-emphasis: {theme_settings.dark_text_emphasis_dark};

  /* Links */
  --bs-link-color: {theme_settings.link_color_dark};
  --bs-link-color-rgb: {rgb_str(theme_settings.link_color_dark)};
  --bs-link-hover-color: {theme_settings.link_hover_color_dark};
  --bs-link-hover-color-rgb: {rgb_str(theme_settings.link_hover_color_dark)};
}}
"""
    return light_css.strip()


@register.simple_tag(takes_context=True)
def theme_css_variables(context):
    """Generate and cache theme CSS variables.

    This tag generates inline CSS with Bootstrap custom properties
    based on ThemeSettings. The CSS is cached for performance.

    Usage in templates:
        {% load theme %}
        {% theme_css_variables %}

    Returns:
        HTML style tag with CSS custom properties
    """
    # Try to get theme settings from context (provided by Wagtail)
    theme_settings = None
    if hasattr(context, "get"):
        settings_context = context.get("settings")
        if settings_context:
            theme_settings = getattr(settings_context.get("cms"), "ThemeSettings", None)

    # If not in context, try to get from database directly
    if not theme_settings:
        site = Site.find_for_request(context.get("request"))
        if site:
            theme_settings = ThemeSettings.for_site(site)

    if not theme_settings:
        return ""

    # Create cache key including site ID and CSS version for invalidation
    cache_key = f"theme_css_v{theme_settings.css_version}_site{theme_settings.site_id}"

    # Try to get from cache
    cached_css = cache.get(cache_key)
    if cached_css:
        return mark_safe(f"<style>{cached_css}</style>")  # noqa: S308

    # Generate CSS and cache it indefinitely (manual invalidation via css_version)
    css = generate_theme_css(theme_settings)
    cache.set(cache_key, css, None)  # None = cache indefinitely

    return mark_safe(f"<style>{css}</style>")  # noqa: S308
