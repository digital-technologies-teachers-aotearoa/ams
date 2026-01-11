"""App configuration for the terms app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TermsConfig(AppConfig):
    """Configuration for the terms app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ams.terms"
    verbose_name = _("Terms and Conditions")
