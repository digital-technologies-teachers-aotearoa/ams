import pytest
from django.test.utils import override_settings
from django.utils import translation

from config.templatetags.localise_url import localise_url


@override_settings(LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")])
def test_localise_url_falls_back_to_active_language():
    """Without a language_code arg, localise_url uses the active language."""
    with translation.override("mi"):
        assert localise_url("/events/") == "/mi/events/"
    with translation.override("en"):
        assert localise_url("/events/") == "/en/events/"


@pytest.mark.parametrize(
    ("url", "language_code", "expected"),
    [
        # Internal URL without prefix gets prefixed
        ("/events/", "mi", "/mi/events/"),
        ("/events/", "en", "/en/events/"),
        # Already prefixed URLs are unchanged
        ("/mi/events/", "mi", "/mi/events/"),
        ("/en/events/", "en", "/en/events/"),
        ("/mi/events/", "en", "/mi/events/"),
        # External URLs are unchanged
        ("https://example.com/path/", "mi", "https://example.com/path/"),
        ("http://example.com/", "en", "http://example.com/"),
        # Fragment-only links are unchanged
        ("#section", "mi", "#section"),
        # Empty/None inputs return as-is
        ("", "mi", ""),
        (None, "mi", None),
        # URL without leading slash
        ("events/", "mi", "/mi/events/"),
        # Trailing slash is preserved
        ("/resources/", "mi", "/mi/resources/"),
    ],
)
@override_settings(LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")])
def test_localise_url(url, language_code, expected):
    """Test localise_url filter adds language prefix to unlocalized internal URLs."""
    assert localise_url(url, language_code) == expected
