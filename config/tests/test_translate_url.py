import pytest
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils import translation

from config.templatetags.translate_url import translate_url as tag_translate_url


# Test fallback to request path when no explicit path provided
@pytest.mark.parametrize(
    ("current_path", "target_lang", "expected_path"),
    [
        ("/en/another/page/", "mi", "/mi/another/page/"),
        ("/en/plain/path/", "mi", "/mi/plain/path/"),
        ("/en/current/page/", "mi", "/mi/current/page/"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_uses_request_path_when_no_path_given(
    current_path,
    target_lang,
    expected_path,
):
    """Test that translate_url uses request path when no explicit path is provided."""
    req = RequestFactory().get(current_path)
    ctx = {"request": req}
    result = tag_translate_url(ctx, target_lang)
    assert result == expected_path


# Test cases for URL translation with explicit paths
@pytest.mark.parametrize(
    ("source_lang", "target_lang", "source_path", "expected_path"),
    [
        # English to Māori translations
        ("en", "mi", "/en/another/page/", "/mi/another/page/"),
        ("en", "mi", "/en/plain/path/", "/mi/plain/path/"),
        ("en", "mi", "/en/current/page/", "/mi/current/page/"),
        # Māori to English translations
        ("mi", "en", "/mi/another/page/", "/en/another/page/"),
        ("mi", "en", "/mi/plain/path/", "/en/plain/path/"),
        ("mi", "en", "/mi/current/page/", "/en/current/page/"),
        # Same language (should still translate)
        ("en", "en", "/en/another/page/", "/en/another/page/"),
        ("mi", "mi", "/mi/another/page/", "/mi/another/page/"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_with_explicit_paths(
    source_lang,
    target_lang,
    source_path,
    expected_path,
):
    """Test URL translation between languages with explicit paths."""
    ctx = {"request": RequestFactory().get(f"/{source_lang}/ignored/")}
    with translation.override(source_lang):
        result = tag_translate_url(ctx, target_lang, source_path)
    assert result == expected_path


# Test query string preservation
@pytest.mark.parametrize(
    ("source_lang", "target_lang", "query_string", "path"),
    [
        ("en", "mi", "?a=1&b=2", "/current/page/"),
        ("en", "mi", "?search=test&page=2", "/another/page/"),
        ("en", "mi", "?param=value%20with%20spaces", "/plain/path/"),
        ("en", "mi", "", "/current/page/"),  # No query string
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_preserves_query_strings(
    source_lang,
    target_lang,
    query_string,
    path,
):
    """Test that URL translation preserves query strings from request."""
    req = RequestFactory().get(f"/{source_lang}{path}{query_string}")
    ctx = {"request": req}
    result = tag_translate_url(ctx, target_lang)
    expected = f"/{target_lang}{path}{query_string}"
    assert result == expected


# Test root path handling
@pytest.mark.parametrize(
    ("language_code", "path", "expected_path"),
    [
        ("en", "/", "/en/"),
        ("mi", "/", "/mi/"),
        ("en", None, "/en/"),  # No path provided
        ("mi", None, "/mi/"),  # No path provided
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_root_paths(language_code, path, expected_path):
    """Test translation of root paths returns language-prefixed root."""
    if path is None:
        result = tag_translate_url({}, language_code)
    else:
        result = tag_translate_url({}, language_code, path)
    assert result == expected_path


@pytest.mark.parametrize(
    ("language_code", "expected_path"),
    [
        ("en", "/en/"),
        ("mi", "/mi/"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_without_request_falls_back_to_lang_root(
    language_code,
    expected_path,
):
    """Test that without a request, translate_url returns language root."""
    result = tag_translate_url({}, language_code)
    assert result == expected_path


@pytest.mark.parametrize(
    ("context", "lang_code", "path", "expected_result"),
    [
        # Empty context, no path
        ({}, "en", None, "/en/"),
        ({}, "mi", None, "/mi/"),
        # Empty context with explicit path
        ({}, "en", "/en/another/page/", "/en/another/page/"),
        # Context with request, no path (uses request path)
        (
            {"request": RequestFactory().get("/en/current/page/")},
            "mi",
            None,
            "/mi/current/page/",
        ),
        # Context with request and explicit path (uses explicit path)
        (
            {"request": RequestFactory().get("/en/ignored/")},
            "mi",
            "/en/another/page/",
            "/mi/another/page/",
        ),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_context_variations(context, lang_code, path, expected_result):
    """Test translate_url with various context and parameter combinations."""
    result = tag_translate_url(context, lang_code, path)

    assert result == expected_result


@pytest.mark.parametrize(
    ("source_path", "target_lang", "expected_path"),
    [
        ("/en/another/page/#section", "mi", "/mi/another/page/#section"),
        ("/en/current/page/#top", "mi", "/mi/current/page/#top"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_with_fragments(source_path, target_lang, expected_path):
    """Test URL translation preserves URL fragments (anchors)."""
    ctx = {"request": RequestFactory().get("/en/ignored/")}
    result = tag_translate_url(ctx, target_lang, source_path)
    assert result == expected_path


@pytest.mark.parametrize(
    ("path_with_slash", "target_lang", "expected_path"),
    [
        ("/en/another/page/", "mi", "/mi/another/page/"),
        ("/en/current/page/", "mi", "/mi/current/page/"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_trailing_slash_handling(
    path_with_slash,
    target_lang,
    expected_path,
):
    """Test URL translation handles trailing slashes correctly."""
    result = tag_translate_url({}, target_lang, path_with_slash)
    assert result == expected_path


@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_non_existent_path():
    """Test translate_url handles non-existent paths by preserving the structure."""
    result = tag_translate_url({}, "mi", "/en/does/not/exist/")
    assert result == "/mi/does/not/exist/"


@pytest.mark.parametrize(
    ("path", "target_lang", "expected_path"),
    [
        # Invalid source language code - should fall back to lang root
        ("/xx/page/", "en", "/en/"),
        ("/invalid/page/", "mi", "/mi/"),
        # Invalid target language code - should fall back to lang root
        ("/en/page/", "xx", "/xx/"),
        ("/mi/page/", "invalid", "/invalid/"),
        # Both invalid
        ("/xx/page/", "yy", "/yy/"),
    ],
)
@override_settings(
    ROOT_URLCONF="config.tests.urls_for_translate",
    LANGUAGES=[("en", "English"), ("mi", "Te Reo Māori")],
)
def test_translate_url_invalid_language_codes(path, target_lang, expected_path):
    """Test translate_url with invalid language codes falls back to language root."""
    result = tag_translate_url({}, target_lang, path)
    assert result == expected_path
