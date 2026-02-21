"""Template tags for theme customization."""

from django import template
from django.core.cache import cache
from django.template.loader import render_to_string
from wagtail.models import Site

from ams.cms import color_utils
from ams.cms.models import ThemeSettings

register = template.Library()


@register.filter
def hex_to_rgb(hex_color):
    """Convert hex color to RGB string for CSS."""
    return color_utils.hex_to_rgb_string(hex_color)


@register.filter(name="auto_theme")
def auto_theme_filter(hex_color):
    """Returns 'light' or 'dark' based on background luminance."""
    return color_utils.auto_theme(hex_color)


def compute_derived_colors(theme):
    """Compute all auto-derived color values from the base theme colors.

    Returns a dict of derived CSS variable values including:
    - Secondary/tertiary colors from body colors
    - Emphasis and border colors
    - For each theme color: bg_subtle, border_subtle, text_emphasis, rgb
    - Light/dark theme color equivalents
    """
    body_color = theme.body_color
    body_bg = theme.body_bg

    derived = {}

    # Body RGB strings
    derived["body_color_rgb"] = color_utils.hex_to_rgb_string(body_color)
    derived["body_bg_rgb"] = color_utils.hex_to_rgb_string(body_bg)

    # Secondary: derived from body colors
    derived["secondary_color"] = color_utils.mix_colors(body_color, body_bg, 0.75)
    derived["secondary_bg"] = color_utils.mix_colors(body_bg, body_color, 0.90)
    derived["secondary_color_rgb"] = color_utils.hex_to_rgb_string(
        derived["secondary_color"],
    )
    derived["secondary_bg_rgb"] = color_utils.hex_to_rgb_string(derived["secondary_bg"])

    # Tertiary: derived from body colors
    derived["tertiary_color"] = color_utils.mix_colors(body_color, body_bg, 0.50)
    derived["tertiary_bg"] = color_utils.mix_colors(body_bg, body_color, 0.95)
    derived["tertiary_color_rgb"] = color_utils.hex_to_rgb_string(
        derived["tertiary_color"],
    )
    derived["tertiary_bg_rgb"] = color_utils.hex_to_rgb_string(derived["tertiary_bg"])

    # Emphasis: near-black for light mode
    derived["emphasis_color"] = "#000000"
    derived["emphasis_color_rgb"] = "0, 0, 0"

    # Border: derived from body bg
    derived["border_color"] = color_utils.mix_colors(body_bg, body_color, 0.85)
    derived["border_color_rgb"] = color_utils.hex_to_rgb_string(derived["border_color"])

    # Theme colors: primary, success, danger, warning, info
    theme_colors = {
        "primary": theme.primary_color,
        "success": theme.success_color,
        "danger": theme.danger_color,
        "warning": theme.warning_color,
        "info": theme.info_color,
    }

    for name, base in theme_colors.items():
        variants = color_utils.derive_theme_variants(base)
        derived[f"{name}_rgb"] = color_utils.hex_to_rgb_string(base)
        derived[f"{name}_bg_subtle"] = variants["bg_subtle"]
        derived[f"{name}_border_subtle"] = variants["border_subtle"]
        derived[f"{name}_text_emphasis"] = variants["text_emphasis"]

    # Light theme color: derived from body_bg
    derived["light"] = color_utils.mix_colors(body_bg, body_color, 0.97)
    derived["light_rgb"] = color_utils.hex_to_rgb_string(derived["light"])
    light_variants = color_utils.derive_theme_variants(derived["light"])
    derived["light_bg_subtle"] = light_variants["bg_subtle"]
    derived["light_border_subtle"] = light_variants["border_subtle"]
    derived["light_text_emphasis"] = light_variants["text_emphasis"]

    # Dark theme color: derived from body_color
    derived["dark"] = color_utils.mix_colors(body_color, body_bg, 0.97)
    derived["dark_rgb"] = color_utils.hex_to_rgb_string(derived["dark"])
    dark_variants = color_utils.derive_theme_variants(derived["dark"])
    derived["dark_bg_subtle"] = dark_variants["bg_subtle"]
    derived["dark_border_subtle"] = dark_variants["border_subtle"]
    derived["dark_text_emphasis"] = dark_variants["text_emphasis"]

    # Link RGB strings
    derived["link_color_rgb"] = color_utils.hex_to_rgb_string(theme.link_color)
    derived["link_hover_color_rgb"] = color_utils.hex_to_rgb_string(
        theme.link_hover_color,
    )

    return derived


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

    # Compute derived values
    theme_data = {
        "theme": theme_settings_obj,
        "derived": compute_derived_colors(theme_settings_obj),
    }

    # Step 4: Render the CSS
    html = render_to_string("templatetags/theme_css.html", theme_data)

    # Step 5: Update both cache tiers
    css_cache_key = css_cache_key_template.format(
        version=theme_settings_obj.cache_version,
        site_id=site.id,
    )

    # Cache indefinitely - will be invalidated by version change
    cache.set(version_cache_key, theme_settings_obj.cache_version, None)
    cache.set(css_cache_key, html, None)

    return html
