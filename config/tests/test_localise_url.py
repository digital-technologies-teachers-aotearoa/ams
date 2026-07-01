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
        # Non-i18n app roots (registered outside i18n_patterns in
        # config/urls.py) stay unprefixed regardless of language.
        ("/forum/", "en", "/forum/"),
        ("/forum/", "mi", "/forum/"),
        # No trailing slash — exercises the APPEND_SLASH resolve() fallback.
        ("/forum", "en", "/forum"),
        # Wagtail admin root.
        ("/cms/", "en", "/cms/"),
        # Billing endpoint (billing/ itself has no root view — use a real
        # leaf route).
        ("/billing/xero/webhooks/", "en", "/billing/xero/webhooks/"),
        # Wagtail document serve endpoint (cms-documents/ has no root view
        # either).
        ("/cms-documents/1/test-file.pdf", "en", "/cms-documents/1/test-file.pdf"),
        # Query string / fragment are preserved and don't break the
        # resolve() check.
        ("/forum/?tab=active", "en", "/forum/?tab=active"),
        ("/forum/#top", "en", "/forum/#top"),
        # Root redirect view — deliberate behavior change: this now
        # resolves without a prefix, so it's left as the user's
        # preferred-language root rather than forced to /en/.
        ("/", "en", "/"),
        # Genuinely unresolvable path still falls back to prefixing
        # (regression guard for the fail-safe design).
        ("/does-not-exist/", "en", "/en/does-not-exist/"),
    ],
)
@override_settings(LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")])
def test_localise_url(url, language_code, expected):
    """Test localise_url filter adds language prefix to unlocalized internal URLs."""
    assert localise_url(url, language_code) == expected
