from django.db import models
from django.utils.translation import gettext_lazy as _


class ColourModes(models.TextChoices):
    LIGHT = "light", _("Light")
    DARK = "dark", _("Dark")


class BackgroundOpacities(models.TextChoices):
    OPACITY_15 = "15", "15%"
    OPACITY_25 = "25", "25%"
    OPACITY_50 = "50", "50%"
    OPACITY_75 = "75", "75%"
    OPACITY_100 = "100", "100%"
