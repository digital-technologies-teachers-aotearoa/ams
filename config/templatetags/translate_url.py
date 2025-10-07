"""Module for the custom translate_url template tag."""

from django.template import Library
from django.urls import translate_url as django_translate_url

register = Library()


@register.simple_tag(takes_context=True)
def translate_url(context, lang_code, path=None, *args, **kwargs):
    """Get active page's url for a specified language.

    Usage:
        {% translate_url 'en' %} - translates current page
        {% translate_url 'en' '/' %} - translates specific path
    """
    request = context.get("request")

    # If no path provided, use current request path
    if path is None:
        if not request:
            # Can't do much without the request — return lang root
            return f"/{lang_code}/"
        path = request.get_full_path()  # preserves querystring

    new = django_translate_url(path, lang_code)
    if new:
        return new

    # As a last resort, send to the language's root
    return f"/{lang_code}/"
