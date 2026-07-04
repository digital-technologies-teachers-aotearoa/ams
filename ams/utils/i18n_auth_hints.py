# ruff: noqa: RUF001

from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

# This file exists so that makemessages extracts translations for strings
# owned by django-allauth and Django's own password validators. Both render
# text by calling gettext/ngettext against their own source (outside ams/),
# which is not scanned by makemessages. Declaring the same calls here causes
# makemessages to include them in every language catalog automatically, so
# no manual .po maintenance is needed.

_("Already have an account? Then please %(link)ssign in%(end_link)s.")
_("Password")
_("Password (again)")
_("Your password can’t be too similar to your other personal information.")
ngettext_lazy(
    "Your password must contain at least %(min_length)d character.",
    "Your password must contain at least %(min_length)d characters.",
    "min_length",
)
_("Your password can’t be a commonly used password.")
_("Your password can’t be entirely numeric.")
