from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from wagtail.models import Site

from ams.utils.reserved_paths import get_reserved_paths_set

if TYPE_CHECKING:
    from django.http import HttpRequest


class PathBasedSiteMiddleware(MiddlewareMixin):
    """
    Route requests to different Wagtail Sites based on a path prefix, while
    keeping a single hostname. Example: `/en/` -> English site, `/mi/` -> Māori site.

    How it works:
    - Detect a configured prefix at the start of `PATH_INFO`
    - Set `request.site` to the corresponding Wagtail Site
    - Strip the prefix from `PATH_INFO` so Wagtail page routing sees clean URLs

        Locale-based routing:
        - The first URL segment is treated as a locale code (e.g., `en`, `mi`).
        - The middleware resolves a Wagtail Site with the same hostname and
            `site_name == <locale>`.
        - If no matching Site exists, it falls back to the English site
            (tries `site_name == "English"` then `site_name == "en"`).

    Notes:
    - Create two Wagtail Site records with the same `hostname` and different
      `root_page`. Use the `site_name` values above to identify them.
    - Place this middleware BEFORE `wagtail.core.middleware.SiteMiddleware` so
      `request.site` is already set for downstream Wagtail internals.
    - Requests without a matching prefix fall back to default site behavior.
    """

    def __init__(self, get_response):
        """Initialize middleware and cache valid locale codes.

        Reads `settings.LANGUAGES` to build a set of locale codes for quick
        validation of the first URL segment during request processing.
        """
        super().__init__(get_response)
        self._valid_locales = {
            code for code, _name in getattr(settings, "LANGUAGES", [])
        }
        self._reserved_paths = get_reserved_paths_set()

    def process_request(self, request: HttpRequest):
        """Resolve `request.site` and normalize `PATH_INFO` based on locale,
        unless path is reserved."""
        if not self._valid_locales:
            return

        path = request.META.get("PATH_INFO", "") or request.path
        # Expect `/prefix/...`; ignore `/` or non-matching paths
        if not path.startswith("/"):
            return

        first_segment = self._first_segment(path)
        if not first_segment:
            return

        # Bail if first segment is reserved or not a valid locale.
        if (
            first_segment in self._reserved_paths
            or first_segment not in self._valid_locales
        ):
            return

        # If locale prefix is followed by a reserved segment -> skip routing.
        second_segment = self._second_segment(path)
        if second_segment in self._reserved_paths:
            return

        site = self._resolve_site(request, first_segment)
        if site:
            # Ensure both legacy and internal attributes are set so any code
            # using Wagtail's site resolution sees the selected site.
            request.site = site
            request._wagtail_site = site  # noqa: SLF001
            # Strip the matched prefix from PATH_INFO so Wagtail routing uses
            # URLs relative to the site's root, e.g. `/en/about/` -> `/about/`
            new_path = self._strip_prefix(path, first_segment)
            request.META["PATH_INFO"] = new_path
        return

    @staticmethod
    def _first_segment(path: str) -> str | None:
        """Return the first URL segment or `None`.

        Example: `"/en/abc/def"` -> `"en"`.
        """
        try:
            return path.split("/")[1] or None
        except IndexError:
            return None

    @staticmethod
    def _second_segment(path: str) -> str | None:
        """Return the second URL segment or `None`.

        Example: `"/en/billing/x"` -> `"billing"`.
        """
        try:
            return path.split("/")[2] or None
        except IndexError:
            return None

    @staticmethod
    def _strip_prefix(path: str, prefix: str) -> str:
        """Remove the initial `/<prefix>` from `path`, preserving leading slash."""
        if path.startswith(f"/{prefix}"):
            remainder = path[len(prefix) + 1 :]
            return remainder if remainder.startswith("/") else f"/{remainder}"
        return path

    @staticmethod
    def _resolve_site(
        request: HttpRequest,
        locale: str,
    ) -> Site | None:
        """Resolve a Wagtail `Site` for the given `locale`.

        Attempts to find a `Site` whose `hostname` equals the locale. If none
        is found, falls back to the Wagtail default site (`is_default_site`).
        """
        sites = Site.objects.all()
        if locale:
            sites = sites.filter(hostname=locale)
        site = sites.first()
        if site:
            return site

        return Site.objects.filter(is_default_site=True).first()
