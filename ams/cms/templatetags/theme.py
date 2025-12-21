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
def theme_css(context):
    """Render theme CSS with optimized caching.

    Uses a two-tier caching strategy for maximum performance:
    1. Check cache for version info (lightweight, fast)
    2. If version matches, use cached rendered CSS
    3. Only hit database on cache miss or version change

    This ensures:
    - Single cache lookup per request (version check)
    - Database query only when cache is empty or theme updated
    - Immediate propagation of theme changes (no staleness)

    Returns:
        str: Rendered CSS styles in <style> tags
    """
    # Get current site from request
    request = context.get("request")
    if not request:
        return ""

    site = Site.find_for_request(request)
    if not site:
        return ""

    # Two-tier cache keys
    version_cache_key = f"theme_version_site{site.id}"
    css_cache_key_template = "theme_css_v{version}_site{site_id}"

    # Step 1: Check cached version (lightweight check)
    cached_version = cache.get(version_cache_key)

    if cached_version is not None:
        # Step 2: Try to get rendered CSS for this version
        css_cache_key = css_cache_key_template.format(
            version=cached_version,
            site_id=site.id,
        )
        cached_css = cache.get(css_cache_key)

        if cached_css is not None:
            # Cache hit - return immediately without DB query
            return cached_css

    # Step 3: Cache miss or version mismatch - query database
    try:
        theme_settings_obj = ThemeSettings.for_site(site)
    except ThemeSettings.DoesNotExist:
        return ""

    if not theme_settings_obj:
        return ""

    # Step 4: Render the CSS
    html = render_to_string(
        "templatetags/theme_css.html",
        {"theme": theme_settings_obj},
    )

    # Step 5: Update both cache tiers
    css_cache_key = css_cache_key_template.format(
        version=theme_settings_obj.cache_version,
        site_id=site.id,
    )

    # Cache indefinitely - will be invalidated by version change
    cache.set(version_cache_key, theme_settings_obj.cache_version, None)
    cache.set(css_cache_key, html, None)

    return html
