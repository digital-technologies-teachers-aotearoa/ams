from django.conf import settings
from django.core.exceptions import ValidationError


def patch_menu_item_clean(model_class):
    """Monkey-patch clean() on a menu items to reject links when applications are
    disabled."""
    original_clean = model_class.clean

    def clean(self):
        if not settings.EVENTS_ENABLED:
            link_url = getattr(self, "link_url", "") or ""
            if "/events/" in link_url:
                msg = (
                    "Events are currently disabled. "
                    "Enable the events module before adding event links to menus."
                )
                raise ValidationError(msg)
        original_clean(self)

    model_class.clean = clean
