"""Module for the custom localise_url template filter."""

from django.conf import settings
from django.template import Library
from django.utils.translation import get_language

register = Library()


def _get_valid_lang_codes():
    return frozenset(code for code, name in settings.LANGUAGES)


@register.filter
def localise_url(url, language_code=None):
    """Add language prefix to internal URLs that lack one.

    Falls back to the active language from get_language() when no language_code
    is passed — safe to use in block templates that don't have request in context.
    """
    if not url:
        return url
    if not language_code:
        language_code = get_language()
    if not language_code:
        return url
    if "://" in url or url.startswith("#"):
        return url
    valid_lang_codes = _get_valid_lang_codes()
    parts = url.lstrip("/").split("/")
    if parts and parts[0] in valid_lang_codes:
        return url
    return f"/{language_code}/{url.lstrip('/')}"
