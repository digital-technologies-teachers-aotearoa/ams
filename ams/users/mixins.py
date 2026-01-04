"""View mixins for user permission checking."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class UserSelfOrStaffMixin:
    """Mixin to restrict access to user's own profile or staff.

    This mixin should be used on views that require the user to be either:
    - Viewing their own profile, OR
    - A staff member or superuser

    The view must implement get_object() that returns a User instance.

    Raises:
        PermissionDenied: If user doesn't have permission to view the profile.
    """

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before allowing access to the view."""
        profile_user = self.get_object()

        # Allow staff/admin
        if request.user.is_staff or request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        # Check if user is viewing their own profile
        if request.user == profile_user:
            return super().dispatch(request, *args, **kwargs)

        # Deny access with 403
        raise PermissionDenied(
            _("You do not have permission to view this user profile."),
        )
