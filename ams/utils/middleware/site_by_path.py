from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import cache
from wagtail.models import Site

if TYPE_CHECKING:
    from django.http import HttpRequest

SITE_CACHE_TTL = 300
SITE_CACHE_KEY_PREFIX = "ams:path-site:v1"
_CACHE_MISS = object()


def site_cache_key(language_code: str) -> str:
    return f"{SITE_CACHE_KEY_PREFIX}:{language_code}"


def invalidate_site_cache() -> None:
    for language_code, _name in settings.LANGUAGES:
        cache.delete(site_cache_key(language_code))


class PathBasedSiteMiddleware:
    """
    Route requests to different Wagtail Sites based on the request's language code.

    How it works:
    - Read `request.LANGUAGE_CODE` (set by Django's LocaleMiddleware)
    - Set `request.site` to the Wagtail Site with matching language in SiteSettings
    - If no matching Site exists, fall back to the default Wagtail site

    Notes:
    - Each Wagtail Site should have a SiteSettings record with the appropriate language.
    - Place this middleware AFTER `django.middleware.locale.LocaleMiddleware` so
      `request.LANGUAGE_CODE` is already set.
    """

    def __init__(self, get_response):
        """
        Initialize middleware and cache valid locale codes.

        Reads `settings.LANGUAGES` to build a set of valid locale codes.
        """
        self.get_response = get_response
        self._valid_locales = {
            code for code, _name in getattr(settings, "LANGUAGES", [])
        }

    def __call__(self, request: HttpRequest):
        """
        Process the incoming request and set the Wagtail Site based on language code.

        - Checks if the language code is in allowed locales.
        - Sets `request.site` and `_wagtail_site` if a matching site is found.
        """
        language_code = getattr(request, "LANGUAGE_CODE", None)
        # Only process if language code is recognized
        if language_code in self._valid_locales:
            site = self._resolve_site(request)
            if site:
                request.site = site
                request._wagtail_site = site  # noqa: SLF001
        return self.get_response(request)

    @staticmethod
    def _resolve_site(request: HttpRequest) -> Site | None:
        """
        Resolve a Wagtail `Site` based on the request's language code.

        Attempts to find a `Site` whose SiteSettings language matches
        `request.LANGUAGE_CODE`. If none is found, falls back to the Wagtail
        default site (`is_default_site`).
        """
        language_code = request.LANGUAGE_CODE
        cache_key = site_cache_key(language_code)
        cached_site = cache.get(cache_key, _CACHE_MISS)
        if cached_site is not _CACHE_MISS:
            return cached_site

        site = Site.objects.filter(
            sitesettings__language=language_code,
        ).first()
        # Fall back to the default site if no language match is found.
        resolved_site = site or Site.objects.filter(is_default_site=True).first()
        cache.set(cache_key, resolved_site, SITE_CACHE_TTL)
        return resolved_site
