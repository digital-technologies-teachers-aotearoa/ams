"""Cache invalidation signals for permission utilities."""

from django.core.cache import cache
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver

from ams.memberships.models import IndividualMembership
from ams.memberships.models import OrganisationMembership
from ams.organisations.models import OrganisationMember


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


@receiver(post_save, sender=OrganisationMembership)
@receiver(post_delete, sender=OrganisationMembership)
def invalidate_organisation_membership_cache(sender, instance, **kwargs):
    """
    Invalidate user membership caches when an organisation membership changes.

    When an organisation's membership status changes, all users who are
    members of that organisation need their permission caches invalidated.

    This ensures that cached permission checks are updated when:
    - An organisation membership is created
    - An organisation membership is updated (status changes)
    - An organisation membership is deleted
    """
    if instance.organisation_id:
        # Get all active members of this organisation and invalidate their caches
        member_user_ids = OrganisationMember.objects.filter(
            organisation_id=instance.organisation_id,
            user_id__isnull=False,
            accepted_datetime__isnull=False,
            declined_datetime__isnull=True,
        ).values_list("user_id", flat=True)

        for user_id in member_user_ids:
            cache_key = f"user_has_active_membership_{user_id}"
            cache.delete(cache_key)


@receiver(post_save, sender=OrganisationMember)
@receiver(post_delete, sender=OrganisationMember)
def invalidate_organisation_member_cache(sender, instance, **kwargs):
    """
    Invalidate user membership cache when organisation member status changes.

    When a user joins, leaves, or changes status in an organisation,
    their permission cache needs to be invalidated.

    This ensures that cached permission checks are updated when:
    - A user accepts an organisation invitation
    - A user's organisation membership changes
    - A user is removed from an organisation
    """
    if instance.user_id:
        cache_key = f"user_has_active_membership_{instance.user_id}"
        cache.delete(cache_key)


@receiver(post_save, sender=OrganisationMember)
@receiver(post_delete, sender=OrganisationMember)
def invalidate_organisation_admin_cache(sender, instance, **kwargs):
    """
    Invalidate organisation admin cache when member role changes.

    Ensures cache is fresh when:
    - Member promoted/demoted to/from admin
    - Member leaves organisation
    - Member status changes (declined/revoked)
    """
    if instance.user_id and instance.organisation_id:
        cache_key = f"user_is_org_admin_{instance.user_id}_{instance.organisation_id}"
        cache.delete(cache_key)
