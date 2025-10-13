from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ams.billing"
    verbose_name = _("Billing")

    def ready(self) -> None:  # pragma: no cover - import side effects only
        # Register signals
        from . import signals  # noqa: F401, PLC0415
