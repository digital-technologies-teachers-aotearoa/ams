from django import template
from django.conf import settings
from django.utils.translation import get_language

register = template.Library()


def localize_url(url_suffix: str) -> str:
    if url_suffix.startswith("#") or url_suffix.find(":") != -1:
        return url_suffix

    url_suffix = url_suffix.removeprefix("/")

    current_language = get_language()
    if current_language == settings.LANGUAGE_CODE:
        return f"/{url_suffix}"

    return f"/{current_language}/{url_suffix}"


register.filter("localize_url", localize_url)
