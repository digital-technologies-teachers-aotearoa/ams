"""Validators for CMS models."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_hex_color(value):
    """Validate that a string is a valid hex color code.

    Args:
        value: String to validate (e.g., "#ffffff" or "#fff")

    Raises:
        ValidationError: If the value is not a valid hex color code
    """
    if not value:
        return

    # Allow both 3-digit and 6-digit hex codes
    if not re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", value):
        raise ValidationError(
            _("%(value)s is not a valid hex color code. Use format #rrggbb or #rgb"),
            params={"value": value},
        )
