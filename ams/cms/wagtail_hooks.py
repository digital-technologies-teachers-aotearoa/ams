from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from ams.utils.permissions import user_has_active_membership


@hooks.register("construct_help_menu")
def add_ams_help_menu_item(request, menu_items):
    """Add AMS help link to the Wagtail admin help menu."""
    menu_items.append(
        MenuItem(
            _("AMS help"),
            f"{settings.DOCUMENTATION_URL}/admin/cms/",
            name="ams_help",
            icon_name="help",
            attrs={"target": "_blank", "rel": "noopener noreferrer"},
        ),
    )


@hooks.register("before_serve_document")
def check_document_permissions(document, request):
    """Check permissions before serving a document."""
    if request.user.is_superuser or user_has_active_membership(request.user):
        return None
    # Else show error and redirect to login
    messages.error(
        request,
        "You must have an active membership to view this file",
    )
    return redirect("account_login")
