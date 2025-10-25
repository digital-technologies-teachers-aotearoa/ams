"""Cache invalidation signals for permission utilities."""

from django.core.cache import cache
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.memberships.models import IndividualMembership


@receiver(post_save, sender=IndividualMembership)
@receiver(post_delete, sender=IndividualMembership)
def invalidate_user_membership_cache(sender, instance, **kwargs):
    """
    Invalidate the user membership cache when a membership changes.

    This ensures that cached permission checks are updated when:
    - A new membership is created
    - A membership is updated (status changes)
    - A membership is deleted
    """
    if instance.user_id:
        cache_key = f"user_has_active_membership_{instance.user_id}"
        cache.delete(cache_key)
