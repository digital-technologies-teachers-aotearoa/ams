"""Tests for theme customization functionality."""

from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.template import Context
from django.template import Template
from django.template.loader import render_to_string
from wagtail.models import Page
from wagtail.models import Site

from ams.cms.models import ThemeSettings
from config.templatetags.theme import hex_to_rgb


@pytest.fixture
def site(db):
    """Create a test site."""
    root = Page.get_first_root_node()
    return Site.objects.create(
        hostname="localhost",
        root_page=root,
        is_default_site=True,
    )


@pytest.mark.django_db
class TestThemeSettings:
    """Tests for ThemeSettings model."""

    def test_create_theme_settings(self, site):
        """Test creating ThemeSettings with default values."""
        theme = ThemeSettings.objects.create(site=site)
        assert theme.primary_color == "#0d6efd"
        assert theme.css_version == 2  # Incremented from 1 on create  # noqa: PLR2004

    def test_css_version_increments_on_save(self, site):
        """Test that css_version increments on each save."""
        theme = ThemeSettings.objects.create(site=site)
        initial_version = theme.css_version

        theme.primary_color = "#ff0000"
        theme.save()

        assert theme.css_version == initial_version + 1

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
class TestThemeTemplateTag:
    """Tests for theme_css_variables template tag."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

    def test_template_tag_renders(self, site, rf):
        """Test that template tag renders CSS."""
        # Clear cache before starting
        cache.clear()

        theme = ThemeSettings.objects.create(site=site)
        theme.primary_color = "#ff0000"
        theme.save()
        theme.refresh_from_db()  # Reload to get fresh data

        template = Template(
            "{% load theme %}{% theme_css_variables %}",
        )
        request = rf.get("/")
        request.site = site

        context = Context(
            {
                "request": request,
                "settings": {
                    "cms": {
                        "ThemeSettings": theme,
                    },
                },
            },
        )

        result = template.render(context)

        assert "<style>" in result
        assert "--bs-primary: #ff0000" in result
        assert "</style>" in result

    def test_template_tag_uses_cache(self, site, rf):
        """Test that template tag uses cache on subsequent calls."""
        theme = ThemeSettings.objects.create(site=site)
        cache.clear()

        template = Template("{% load theme %}{% theme_css_variables %}")
        request = rf.get("/")
        request.site = site

        context = Context(
            {
                "request": request,
                "settings": {"cms": {"ThemeSettings": theme}},
            },
        )

        # First render - should generate and cache
        with patch("config.templatetags.theme.render_to_string") as mock_render:
            mock_render.return_value = "<style>/* test css */</style>"
            result1 = template.render(context)
            assert mock_render.call_count == 1

        # Second render - should use cache
        with patch("config.templatetags.theme.render_to_string") as mock_render:
            mock_render.return_value = "<style>/* test css */</style>"
            result2 = template.render(context)
            assert mock_render.call_count == 0  # Not called, used cache

        assert result1 == result2

    def test_template_tag_cache_invalidation(self, site, rf):
        """Test that cache is invalidated when settings change."""
        theme = ThemeSettings.objects.create(site=site)
        theme.primary_color = "#ff0000"
        theme.save()
        theme.refresh_from_db()  # Reload to get fresh data
        cache.clear()

        template = Template("{% load theme %}{% theme_css_variables %}")
        request = rf.get("/")
        request.site = site

        context = Context(
            {
                "request": request,
                "settings": {"cms": {"ThemeSettings": theme}},
            },
        )

        # First render
        result1 = template.render(context)
        assert "#ff0000" in result1

        # Update theme (increments css_version)
        theme.primary_color = "#00ff00"
        theme.save()
        theme.refresh_from_db()  # Reload to get fresh data

        # Update context with new theme
        context = Context(
            {
                "request": request,
                "settings": {"cms": {"ThemeSettings": theme}},
            },
        )

        # Second render should reflect changes
        result2 = template.render(context)
        assert "#00ff00" in result2
        assert "#ff0000" not in result2

    def test_template_tag_no_settings(self, rf):
        """Test template tag returns empty string when no settings."""
        # Delete all sites and theme settings to ensure clean state
        ThemeSettings.objects.all().delete()
        Site.objects.all().delete()

        template = Template("{% load theme %}{% theme_css_variables %}")
        request = rf.get("/")
        # Create a request without a site attribute, and no settings in context
        context = Context({"request": request})

        result = template.render(context)
        # Without a site, the tag should return an empty string
        assert result.strip() == ""


@pytest.mark.django_db
class TestThemeSignals:
    """Tests for theme cache clearing signals."""

    def test_cache_cleared_on_delete(self, site):
        """Test that cache is cleared when ThemeSettings is deleted."""
        theme = ThemeSettings.objects.create(site=site)
        cache_key = f"theme_css_v{theme.css_version}_site{theme.site_id}"

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
        old_version = theme.css_version
        old_cache_key = f"theme_css_v{old_version}_site{theme.site_id}"

        # Set old cache
        cache.set(old_cache_key, "old css", None)

        # Save to increment version
        theme.primary_color = "#ff0000"
        theme.save()

        # Old cache should be cleared
        assert cache.get(old_cache_key) is None
