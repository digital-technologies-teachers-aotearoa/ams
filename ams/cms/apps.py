from django.apps import AppConfig


class CmsConfig(AppConfig):
    name = "ams.cms"
    verbose_name = "CMS"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Import signals when the app is ready."""
        import ams.cms.signals  # noqa: F401, PLC0415
