"""Permission utility functions for the AMS application."""

from django.contrib.auth import get_user_model
from django.core.cache import cache

from ams.memberships.models import MembershipStatus

User = get_user_model()


def _check_user_membership_core(user: User) -> bool:
    """
    Core logic to check if a user has an active individual membership.

    This internal function contains the shared business logic without any caching.
    It assumes the user is authenticated and is NOT a superuser.
    It should not be called directly - use one of the public wrapper functions.

    Args:
        user: The authenticated, non-superuser to check permissions for

    Returns:
        bool: True if user has active individual membership, False otherwise
    """
    # Check for active individual membership
    return any(
        m.status() == MembershipStatus.ACTIVE for m in user.individual_memberships.all()
    )


def user_has_active_membership(user: User) -> bool:
    """
    Check if a user has an active membership with Django cache backend caching.

    Returns True if the user is either:
    - A superuser
    - Has an active individual membership

    This function uses Django's cache framework to avoid repeated database queries
    across multiple requests.

    Args:
        user: The user to check permissions for

    Returns:
        bool: True if user has active membership, False otherwise
    """
    # For unauthenticated users and superusers, don't use cache
    # (these checks are fast and don't require DB queries)
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Create a cache key based on user ID
    cache_key = f"user_has_active_membership_{user.id}"

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Call core logic to check membership
    has_active = _check_user_membership_core(user)

    # Cache the result for 5 minutes (300 seconds)
    # This is a reasonable balance between performance and data freshness
    cache.set(cache_key, has_active, 300)

    return has_active


def user_has_active_membership_request_cached(user: User) -> bool:
    """
    Check if a user has an active membership with per-request caching.

    This version caches the result for the duration of a single request only.
    Use this if you need very fresh data but want to avoid multiple DB queries
    within the same request.

    Args:
        user: The user to check permissions for

    Returns:
        bool: True if user has active membership, False otherwise
    """
    # For unauthenticated users and superusers, don't use cache
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    # Use a simple attribute-based cache on the user object for this request
    cache_attr = "_cached_has_active_membership"

    if hasattr(user, cache_attr):
        return getattr(user, cache_attr)

    # Call core logic to check membership
    has_active = _check_user_membership_core(user)

    # Cache on the user object for this request
    setattr(user, cache_attr, has_active)

    return has_active
