from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UtilsConfig(AppConfig):
    name = "ams.utils"
    verbose_name = _("Utils")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signal handlers when the app is ready."""
        import ams.utils.signals  # noqa: F401, PLC0415
