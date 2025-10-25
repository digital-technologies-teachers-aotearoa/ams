"""Permission utility functions for the AMS application."""

from django.contrib.auth import get_user_model

from ams.memberships.models import MembershipStatus

User = get_user_model()


def user_has_active_membership(user: User) -> bool:
    """
    Check if a user has an active membership.

    Returns True if the user is either:
    - A superuser
    - Has an active individual membership

    Args:
        user: The user to check permissions for

    Returns:
        bool: True if user has active membership, False otherwise
    """
    if not user.is_authenticated:
        return False

    # Superusers always have access
    if user.is_superuser:
        return True

    # Check for active individual membership
    return any(
        m.status() == MembershipStatus.ACTIVE for m in user.individual_memberships.all()
    )
