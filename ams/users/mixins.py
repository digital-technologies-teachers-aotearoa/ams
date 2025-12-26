"""View mixins for user and organisation permission checking."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from ams.users.models import OrganisationMember


def user_is_organisation_admin(user, organisation):
    """Check if a user is an admin of the given organisation.

    Args:
        user: The user to check permissions for.
        organisation: The organisation to check admin status against.

    Returns:
        bool: True if user is an admin of the organisation, False otherwise.
    """
    if not user.is_authenticated:
        return False
    return OrganisationMember.objects.filter(
        organisation=organisation,
        user=user,
        role=OrganisationMember.Role.ADMIN,
    ).exists()


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
