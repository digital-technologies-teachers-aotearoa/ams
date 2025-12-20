"""Tests for theme customization functionality."""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.context_processors import theme_settings as theme_settings_processor
from ams.cms.models import ThemeSettings
from config.templatetags.theme import hex_to_rgb


@pytest.fixture
def site(db):
    """Get or create a test site."""
    root = Page.get_first_root_node()
    site, _created = Site.objects.get_or_create(
        hostname="localhost",
        defaults={
            "root_page": root,
            "is_default_site": True,
        },
    )
    return site


@pytest.mark.django_db
class TestThemeSettings:
    """Tests for ThemeSettings model."""

    def test_create_theme_settings(self, site):
        """Test creating ThemeSettings with default values."""
        theme = ThemeSettings.objects.create(site=site)
        assert theme.primary_color == "#0d6efd"
        # Cache version should be incremented from initial 1
        assert theme.cache_version == 2  # noqa: PLR2004
        # Check that a revision was created
        assert theme.revisions.count() == 1
        latest_revision = theme.revisions.first()
        assert latest_revision.data["primary_color"] == "#0d6efd"

    def test_revision_created_on_save(self, site):
        """Test that a new revision is created on each save."""
        theme = ThemeSettings.objects.create(site=site)
        initial_revision_count = theme.revisions.count()
        initial_cache_version = theme.cache_version

        theme.primary_color = "#ff0000"
        theme.save()

        # Cache version should increment
        assert theme.cache_version == initial_cache_version + 1
        # Should have one more revision
        assert theme.revisions.count() == initial_revision_count + 1
        # Latest revision should have the new color
        latest_revision = theme.revisions.first()
        assert latest_revision.data["primary_color"] == "#ff0000"

    def test_custom_colors(self, site):
        """Test creating ThemeSettings with custom colors."""
        theme = ThemeSettings.objects.create(
            site=site,
            primary_color="#ff0000",
            secondary_color_light="#00ff00",
            body_bg_light="#ffffff",
            body_bg_dark="#000000",
        )

        assert theme.primary_color == "#ff0000"
        assert theme.secondary_color_light == "#00ff00"
        assert theme.body_bg_light == "#ffffff"
        assert theme.body_bg_dark == "#000000"

    def test_invalid_color_raises_validation_error(self, site):
        """Test that invalid color values raise ValidationError."""
        theme = ThemeSettings(site=site, primary_color="invalid")

        with pytest.raises(ValidationError) as exc_info:
            theme.full_clean()
        # ColorField should raise validation error for invalid hex colors
        assert "primary_color" in exc_info.value.message_dict

    def test_revision_stores_timestamp(self, site):
        """Test that revisions store creation timestamp."""
        theme = ThemeSettings.objects.create(site=site)

        latest_revision = theme.revisions.first()
        assert latest_revision is not None
        assert latest_revision.created_at is not None

    def test_multiple_revisions_stored(self, site):
        """Test that all revisions are stored, not just the latest."""
        theme = ThemeSettings.objects.create(site=site)

        # Make multiple changes
        theme.primary_color = "#ff0000"
        theme.save()

        theme.primary_color = "#00ff00"
        theme.save()

        theme.primary_color = "#0000ff"
        theme.save()

        # Should have 4 total revisions (1 from create + 3 from saves)
        assert theme.revisions.count() == 4  # noqa: PLR2004

        # Check that revisions are ordered by most recent first
        revisions = list(theme.revisions.all())
        assert revisions[0].data["primary_color"] == "#0000ff"  # Latest
        assert revisions[1].data["primary_color"] == "#00ff00"
        assert revisions[2].data["primary_color"] == "#ff0000"
        assert revisions[3].data["primary_color"] == "#0d6efd"  # Original


@pytest.mark.django_db
class TestThemeCSSGeneration:
    """Tests for theme CSS generation."""

    def test_hex_to_rgb_conversion(self):
        """Test hex to RGB conversion filter."""
        assert hex_to_rgb("#ffffff") == "255, 255, 255"
        assert hex_to_rgb("#000000") == "0, 0, 0"
        assert hex_to_rgb("#0d6efd") == "13, 110, 253"

    def test_hex_to_rgb_three_digit(self):
        """Test hex to RGB conversion with 3-digit codes."""
        assert hex_to_rgb("#fff") == "255, 255, 255"
        assert hex_to_rgb("#000") == "0, 0, 0"
        assert hex_to_rgb("#abc") == "170, 187, 204"

    def test_template_renders_theme_css(self, site):
        """Test that template renders CSS with theme values."""
        theme = ThemeSettings.objects.create(
            site=site,
            primary_color="#ff0000",
            body_bg_light="#ffffff",
            body_bg_dark="#000000",
        )

        html = render_to_string("templatetags/theme_css.html", {"theme": theme})

        assert ":root" in html
        assert '[data-bs-theme="dark"]' in html
        assert "--bs-primary: #ff0000" in html
        assert "--bs-body-bg: #ffffff" in html
        assert "--bs-primary-rgb: 255, 0, 0" in html
        assert "<style>" in html
        assert "</style>" in html

    def test_dark_mode_css_separate(self, site):
        """Test that dark mode colors are in separate selector."""
        theme = ThemeSettings.objects.create(
            site=site,
            body_bg_light="#ffffff",
            body_bg_dark="#000000",
            body_color_light="#000000",
            body_color_dark="#ffffff",
        )

        html = render_to_string("templatetags/theme_css.html", {"theme": theme})

        # Check light mode section
        light_section = html.split('[data-bs-theme="dark"]')[0]
        assert "--bs-body-bg: #ffffff" in light_section
        assert "--bs-body-color: #000000" in light_section

        # Check dark mode section
        dark_section = html.split('[data-bs-theme="dark"]')[1]
        assert "--bs-body-bg: #000000" in dark_section
        assert "--bs-body-color: #ffffff" in dark_section


@pytest.mark.django_db
class TestThemeSignals:
    """Tests for theme cache clearing signals."""

    def test_cache_cleared_on_delete(self, site):
        """Test that cache is cleared when ThemeSettings is deleted."""
        theme = ThemeSettings.objects.create(site=site)
        cache_key = f"theme_css_v{theme.cache_version}_site{theme.site_id}"

        # Set something in cache
        cache.set(cache_key, "test css", None)
        assert cache.get(cache_key) == "test css"

        # Delete theme
        theme.delete()

        # Cache should be cleared
        assert cache.get(cache_key) is None

    def test_old_cache_cleared_on_save(self, site):
        """Test that old cache version is cleared when saving."""
        theme = ThemeSettings.objects.create(site=site)
        old_version = theme.cache_version
        old_cache_key = f"theme_css_v{old_version}_site{theme.site_id}"

        # Set old cache
        cache.set(old_cache_key, "old css", None)

        # Save to increment version
        theme.primary_color = "#ff0000"
        theme.save()

        # Old cache should be cleared
        assert cache.get(old_cache_key) is None
        assert cache.get(old_cache_key) is None


@pytest.mark.django_db
class TestThemeContextProcessor:
    """Tests for theme_settings context processor."""

    def test_context_processor_provides_theme_css(self, site, rf):
        """Test that context processor provides theme_css in context."""
        theme = ThemeSettings.objects.create(site=site)
        theme.primary_color = "#ff0000"
        theme.save()
        cache.clear()

        request = rf.get("/")
        request.site = site

        # Call context processor
        context = theme_settings_processor(request)

        assert "theme_css" in context
        assert "<style>" in context["theme_css"]
        assert "#ff0000" in context["theme_css"]
        assert "</style>" in context["theme_css"]

    def test_context_processor_uses_two_tier_cache(self, site, rf):
        """Test that context processor uses two-tier caching strategy."""
        theme = ThemeSettings.objects.create(site=site)
        cache.clear()

        request = rf.get("/")
        request.site = site

        # First call - should query DB and cache both tiers
        with patch("ams.cms.context_processors.ThemeSettings.for_site") as mock_query:
            mock_query.return_value = theme
            context1 = theme_settings_processor(request)
            assert mock_query.call_count == 1

        # Second call - should use cache, no DB query
        with patch("ams.cms.context_processors.ThemeSettings.for_site") as mock_query:
            context2 = theme_settings_processor(request)
            assert mock_query.call_count == 0  # No DB query

        # Results should be identical
        assert context1["theme_css"] == context2["theme_css"]

    def test_context_processor_cache_invalidation(self, site, rf):
        """Test that context processor detects version changes."""
        theme = ThemeSettings.objects.create(site=site)
        theme.primary_color = "#ff0000"
        theme.save()
        cache.clear()

        request = rf.get("/")
        request.site = site

        # First call - caches version 2
        context1 = theme_settings_processor(request)
        assert "#ff0000" in context1["theme_css"]

        # Update theme - increments to version 3
        theme.primary_color = "#00ff00"
        theme.save()
        theme.refresh_from_db()

        # Second call - should detect version change and update
        context2 = theme_settings_processor(request)
        assert "#00ff00" in context2["theme_css"]
        assert "#ff0000" not in context2["theme_css"]

    def test_context_processor_no_site(self, rf):
        """Test processor returns empty when Site.find_for_request returns None."""
        # Mock Site.find_for_request to return None
        with patch("ams.cms.context_processors.Site.find_for_request") as mock_find:
            mock_find.return_value = None
            request = rf.get("/")

            context = theme_settings_processor(request)

            assert "theme_css" in context
            assert context["theme_css"] == ""

    def test_context_processor_autocreates_settings(self, site, rf):
        """Test that context processor auto-creates theme settings via for_site."""
        # Ensure no theme settings exist for this site initially
        ThemeSettings.objects.filter(site=site).delete()
        cache.clear()

        request = rf.get("/")
        request.site = site

        # Call context processor - should auto-create settings
        context = theme_settings_processor(request)

        # Should have created settings with default values
        assert "theme_css" in context
        assert "<style>" in context["theme_css"]
        assert len(context["theme_css"]) > 0

        # Verify settings were created in database
        theme = ThemeSettings.for_site(site)
        assert theme is not None
        assert theme.primary_color == "#0d6efd"  # Default value

    def test_context_processor_performance(self, site, rf):
        """Test that context processor only queries DB once."""
        theme = ThemeSettings.objects.create(site=site)
        cache.clear()

        request = rf.get("/")
        request.site = site

        # First call
        with patch("ams.cms.context_processors.ThemeSettings.for_site") as mock_query:
            mock_query.return_value = theme
            theme_settings_processor(request)
            first_call_count = mock_query.call_count

        # Make 10 more calls - should all use cache
        with patch("ams.cms.context_processors.ThemeSettings.for_site") as mock_query:
            for _ in range(10):
                theme_settings_processor(request)
            subsequent_calls = mock_query.call_count

        assert first_call_count == 1
        assert subsequent_calls == 0  # No DB queries

    def test_context_processor_cache_keys(self, site, rf):
        """Test that correct cache keys are used."""
        theme = ThemeSettings.objects.create(site=site)
        cache.clear()

        request = rf.get("/")
        request.site = site

        # Call context processor
        theme_settings_processor(request)

        # Check that both cache tiers are populated
        version_key = f"theme_version_site{site.id}"
        css_key = f"theme_css_v{theme.cache_version}_site{site.id}"

        assert cache.get(version_key) == theme.cache_version
        assert cache.get(css_key) is not None
        assert "<style>" in cache.get(css_key)
