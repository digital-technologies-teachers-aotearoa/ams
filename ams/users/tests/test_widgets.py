"""Tests for custom admin widgets."""

import json

import pytest
from django.test import RequestFactory

from ams.users.widgets import OptionsWidget
from ams.users.widgets import TranslationWidget


@pytest.fixture
def request_factory():
    """Create RequestFactory instance."""
    return RequestFactory()


@pytest.mark.django_db
class TestTranslationWidget:
    """Tests for TranslationWidget."""

    def test_render_with_empty_value(self):
        """Test rendering widget with empty value."""
        widget = TranslationWidget()
        html = widget.render("name_translations", None, {})

        # Check that it renders without errors
        assert "translation-widget" in html
        assert "English" in html

    def test_render_with_populated_value(self):
        """Test rendering widget with populated value."""
        widget = TranslationWidget()
        value = json.dumps({"en": "Test Name"})
        html = widget.render("name_translations", value, {})

        # Check that value appears in rendered HTML
        assert 'value="Test Name"' in html
        assert "translation-widget" in html

    def test_render_with_dict_value(self):
        """Test rendering widget with dict value (not JSON string)."""
        widget = TranslationWidget()
        value = {"en": "Test Name"}
        html = widget.render("name_translations", value, {})

        # Should handle dict gracefully
        assert 'value="Test Name"' in html

    def test_value_from_datadict_with_all_languages(self):
        """Test reconstructing JSON from all language inputs."""
        widget = TranslationWidget()
        data = {
            "name_translations_en": "English Name",
        }

        result = widget.value_from_datadict(data, {}, "name_translations")
        parsed = json.loads(result)

        assert parsed["en"] == "English Name"

    def test_value_from_datadict_with_empty_values(self):
        """Test reconstructing JSON with empty values."""
        widget = TranslationWidget()
        data = {
            "name_translations_en": "",
        }

        result = widget.value_from_datadict(data, {}, "name_translations")

        # Should return empty JSON object when all values are empty
        assert result == "{}"

    def test_value_from_datadict_with_whitespace(self):
        """Test that whitespace-only values are treated as empty."""
        widget = TranslationWidget()
        data = {
            "name_translations_en": "   ",
        }

        result = widget.value_from_datadict(data, {}, "name_translations")

        # Should return empty JSON object
        assert result == "{}"

    def test_get_context_with_json_string(self):
        """Test get_context parses JSON string correctly."""
        widget = TranslationWidget()
        value = json.dumps({"en": "Test"})
        context = widget.get_context("test", value, {})

        assert context["value"] == {"en": "Test"}

    def test_get_context_with_invalid_json(self):
        """Test get_context handles invalid JSON gracefully."""
        widget = TranslationWidget()
        value = "not valid json"
        context = widget.get_context("test", value, {})

        # Should return empty dict for invalid JSON
        assert context["value"] == {}


@pytest.mark.django_db
class TestOptionsWidget:
    """Tests for OptionsWidget."""

    def test_render_with_empty_value(self):
        """Test rendering widget with empty value."""
        widget = OptionsWidget()
        html = widget.render("options", None, {})

        # Check that it renders without errors
        assert "options-widget" in html
        assert "English" in html
        assert "Add Choice" in html

    def test_render_with_populated_value(self):
        """Test rendering widget with populated choices."""
        widget = OptionsWidget()
        value = json.dumps(
            {
                "choices": [
                    {
                        "value": "option1",
                        "label_translations": {"en": "Option 1"},
                    },
                    {
                        "value": "option2",
                        "label_translations": {"en": "Option 2"},
                    },
                ],
            },
        )
        html = widget.render("options", value, {})

        # Check that value is embedded in script tag
        assert "options-widget" in html
        assert "option1" in html
        assert "option2" in html

    def test_render_with_dict_value(self):
        """Test rendering widget with dict value (not JSON string)."""
        widget = OptionsWidget()
        value = {
            "choices": [
                {
                    "value": "option1",
                    "label_translations": {"en": "Option 1"},
                },
            ],
        }
        html = widget.render("options", value, {})

        # Should handle dict gracefully
        assert "options-widget" in html
        assert "option1" in html

    def test_value_from_datadict(self):
        """Test value_from_datadict returns hidden field value."""
        widget = OptionsWidget()

        # JavaScript should populate this hidden field
        data = {
            "options": json.dumps(
                {
                    "choices": [
                        {
                            "value": "val1",
                            "label_translations": {"en": "Label 1"},
                        },
                    ],
                },
            ),
        }

        result = widget.value_from_datadict(data, {}, "options")
        parsed = json.loads(result)

        assert "choices" in parsed
        assert len(parsed["choices"]) == 1
        assert parsed["choices"][0]["value"] == "val1"

    def test_value_from_datadict_with_missing_field(self):
        """Test value_from_datadict with missing field returns empty."""
        widget = OptionsWidget()
        data = {}

        result = widget.value_from_datadict(data, {}, "options")

        # Should return empty JSON object
        assert result == "{}"

    def test_get_context_with_json_string(self):
        """Test get_context parses JSON string correctly."""
        widget = OptionsWidget()
        value = json.dumps({"choices": []})
        context = widget.get_context("test", value, {})

        # Value should be JSON string in value_json for template
        assert context["value_json"] == '{"choices": []}'

    def test_get_context_with_invalid_json(self):
        """Test get_context handles invalid JSON gracefully."""
        widget = OptionsWidget()
        value = "not valid json"
        context = widget.get_context("test", value, {})

        # Should return empty JSON object string for invalid JSON
        assert context["value_json"] == "{}"

    def test_get_context_preserves_nested_structure(self):
        """Test get_context preserves nested translation structure."""
        widget = OptionsWidget()
        value = {
            "choices": [
                {
                    "value": "test",
                    "label_translations": {"en": "Test", "mi": "Whakamātau"},
                },
            ],
        }
        context = widget.get_context("test", value, {})

        # Should be properly JSON-encoded in value_json
        parsed = json.loads(context["value_json"])
        assert parsed["choices"][0]["label_translations"]["en"] == "Test"
        assert parsed["choices"][0]["label_translations"]["mi"] == "Whakamātau"
