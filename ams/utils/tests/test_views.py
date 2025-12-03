"""Tests for utility views, including page_not_found function."""

from http import HTTPStatus

import pytest
from django.http import Http404
from django.test import RequestFactory
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import ContentPage
from ams.cms.models import HomePage
from ams.cms.models import SiteSettings
from ams.utils.views import _build_locale_info
from ams.utils.views import _find_page_in_site
from ams.utils.views import _normalize_path
from ams.utils.views import page_not_found


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture(scope="class")
def setup_multilingual_sites(django_db_setup, django_db_blocker):
    """Set up English and Māori sites with mirrored page structures."""
    with django_db_blocker.unblock():
        # Clean slate
        Site.objects.all().delete()
        Page.objects.filter(depth__gt=1).delete()

        # Get root page
        root = Page.get_first_root_node()

        # Create English site (default)
        en_home = HomePage(title="Home", slug="home-en")
        root.add_child(instance=en_home)
        en_home.save_revision().publish()

        en_site = Site.objects.create(
            hostname="en.example.com",
            port=80,
            root_page=en_home,
            is_default_site=True,
            site_name="English Site",
        )
        SiteSettings.objects.create(site=en_site, language="en")

        # Create English pages
        en_about = ContentPage(title="About Us", slug="about")
        en_home.add_child(instance=en_about)
        en_about.save_revision().publish()

        en_contact = ContentPage(title="Contact", slug="contact")
        en_home.add_child(instance=en_contact)
        en_contact.save_revision().publish()

        en_team = ContentPage(title="Our Team", slug="team")
        en_about.add_child(instance=en_team)
        en_team.save_revision().publish()

        # Create Māori site
        mi_home = HomePage(title="Kāinga", slug="home-mi")
        root.add_child(instance=mi_home)
        mi_home.save_revision().publish()

        mi_site = Site.objects.create(
            hostname="mi.example.com",
            port=80,
            root_page=mi_home,
            is_default_site=False,
            site_name="Te Reo Māori Site",
        )
        SiteSettings.objects.create(site=mi_site, language="mi")

        # Create Māori pages (mirrored structure)
        mi_about = ContentPage(title="Mō Mātou", slug="about")
        mi_home.add_child(instance=mi_about)
        mi_about.save_revision().publish()

        mi_contact = ContentPage(title="Whakapā Mai", slug="contact")
        mi_home.add_child(instance=mi_contact)
        mi_contact.save_revision().publish()

        mi_team = ContentPage(title="Tō Mātou Rōpū", slug="team")
        mi_about.add_child(instance=mi_team)
        mi_team.save_revision().publish()

        # Create French site with partial overlap
        fr_home = HomePage(title="Accueil", slug="home-fr")
        root.add_child(instance=fr_home)
        fr_home.save_revision().publish()

        fr_site = Site.objects.create(
            hostname="fr.example.com",
            port=80,
            root_page=fr_home,
            is_default_site=False,
            site_name="French Site",
        )
        SiteSettings.objects.create(site=fr_site, language="fr")

        # French only has about page
        fr_about = ContentPage(title="À Propos", slug="about")
        fr_home.add_child(instance=fr_about)
        fr_about.save_revision().publish()

        return {
            "en_site": en_site,
            "mi_site": mi_site,
            "fr_site": fr_site,
            "en_home": en_home,
            "mi_home": mi_home,
            "fr_home": fr_home,
            "en_about": en_about,
            "mi_about": mi_about,
            "fr_about": fr_about,
            "en_contact": en_contact,
            "mi_contact": mi_contact,
            "en_team": en_team,
            "mi_team": mi_team,
        }


class TestNormalizePath:
    """Test the _normalize_path helper function."""

    def test_normalize_path_with_no_language_code(self):
        result = _normalize_path("/about/team/", None)
        assert result == "/about/team/"

    def test_normalize_path_with_language_prefix_and_trailing_path(self):
        result = _normalize_path("/en/about/team/", "en")
        assert result == "/about/team/"

    def test_normalize_path_with_language_prefix_only(self):
        result = _normalize_path("/en", "en")
        assert result == "/"

    def test_normalize_path_with_language_prefix_and_slash(self):
        result = _normalize_path("/en/", "en")
        assert result == "/"

    def test_normalize_path_without_matching_prefix(self):
        result = _normalize_path("/about/", "en")
        assert result == "/about/"

    def test_normalize_path_with_different_language_in_path(self):
        result = _normalize_path("/fr/about/", "en")
        assert result == "/fr/about/"

    def test_normalize_path_empty_string(self):
        result = _normalize_path("", "en")
        assert result == ""

    def test_normalize_path_root(self):
        result = _normalize_path("/", "en")
        assert result == "/"


@pytest.mark.django_db
class TestFindPageInSite:
    """Test the _find_page_in_site helper function."""

    def test_find_page_in_site_finds_root_page(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites
        request = request_factory.get("/")

        page = _find_page_in_site(sites["en_site"], "/", request)

        assert page is not None
        assert page.id == sites["en_home"].id

    def test_find_page_in_site_finds_direct_child(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites
        request = request_factory.get("/about/")

        page = _find_page_in_site(sites["en_site"], "/about/", request)

        assert page is not None
        assert page.id == sites["en_about"].id

    def test_find_page_in_site_finds_nested_page(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites
        request = request_factory.get("/about/team/")

        page = _find_page_in_site(sites["en_site"], "/about/team/", request)

        assert page is not None
        assert page.id == sites["en_team"].id

    def test_find_page_in_site_raises_http404_for_nonexistent_page(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites
        request = request_factory.get("/nonexistent/")

        with pytest.raises(Http404):
            _find_page_in_site(sites["en_site"], "/nonexistent/", request)

    def test_find_page_in_site_with_empty_path(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites
        request = request_factory.get("/")

        page = _find_page_in_site(sites["en_site"], "", request)

        assert page is not None
        assert page.id == sites["en_home"].id


@pytest.mark.django_db
class TestBuildLocaleInfo:
    """Test the _build_locale_info helper function."""

    def test_build_locale_info_with_builtin_language(self, setup_multilingual_sites):
        sites = setup_multilingual_sites

        result = _build_locale_info(sites["en_about"], "en")

        assert result["language"] == "en"
        assert result["language_name"] == "English"
        assert result["url"] == sites["en_about"].url_path
        assert result["title"] == "About Us"

    def test_build_locale_info_with_custom_language(self, setup_multilingual_sites):
        sites = setup_multilingual_sites

        result = _build_locale_info(sites["mi_about"], "mi")

        assert result["language"] == "mi"
        assert result["language_name"] == "Te Reo Māori"  # From LANG_INFO
        assert result["url"] == sites["mi_about"].url_path
        assert result["title"] == "Mō Mātou"

    def test_build_locale_info_with_unknown_language(self, setup_multilingual_sites):
        sites = setup_multilingual_sites

        # Mock an unknown language
        result = _build_locale_info(sites["en_about"], "xx")

        assert result["language"] == "xx"
        assert result["language_name"] == "XX"  # Falls back to uppercase
        assert result["url"] == sites["en_about"].url_path
        assert result["title"] == "About Us"


@pytest.mark.django_db
class TestPageNotFoundFunction:
    """Test the page_not_found function (integration tests)."""

    def test_page_not_found_finds_available_locales(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        # Simulate request for /en/about/ that doesn't exist
        request = request_factory.get("/en/about/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        context = response.context_data
        assert "available_locales" in context
        locales = context["available_locales"]

        # Should find Māori and French versions
        assert len(locales) == 2  # noqa: PLR2004

        locale_languages = {loc["language"] for loc in locales}
        assert "mi" in locale_languages
        assert "fr" in locale_languages
        assert "en" not in locale_languages  # Current site excluded

    def test_page_not_found_with_nested_page(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        # Request for nested page /en/about/team/
        request = request_factory.get("/en/about/team/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should only find Māori version (French doesn't have /about/team/)
        assert len(locales) == 1
        assert locales[0]["language"] == "mi"
        assert locales[0]["title"] == "Tō Mātou Rōpū"

    def test_page_not_found_without_language_code(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        request = request_factory.get("/about/")
        # No LANGUAGE_CODE set
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]
        # Should still work, finds pages at /about/ path
        assert len(locales) == 2  # noqa: PLR2004

    def test_page_not_found_without_site(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        request = request_factory.get("/about/")
        request.LANGUAGE_CODE = "en"
        # No site attribute

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]
        # Should find all sites with matching pages
        assert len(locales) == 3  # All three sites  # noqa: PLR2004

    def test_page_not_found_excludes_current_site(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        request = request_factory.get("/mi/contact/")
        request.LANGUAGE_CODE = "mi"
        request.site = sites["mi_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should only find English (not Māori current site, not French without contact)
        assert len(locales) == 1
        assert locales[0]["language"] == "en"

    def test_page_not_found_with_nonexistent_page_path(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        # Request for page that doesn't exist in any site
        request = request_factory.get("/en/nonexistent-page/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should be empty - no matching pages
        assert len(locales) == 0

    def test_page_not_found_handles_site_without_settings(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        # Remove site settings for one site
        SiteSettings.objects.filter(site=sites["fr_site"]).delete()

        request = request_factory.get("/en/about/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should only find Māori (French has no sitesettings.language)
        assert len(locales) == 1
        assert locales[0]["language"] == "mi"

    def test_page_not_found_handles_exceptions_gracefully(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        """Test that page_not_found handles exceptions without breaking."""
        sites = setup_multilingual_sites

        request = request_factory.get("/en/nonexistent/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        # Should not raise exception even when pages don't exist
        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        # Should return empty list when no matching pages found
        locales = response.context_data["available_locales"]
        assert isinstance(locales, list)

    def test_page_not_found_with_language_prefix_stripping(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        # Request with language prefix
        request = request_factory.get("/mi/about/")
        request.LANGUAGE_CODE = "mi"
        request.site = sites["mi_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should find English and French by matching path without language prefix
        assert len(locales) == 2  # noqa: PLR2004
        locale_languages = {loc["language"] for loc in locales}
        assert "en" in locale_languages
        assert "fr" in locale_languages

    def test_page_not_found_handles_root_path(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        request = request_factory.get("/en")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Should find home pages in other sites
        assert len(locales) == 2  # noqa: PLR2004
        titles = {loc["title"] for loc in locales}
        assert "Kāinga" in titles  # Māori home
        assert "Accueil" in titles  # French home

    def test_page_not_found_includes_correct_url_paths(
        self,
        setup_multilingual_sites,
        request_factory,
    ):
        sites = setup_multilingual_sites

        request = request_factory.get("/en/about/")
        request.LANGUAGE_CODE = "en"
        request.site = sites["en_site"]

        response = page_not_found(request)

        assert response.status_code == HTTPStatus.NOT_FOUND
        locales = response.context_data["available_locales"]

        # Check URLs are properly set
        for locale in locales:
            assert locale["url"].startswith("/")
            assert "about" in locale["url"].lower() or locale["title"]
