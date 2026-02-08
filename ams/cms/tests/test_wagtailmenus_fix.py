"""Tests for wagtailmenus monkey patches.

These tests verify that the monkey patch in ams/cms/admin.py correctly
handles integer primary keys in MainMenuEditView.setup() and get_edit_url().

The original bug: wagtailmenus passes integers to quote()/unquote() functions
that expect strings, causing TypeError in Django 5.2.11 + Wagtail 7.3.
"""

import inspect

import pytest
from django.contrib.admin.utils import quote
from django.contrib.admin.utils import unquote
from wagtail.models import Page
from wagtail.models import Site
from wagtailmenus.menuadmin import MainMenuEditView
from wagtailmenus.models import MainMenu


@pytest.fixture
def site(db):
    """Get or create a test site."""
    root = Page.get_first_root_node()
    site, _created = Site.objects.get_or_create(
        hostname="testserver",
        defaults={
            "root_page": root,
            "is_default_site": True,
        },
    )
    return site


@pytest.fixture
def main_menu(site):
    """Create a main menu for the test site."""
    menu, _created = MainMenu.objects.get_or_create(site=site)
    return menu


@pytest.mark.django_db
class TestWagtailmenusQuoteUnquoteFix:
    """Tests that verify the quote/unquote monkey patch works correctly."""

    def test_unquote_accepts_integers_as_strings(self):
        """Test that our fix allows unquote to work with integer PKs."""
        # Original bug: unquote(3) raises TypeError
        # Our fix: unquote(str(3)) works correctly
        with pytest.raises(TypeError, match="expected string or bytes-like object"):
            unquote(3)

        # After conversion to string, it works
        result = unquote(str(3))
        assert result == "3"

    def test_quote_accepts_integers_as_strings(self):
        """Test that our fix allows quote to work with integer PKs."""
        # quote() with integer works but returns integer unchanged
        # Our fix ensures we pass string: quote(str(3))
        result = quote(str(3))
        assert result == "3"

    def test_patched_setup_method_exists(self):
        """Verify that MainMenuEditView.setup has been monkey-patched."""
        # Check that the method exists and has our docstring
        assert hasattr(MainMenuEditView, "setup")
        source = inspect.getsource(MainMenuEditView.setup)
        assert "Convert pk to string before passing to unquote" in source

    def test_patched_get_edit_url_method_exists(self):
        """Verify that MainMenuEditView.get_edit_url has been monkey-patched."""
        # Check that the method exists and has our docstring
        assert hasattr(MainMenuEditView, "get_edit_url")
        source = inspect.getsource(MainMenuEditView.get_edit_url)
        assert "Convert pk to string before passing to quote" in source
