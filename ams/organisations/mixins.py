"""View mixins for organisation permission checking."""

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from ams.organisations.models import OrganisationMember


def user_is_organisation_admin(user, organisation):
    """Check if a user is an admin of the given organisation.

    Uses 5-minute caching to reduce database queries for repeated checks.
    Cache is automatically invalidated when member role changes.

    Args:
        user: The user to check permissions for.
        organisation: The organisation to check admin status against.

    Returns:
        bool: True if user is an admin of the organisation, False otherwise.
    """
    # Fast-path for unauthenticated users (no caching needed)
    if not user.is_authenticated:
        return False

    # Fast-path for superusers (no caching needed)
    if user.is_superuser:
        return True

    # Check cache first
    cache_key = f"user_is_org_admin_{user.id}_{organisation.id}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    # Query database
    is_admin = OrganisationMember.objects.filter(
        organisation=organisation,
        user=user,
        role=OrganisationMember.Role.ADMIN,
    ).exists()

    # Cache for 5 minutes (300 seconds)
    cache.set(cache_key, is_admin, 300)

    return is_admin


class OrganisationAdminMixin:
    """Mixin to restrict access to staff/admin or organisation admins.

    This mixin should be used on views that require the user to be either:
    - A staff member or superuser, OR
    - An admin of the specific organisation being accessed

    The view must implement get_object() that returns an Organisation instance.

    Raises:
        PermissionDenied: If user doesn't have permission to access the organisation.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before allowing access to the view.

        Returns:
            HttpResponse: The response from the parent dispatch method.

        Raises:
            PermissionDenied: If user lacks permission to access this organisation.
        """
        organisation = self.get_object()

        # Allow staff/admin
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Check if user is an organisation admin
        if user_is_organisation_admin(request.user, organisation):
            return super().dispatch(request, *args, **kwargs)

        # Deny access with 403
        raise PermissionDenied(
            _("You do not have permission to access this organisation."),
        )
