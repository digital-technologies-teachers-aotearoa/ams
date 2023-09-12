import re
from typing import Optional

from django import template
from django.conf import settings
from django.utils.translation import get_language

register = template.Library()


def localize_url(url_suffix: str, language_code: Optional[str] = None) -> str:
    if url_suffix.startswith("#") or url_suffix.find(":") != -1:
        return url_suffix

    url_suffix = url_suffix.removeprefix("/")

    if not language_code:
        language_code = get_language()

    if language_code == settings.LANGUAGE_CODE:
        return f"/{url_suffix}"

    return f"/{language_code}/{url_suffix}"


@register.simple_tag
def change_url_locale(url: str, language_code: str) -> str:
    if url.startswith(f"/{language_code}/"):
        return url

    # If url already contains a language code, then change or remove it
    match = re.match(r"^/[a-z]{2}/(.*)", url)
    if match:
        url_suffix = match.group(1)

        if language_code == settings.LANGUAGE_CODE:
            return f"/{url_suffix}"

        return f"/{language_code}/{url_suffix}"

    return localize_url(url, language_code)


register.filter("localize_url", localize_url)
