from django.conf import settings
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem


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
