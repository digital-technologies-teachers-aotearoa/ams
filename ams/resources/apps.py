# ruff: noqa: PLC0415

from django.apps import AppConfig


class ResourcesAppConfig(AppConfig):
    name = "ams.resources"
    verbose_name = "Resources"

    def ready(self):
        from wagtailmenus.models import FlatMenuItem
        from wagtailmenus.models import MainMenuItem

        from ams.resources.validators import patch_menu_item_clean

        patch_menu_item_clean(MainMenuItem)
        patch_menu_item_clean(FlatMenuItem)
