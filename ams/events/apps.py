# ruff: noqa: PLC0415

from django.apps import AppConfig


class EventsAppConfig(AppConfig):
    name = "ams.events"
    verbose_name = "Events"

    def ready(self):
        from wagtailmenus.models import FlatMenuItem
        from wagtailmenus.models import MainMenuItem

        from ams.events.validators import patch_menu_item_clean

        patch_menu_item_clean(MainMenuItem)
        patch_menu_item_clean(FlatMenuItem)
