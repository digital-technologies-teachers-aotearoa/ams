"""Module for the custom localise_url template filter."""

from urllib.parse import urlsplit

from django.conf import settings
from django.template import Library
from django.urls import Resolver404
from django.urls import resolve
from django.utils.translation import get_language

register = Library()


def _get_valid_lang_codes():
    return frozenset(code for code, name in settings.LANGUAGES)


def _resolves_without_language_prefix(path):
    """Return True if `path` resolves to a view without an i18n language prefix.

    Apps registered outside i18n_patterns() in config/urls.py (forum/, billing/,
    cms/, cms-documents/) must never get a language prefix. Rather than
    hardcoding that list, ask the resolver directly: if the path already
    resolves on its own, it doesn't need one.
    """
    if not path.startswith("/"):
        path = f"/{path}"
    candidates = [path]
    if settings.APPEND_SLASH and not path.endswith("/"):
        candidates.append(f"{path}/")
    for candidate in candidates:
        try:
            resolve(candidate)
        except Resolver404:
            continue
        return True
    return False


@register.filter
def localise_url(url, language_code=None):
    """Add language prefix to internal URLs that lack one.

    Falls back to the active language from get_language() when no language_code
    is passed — safe to use in block templates that don't have request in context.

    URLs that already resolve without a language prefix (e.g. /forum/, /cms/,
    /billing/..., /cms-documents/..., registered outside i18n_patterns() in
    config/urls.py) are left untouched.
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
    if _resolves_without_language_prefix(urlsplit(url).path):
        return url
    return f"/{language_code}/{url.lstrip('/')}"
