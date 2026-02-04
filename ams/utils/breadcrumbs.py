"""Breadcrumb functionality for Django pages."""

from typing import TypedDict

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch
from django.urls import Resolver404
from django.urls import resolve
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ams.cms.models import HomePage
from ams.organisations.models import Organisation

User = get_user_model()


class BreadcrumbConfig(TypedDict, total=False):
    """Configuration for a breadcrumb entry."""

    parent: str | None
    label: str  # Static label
    label_getter: str  # Name of dynamic label getter function


# Breadcrumb registry with parent and label configuration
BREADCRUMB_REGISTRY: dict[str, BreadcrumbConfig] = {
    # User pages
    "users:detail": {
        "parent": None,
        "label_getter": "get_user_dashboard_label",
    },
    "users:update": {
        "parent": "users:detail",
        "label": _("Update Account"),
    },
    # Membership pages
    "memberships:apply-individual": {
        "parent": "users:detail",
        "label": _("Apply for Membership"),
    },
    # Organisation pages
    "organisations:create": {
        "parent": "users:detail",
        "label": _("Create Organisation"),
    },
    "organisations:detail": {
        "parent": "users:detail",
        "label_getter": "get_organisation_name",
    },
    "organisations:update": {
        "parent": "organisations:detail",
        "label": _("Edit Organisation"),
    },
    "organisations:invite_member": {
        "parent": "organisations:detail",
        "label": _("Invite Member"),
    },
    "organisations:remove_member": {
        "parent": "organisations:detail",
        "label": _("Remove Member"),
    },
    "organisations:make_admin": {
        "parent": "organisations:detail",
        "label": _("Make Admin"),
    },
    "organisations:revoke_admin": {
        "parent": "organisations:detail",
        "label": _("Revoke Admin"),
    },
    "organisations:leave": {
        "parent": "organisations:detail",
        "label": _("Leave Organisation"),
    },
    "organisations:deactivate": {
        "parent": "organisations:detail",
        "label": _("Deactivate Organisation"),
    },
    "memberships:apply-organisation": {
        "parent": "organisations:detail",
        "label": _("Add Membership"),
    },
    "memberships:add_seats": {
        "parent": "organisations:detail",
        "label": _("Add Seats"),
    },
    # Auth pages (allauth)
    "account_login": {
        "parent": None,
        "label": _("Sign In"),
    },
    "account_signup": {
        "parent": None,
        "label": _("Sign Up"),
    },
    "account_change_password": {
        "parent": "users:detail",
        "label": _("Change Password"),
    },
    "account_email": {
        "parent": "users:detail",
        "label": _("Email Addresses"),
    },
    "mfa_index": {
        "parent": "users:detail",
        "label": _("MFA"),
    },
    "mfa_activate_totp": {
        "parent": "users:detail",
        "label": _("MFA"),
    },
    "mfa_deactivate_totp": {
        "parent": "users:detail",
        "label": _("MFA"),
    },
}


def _get_cached_value(request, cache_key, getter_func):
    """Generic cache getter with fallback."""
    if not hasattr(request, "breadcrumb_cache"):
        request.breadcrumb_cache = {}

    if cache_key not in request.breadcrumb_cache:
        request.breadcrumb_cache[cache_key] = getter_func()

    return request.breadcrumb_cache[cache_key]


def _get_organisation_name(request, **kwargs):
    """Get organisation name for breadcrumb with caching and error handling."""

    def get_name():
        try:
            if org_uuid := kwargs.get("uuid"):
                return Organisation.objects.get(uuid=org_uuid).name
        except Organisation.DoesNotExist:
            pass
        return _("Organisation")

    return _get_cached_value(request, "org_name", get_name)


def _get_user_dashboard_label(request, **kwargs):
    """Get user dashboard label using user's full name."""

    def get_name():
        try:
            if username := kwargs.get("username"):
                user = User.objects.get(username=username)
                return user.get_full_name()
        except User.DoesNotExist:
            pass
        return _("User")

    return _get_cached_value(request, "user_name", get_name)


# Label getter functions
LABEL_GETTERS = {
    "get_organisation_name": _get_organisation_name,
    "get_user_dashboard_label": _get_user_dashboard_label,
}


def get_current_view_name(request):
    """
    Get the current view name from the request.

    Returns:
        str: View name like 'users:detail' or None if not resolvable
    """
    try:
        resolved = resolve(request.path_info)
    except Resolver404:
        return None
    else:
        # Build full view name with namespace
        if resolved.namespace:
            return f"{resolved.namespace}:{resolved.url_name}"
        return resolved.url_name


def is_homepage(request):
    """Check if current page is homepage."""
    # For Wagtail pages
    if hasattr(request, "page"):
        return isinstance(request.page, HomePage)

    # For Django views
    view_name = get_current_view_name(request)
    # Check if root redirect or any language-prefixed root
    if view_name == "root_redirect":
        return True

    # Check if path is a root path (with or without language prefix)
    path = request.path.rstrip("/")
    return bool(path == "" or path in ["/en", "/de", "/es", "/fr"])


def _get_kwargs_for_view(request, view_name, current_kwargs):
    """Get the appropriate kwargs for a view, filling in missing parameters."""
    # For users:detail, ensure we have username
    if view_name == "users:detail" and "username" not in current_kwargs:
        if request.user.is_authenticated:
            return {**current_kwargs, "username": request.user.username}

    return current_kwargs


def get_breadcrumbs_for_django_page(request, view_name, **kwargs):
    """
    Generate breadcrumbs for a Django view.

    Args:
        request: Current request (needed for i18n and caching)
        view_name: e.g., 'organisations:update'
        **kwargs: URL kwargs from resolved URL

    Returns:
        list: Breadcrumb dicts with url, title, is_active
    """
    breadcrumbs = []
    current_name = view_name
    visited = set()  # Prevent circular references

    while current_name and current_name not in visited:
        visited.add(current_name)

        if current_name not in BREADCRUMB_REGISTRY:
            break

        config = BREADCRUMB_REGISTRY[current_name]

        # Get kwargs for this specific view
        view_kwargs = _get_kwargs_for_view(request, current_name, kwargs)

        # Get label (static or dynamic)
        if "label_getter" in config:
            label = LABEL_GETTERS[config["label_getter"]](request, **view_kwargs)
        else:
            label = config["label"]

        # Build URL with proper kwargs
        try:
            url = reverse(current_name, kwargs=view_kwargs)
        except NoReverseMatch:
            url = None

        breadcrumbs.insert(
            0,
            {
                "url": url,
                "title": label,
                "is_active": current_name == view_name,
            },
        )

        current_name = config["parent"]

    # Always prepend home
    breadcrumbs.insert(
        0,
        {
            "url": reverse("root_redirect"),  # Uses i18n
            "title": _("Home"),
            "is_active": False,
        },
    )

    return breadcrumbs
