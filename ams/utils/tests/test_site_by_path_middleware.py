import pytest
from django.test import RequestFactory
from wagtail.models import Site

from ams.utils.middleware.site_by_path import PathBasedSiteMiddleware


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture(autouse=True)
def languages_settings(settings):
    settings.LANGUAGES = [
        ("en", "English"),
        ("mi", "Te Reo Māori"),
    ]
    return settings


@pytest.fixture
def sites(db):
    # Ensure a clean slate: exactly one default site overall
    Site.objects.all().delete()
    # English site is also the default site
    en_default_site = Site.objects.create(
        hostname="en",
        port=80,
        root_page_id=1,  # dummy; tests do not traverse pages
        is_default_site=True,
        site_name="English",
    )
    mi_site = Site.objects.create(
        hostname="mi",
        port=80,
        root_page_id=1,
        is_default_site=False,
        site_name="Te Reo Māori",
    )
    return {"en": en_default_site, "mi": mi_site}


def _process(mw: PathBasedSiteMiddleware, path: str, host: str = "website.com"):
    request = RequestFactory().get(path, HTTP_HOST=host)
    mw.process_request(request)
    return request


@pytest.mark.parametrize(
    ("path", "locale", "expected_path"),
    [
        ("/en/about/", "en", "/about/"),
        ("/mi/contact/", "mi", "/contact/"),
    ],
)
def test_locale_routes_and_strips_prefix(sites, rf, path, locale, expected_path):
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, path)

    assert getattr(request, "site", None) is not None
    assert request.site.hostname == locale
    # Wagtail cached site must also be set for third-party calls
    assert getattr(request, "_wagtail_site", None) is request.site
    # Prefix stripped
    assert request.META["PATH_INFO"] == expected_path


@pytest.mark.parametrize("path", ["/about/", "/xx/page/"])
def test_non_locale_prefix_does_not_set_site(sites, rf, path):
    """When no/invalid locale prefix, middleware does not set site."""
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, path)

    # Middleware doesn't set site when prefix is not a valid locale
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")
    # Path remains unchanged
    assert request.META["PATH_INFO"] == path


def test_non_slash_path_is_ignored(sites, rf):
    mw = PathBasedSiteMiddleware(lambda r: r)
    # PATH_INFO without leading slash should be ignored (returns early)
    request = RequestFactory().get("en/about")
    mw.process_request(request)
    # No site assigned
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


def test_unknown_locale_with_languages_empty_ignores_processing(sites, rf, settings):
    settings.LANGUAGES = []
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, "/en/about/")
    # No site assigned because valid locales are empty
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/en/", "en"),
        ("/en/about/", "en"),
        ("/", None),
        ("", None),
    ],
)
def test_first_segment_detects_locale_correctly(sites, path, expected):
    assert PathBasedSiteMiddleware._first_segment(path) == expected  # noqa: SLF001


@pytest.mark.parametrize(
    ("path", "prefix", "expected"),
    [
        ("/en/about/", "en", "/about/"),
        ("/mi", "mi", "/"),
        ("/en", "en", "/"),
        ("/xx/page", "en", "/xx/page"),
    ],
)
def test_strip_prefix_preserves_leading_slash(sites, path, prefix, expected):
    assert PathBasedSiteMiddleware._strip_prefix(path, prefix) == expected  # noqa: SLF001


def test_middleware_sets_both_site_attributes_on_locale_match(sites, rf):
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, "/en/")
    assert request.site.hostname == "en"
    assert getattr(request, "_wagtail_site", None) is request.site


def test_middleware_sets_default_on_no_prefix(sites, rf):
    """When no prefix, middleware doesn't interfere - lets Wagtail handle it."""
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, "/")
    # Middleware doesn't set site - Wagtail's SiteMiddleware handles this
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


def test_middleware_handles_different_hostnames_gracefully(sites, rf):
    mw = PathBasedSiteMiddleware(lambda r: r)
    # Even with a different host, locale routing should match by hostname==locale
    request = _process(mw, "/mi/section/", host="otherhost.example")
    assert request.site.hostname == "mi"
    assert request.META["PATH_INFO"] == "/section/"


@pytest.mark.parametrize(
    "path",
    [
        "/billing/invoice/123/",
        "/users/profile/",
        "/forum/thread/456/",
        "/cms/admin/",
        "/accounts/login/",
    ],
)
def test_reserved_paths_not_treated_as_locales(sites, rf, path):
    """Reserved paths like /billing/, /users/, etc are not treated as locales."""
    mw = PathBasedSiteMiddleware(lambda r: r)
    request = _process(mw, path)
    # Should not set site attribute (or should set to default)
    assert not hasattr(request, "site") or request.site.is_default_site


@pytest.mark.parametrize(
    "path",
    [
        "/en/billing/invoice/123/",
        "/mi/users/profile/",
        "/en/forum/thread/456/",
        "/mi/cms/admin/",
        "/en/accounts/login/",
    ],
)
def test_reserved_paths_after_locale_do_not_set_site(sites, rf, path):
    """Locale prefix + reserved path should not set site or strip path."""
    mw = PathBasedSiteMiddleware(lambda r: r)
    original_path = path
    request = _process(mw, path)
    # Middleware should ignore locale because next segment is reserved
    assert not hasattr(request, "site") or request.site.is_default_site
    assert not hasattr(request, "_wagtail_site")
    # Path should remain unchanged
    assert request.META["PATH_INFO"] == original_path
