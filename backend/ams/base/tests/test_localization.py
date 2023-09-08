from django.test import TestCase, override_settings
from django.utils import translation

from ..templatetags.localize_url import change_url_locale, localize_url

test_languages = [("en", "English"), ("fr", "French")]


@override_settings(LANGUAGE_CODE="en", WAGTAIL_CONTENT_LANGUAGES=test_languages, LANGUAGES=test_languages)
class LocalizeUrlTests(TestCase):
    def setUp(self) -> None:
        translation.activate("fr")

    def test_localize_url_adds_language_prefix_to_root_page(self) -> None:
        self.assertEqual("/fr/", localize_url("/"))

    def test_localize_url_adds_language_prefix_to_page(self) -> None:
        self.assertEqual("/fr/about/", localize_url("/about/"))

    def test_localize_url_does_not_modify_external_link(self) -> None:
        url = "https://example.com"
        self.assertEqual(url, localize_url(url))

    def test_localize_url_does_not_modify_anchor_link(self) -> None:
        url = "#"
        self.assertEqual(url, localize_url(url))

    def test_change_url_locale_adds_prefix_to_root_page(self) -> None:
        self.assertEqual("/fr/", change_url_locale("/", "fr"))

    def test_change_url_locale_removes_prefix_from_root_page_for_default_language(self) -> None:
        self.assertEqual("/", change_url_locale("/fr/", "en"))

    def test_change_url_locale_adds_prefix_to_page(self) -> None:
        self.assertEqual("/fr/about/", change_url_locale("/about/", "fr"))

    def test_change_url_locale_removes_prefix_from_page_for_default_language(self) -> None:
        self.assertEqual("/about/", change_url_locale("/fr/about/", "en"))

    def test_change_url_locale_does_not_change_url_already_for_language(self) -> None:
        self.assertEqual("/fr/about/", change_url_locale("/fr/about/", "fr"))

    def test_change_url_locale_does_not_change_url_already_for_default_language(self) -> None:
        self.assertEqual("/about/", change_url_locale("/about/", "en"))
