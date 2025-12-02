"""Module for the custom translate_url template tag."""

from urllib.parse import urlparse
from urllib.parse import urlunparse

from django.conf import settings
from django.template import Library
from django.urls import translate_url as django_translate_url

register = Library()

# Precompute valid language codes at module load time
VALID_LANG_CODES = frozenset(code for code, name in settings.LANGUAGES)


@register.simple_tag(takes_context=True)
def translate_url(context, lang_code, path=None, *args, **kwargs):
    """Get active page's url for a specified language.

    Usage:
        {% translate_url 'en' %} - translates current page
        {% translate_url 'en' '/' %} - translates specific path
    """
    # Early validation of target language code
    lang_code_valid = lang_code in VALID_LANG_CODES

    # If no path provided, use current request path
    if path is None:
        request = context.get("request")
        if not request:
            # Can't do much without the request — return lang root
            return f"/{lang_code}/"
        path = request.get_full_path()  # preserves querystring

    translated = django_translate_url(path, lang_code)
    if translated != path:
        return translated

    # If Django couldn't translate it, try to replace the language prefix manually
    # Only proceed if target lang is valid
    if not lang_code_valid:
        return f"/{lang_code}/"

    # Parse URL only when needed (fallback case)
    parsed = urlparse(path)
    path_parts = parsed.path.split("/")

    # If path starts with a language code (e.g., /en/page/), replace it
    if (
        len(path_parts) > 1
        and path_parts[1] in VALID_LANG_CODES
        and lang_code in VALID_LANG_CODES
    ):
        path_parts[1] = lang_code
        new_path = "/".join(path_parts)
        return urlunparse(parsed._replace(path=new_path))

    # As a last resort, send to the language's root
    return f"/{lang_code}/"
