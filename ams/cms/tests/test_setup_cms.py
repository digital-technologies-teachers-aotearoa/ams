"""Tests for the setup_cms management command."""

from io import StringIO

import pytest
from django.core.management import call_command
from wagtail.models import Locale
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import HomePage
from ams.cms.models import SiteSettings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_cms_state(wagtail_site, db):
    """Delete stale CMS objects left by previous test runs.

    setup_cms calls modify_site_hostname_constraint which runs DDL (ALTER TABLE).
    In psycopg3 this breaks savepoint rollback, so Locale/Site/Page rows can
    persist across --reuse-db runs. This fixture deletes them at the start of
    each test so every test begins with a consistent empty slate.

    Depends on wagtail_site so it runs after the base en Locale/Site are set up.
    """
    Page.objects.filter(depth__gte=2).delete()
    Locale.objects.exclude(language_code="en").delete()
    Site.objects.exclude(id=wagtail_site.id).delete()


def _setup_cms():
    call_command("setup_cms", stdout=StringIO(), stderr=StringIO())


def test_setup_cms_creates_only_enabled_languages(wagtail_site, settings):
    """Languages absent from settings.LANGUAGES never get Wagtail content."""
    settings.LANGUAGES = [("en", "English")]
    settings.WAGTAIL_CONTENT_LANGUAGES = [("en", "English")]
    _setup_cms()

    assert not Locale.objects.filter(language_code="mi").exists()
    assert Site.objects.count() == 1
    assert not SiteSettings.objects.filter(language="mi").exists()


def test_setup_cms_creates_site_per_enabled_language(wagtail_site, settings):
    """Each language in settings.LANGUAGES gets its own Locale/HomePage/Site."""
    settings.LANGUAGES = [("en", "English"), ("mi", "Te Reo Māori")]
    settings.WAGTAIL_CONTENT_LANGUAGES = [("en", "English"), ("mi", "Te Reo Māori")]

    _setup_cms()

    mi_locale = Locale.objects.get(language_code="mi")
    assert HomePage.objects.filter(locale=mi_locale, slug="mi").exists()
    expected_count = 2
    assert Site.objects.count() == expected_count

    mi_site_settings = SiteSettings.objects.get(language="mi")
    assert mi_site_settings.site.is_default_site is False

    en_site_settings = SiteSettings.objects.get(language="en")
    assert en_site_settings.site.is_default_site is True


def test_setup_cms_removes_site_when_language_disabled(wagtail_site, settings):
    """Disabling a language removes its live Site, but keeps Locale/HomePage."""
    settings.LANGUAGES = [("en", "English"), ("mi", "Te Reo Māori")]
    settings.WAGTAIL_CONTENT_LANGUAGES = [("en", "English"), ("mi", "Te Reo Māori")]
    _setup_cms()
    mi_locale = Locale.objects.get(language_code="mi")

    settings.LANGUAGES = [("en", "English")]
    settings.WAGTAIL_CONTENT_LANGUAGES = [("en", "English")]
    _setup_cms()

    assert not Site.objects.filter(sitesettings__language="mi").exists()
    assert Locale.objects.filter(language_code="mi").exists()
    assert HomePage.objects.filter(locale=mi_locale, slug="mi").exists()
