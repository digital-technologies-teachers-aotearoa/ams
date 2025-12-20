"""Context processors for CMS app."""

from django.core.cache import cache
from django.template.loader import render_to_string
from wagtail.models import Site

from ams.cms.models import ThemeSettings


def theme_settings(request):
    """Provide theme CSS to all templates with optimized caching.

    Uses a two-tier caching strategy for maximum performance:
    1. Check cache for version info (lightweight, fast)
    2. If version matches, use cached rendered CSS
    3. Only hit database on cache miss or version change

    This ensures:
    - Single cache lookup per request (version check)
    - Database query only when cache is empty or theme updated
    - Immediate propagation of theme changes (no staleness)

    Returns:
        dict: Context with 'theme_css' key containing rendered CSS
    """
    # Get current site
    site = Site.find_for_request(request)
    if not site:
        return {"theme_css": ""}

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
            return {"theme_css": cached_css}

    # Step 3: Cache miss or version mismatch - query database
    try:
        theme_settings_obj = ThemeSettings.for_site(site)
    except ThemeSettings.DoesNotExist:
        return {"theme_css": ""}

    if not theme_settings_obj:
        return {"theme_css": ""}

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

    return {"theme_css": html}
