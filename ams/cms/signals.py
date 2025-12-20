"""Signals for CMS models.

Theme Settings Caching Strategy:
--------------------------------
The theme settings use a two-tier caching approach for optimal performance:

1. Version Cache Key: `theme_version_site{site_id}`
   - Stores only the cache_version integer (lightweight)
   - Checked on every request (fast cache lookup)

2. CSS Cache Key: `theme_css_v{version}_site{site_id}`
   - Stores the rendered CSS HTML (heavier object)
   - Only fetched when version matches

Flow:
- On first request: DB query → render CSS → cache both tiers
- On subsequent requests: Check version cache → use CSS cache (no DB query)
- On theme update: cache_version increments → old caches become stale
- Signals clean up old cache entries to prevent bloat

This ensures:
- Only 1 lightweight cache lookup per request
- Database query only on cache miss or theme updates
- Immediate propagation of changes (no staleness)
"""

from django.core.cache import cache
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.cms.models import ThemeSettings


@receiver(post_save, sender=ThemeSettings)
def clear_theme_cache_on_save(sender, instance, **kwargs):
    """Clear theme CSS cache when ThemeSettings is saved.

    The cache_version field is auto-incremented on save, so old cache keys
    will naturally become stale. This signal clears the previous version
    to prevent cache bloat.

    Also updates the version cache to point to the new version.
    """
    # Clear previous version CSS cache (if it exists)
    if instance.cache_version > 1:
        old_css_cache_key = (
            f"theme_css_v{instance.cache_version - 1}_site{instance.site_id}"
        )
        cache.delete(old_css_cache_key)

    # Update version cache to new version (triggers cache invalidation)
    version_cache_key = f"theme_version_site{instance.site_id}"
    cache.set(version_cache_key, instance.cache_version, None)


@receiver(post_delete, sender=ThemeSettings)
def clear_theme_cache_on_delete(sender, instance, **kwargs):
    """Clear theme CSS cache when ThemeSettings is deleted."""
    css_cache_key = f"theme_css_v{instance.cache_version}_site{instance.site_id}"
    version_cache_key = f"theme_version_site{instance.site_id}"
    cache.delete(css_cache_key)
    cache.delete(version_cache_key)
