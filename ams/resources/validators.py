from django.conf import settings
from django.core.exceptions import ValidationError


def patch_menu_item_clean(model_class):
    """Monkey-patch clean() on menu items to reject links when resources are
    disabled.
    """
    original_clean = model_class.clean

    def clean(self):
        if not settings.RESOURCES_ENABLED:
            link_url = getattr(self, "link_url", "") or ""
            if "/resources/" in link_url:
                msg = (
                    "Resources are currently disabled. "
                    "Enable the resources module before adding resource links to menus."
                )
                raise ValidationError(msg)
        original_clean(self)

    model_class.clean = clean
