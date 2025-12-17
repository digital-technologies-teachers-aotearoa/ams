"""Template tags for theme customization."""

from django import template
from django.core.cache import cache
from django.template.loader import render_to_string
from wagtail.models import Site

from ams.cms.models import ThemeSettings

register = template.Library()


@register.filter
def hex_to_rgb(hex_color):
    """Convert hex color to RGB string for CSS.

    Args:
        hex_color: Hex color string (e.g., "#ffffff" or "#fff")

    Returns:
        String of "r, g, b" format for CSS rgb values
    """
    hex_color = hex_color.lstrip("#")

    # Handle 3-digit hex codes
    if len(hex_color) == 3:  # noqa: PLR2004
        hex_color = "".join([c * 2 for c in hex_color])

    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"


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
            cms_context = settings_context.get("cms")
            if cms_context:
                theme_settings = cms_context.get("ThemeSettings")

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
    cached_html = cache.get(cache_key)
    if cached_html:
        return cached_html

    # Render template with theme settings
    html = render_to_string("templatetags/theme_css.html", {"theme": theme_settings})
    cache.set(cache_key, html, None)  # None = cache indefinitely

    return html
