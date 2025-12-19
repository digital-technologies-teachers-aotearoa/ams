"""Signals for CMS models."""

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
    """
    # Clear previous version cache (if it exists)
    if instance.cache_version > 1:
        old_cache_key = (
            f"theme_css_v{instance.cache_version - 1}_site{instance.site_id}"
        )
        cache.delete(old_cache_key)


@receiver(post_delete, sender=ThemeSettings)
def clear_theme_cache_on_delete(sender, instance, **kwargs):
    """Clear theme CSS cache when ThemeSettings is deleted."""
    cache_key = f"theme_css_v{instance.cache_version}_site{instance.site_id}"
    cache.delete(cache_key)
