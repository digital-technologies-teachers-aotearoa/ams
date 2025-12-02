import pytest
from django.test import RequestFactory
from wagtail.models import Site

from ams.cms.models import SiteSettings
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
    # Create SiteSettings with language for each site
    SiteSettings.objects.create(site=en_default_site, language="en")
    SiteSettings.objects.create(site=mi_site, language="mi")
    return {"en": en_default_site, "mi": mi_site}


def _process(
    mw: PathBasedSiteMiddleware,
    path: str,
    language_code: str | None = None,
    host: str = "website.com",
):
    """Helper to process a request through the middleware."""
    request = RequestFactory().get(path, HTTP_HOST=host)
    if language_code:
        request.LANGUAGE_CODE = language_code
    # Middleware returns the response from get_response
    mw(request)
    return request


@pytest.mark.parametrize(
    ("language_code", "expected_hostname"),
    [
        ("en", "en"),
        ("mi", "mi"),
    ],
)
def test_middleware_sets_site_based_on_language_code(
    sites,
    language_code,
    expected_hostname,
):
    """Middleware sets site based on request.LANGUAGE_CODE."""
    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/", language_code=language_code)

    assert getattr(request, "site", None) is not None
    assert request.site.hostname == expected_hostname
    # Wagtail cached site must also be set for third-party calls
    assert getattr(request, "_wagtail_site", None) is request.site


def test_middleware_without_language_code_does_not_set_site(sites):
    """When no LANGUAGE_CODE, middleware does not set site."""
    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/")

    # Middleware doesn't set site when LANGUAGE_CODE is not set
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


def test_middleware_with_invalid_language_code_does_not_set_site(sites):
    """Invalid language code should not set site."""
    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/", language_code="xx")

    # Middleware doesn't set site when language code is not valid
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


def test_middleware_falls_back_to_default_site_when_no_match(sites, db):
    """When no site matches the language, fall back to default site."""
    # Remove SiteSettings for 'mi' site
    SiteSettings.objects.filter(site=sites["mi"]).delete()

    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/", language_code="mi")

    # Should fall back to default site
    assert request.site.is_default_site
    assert request.site.hostname == "en"


def test_middleware_with_empty_languages_setting(sites, settings):
    """When LANGUAGES is empty, middleware does not set site."""
    settings.LANGUAGES = []
    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/", language_code="en")

    # No site assigned because valid locales are empty
    assert not hasattr(request, "site")
    assert not hasattr(request, "_wagtail_site")


def test_middleware_calls_get_response(sites):
    """Middleware calls get_response and returns its result."""
    response_mock = object()
    get_response_called = []

    def mock_get_response(request):
        get_response_called.append(request)
        return response_mock

    mw = PathBasedSiteMiddleware(mock_get_response)
    request = RequestFactory().get("/about/")
    request.LANGUAGE_CODE = "en"

    result = mw(request)

    assert result is response_mock
    assert len(get_response_called) == 1
    assert get_response_called[0] is request


def test_middleware_sets_both_site_attributes_on_language_match(sites):
    """Middleware sets both site and _wagtail_site attributes."""
    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/", language_code="en")

    assert request.site.hostname == "en"
    assert getattr(request, "_wagtail_site", None) is request.site


def test_middleware_handles_multiple_sites_with_same_language(sites, db):
    """When multiple sites have the same language, first match is used."""
    # Create another site with English language
    another_en_site = Site.objects.create(
        hostname="en-alt",
        port=80,
        root_page_id=1,
        is_default_site=False,
        site_name="English Alternative",
    )
    SiteSettings.objects.create(site=another_en_site, language="en")

    mw = PathBasedSiteMiddleware(lambda r: None)
    request = _process(mw, "/about/", language_code="en")

    # Should get one of the English sites (implementation uses .first())
    assert request.site.sitesettings.language == "en"
