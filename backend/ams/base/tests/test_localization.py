from django.test import TestCase, override_settings
from django.utils import translation

from ..templatetags.localize_url import localize_url

test_languages = [("en", "English"), ("fr", "French")]


@override_settings(WAGTAIL_CONTENT_LANGUAGES=test_languages, LANGUAGES=test_languages)
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
