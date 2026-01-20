"""Custom widgets for Django admin."""

import json

from django import forms
from django.conf import settings


class TranslationWidget(forms.Widget):
    """Widget for editing translation JSON fields as a table."""

    template_name = "admin/widgets/translation_widget.html"

    def __init__(self, attrs=None):
        super().__init__(attrs)
        # Get languages from settings
        self.languages = settings.LANGUAGES

    def get_context(self, name, value, attrs):
        """Add languages and parsed value to context."""
        context = super().get_context(name, value, attrs)
        context["widget"]["languages"] = self.languages

        # Parse JSON value
        if value:
            try:
                parsed_value = json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                parsed_value = {}
        else:
            parsed_value = {}

        context["value"] = parsed_value
        return context

    def value_from_datadict(self, data, files, name):
        """Reconstruct JSON from individual language inputs."""
        result = {}
        for lang_code, _lang_name in self.languages:
            input_name = f"{name}_{lang_code}"
            value = data.get(input_name, "").strip()
            if value:
                result[lang_code] = value
        return json.dumps(result) if result else "{}"


class OptionsWidget(forms.Widget):
    """Widget for editing options JSON field as a dynamic table."""

    template_name = "admin/widgets/options_widget.html"

    def __init__(self, attrs=None):
        super().__init__(attrs)
        # Get languages from settings
        self.languages = settings.LANGUAGES

    def get_context(self, name, value, attrs):
        """Add languages and parsed value to context."""
        context = super().get_context(name, value, attrs)
        context["widget"]["languages"] = self.languages

        # Parse JSON value
        if value:
            try:
                parsed_value = json.loads(value) if isinstance(value, str) else value
            except (json.JSONDecodeError, TypeError):
                parsed_value = {}
        else:
            parsed_value = {}
        # Add JSON string for template use
        context["value_json"] = json.dumps(parsed_value)
        return context

    def value_from_datadict(self, data, files, name):
        """Reconstruct JSON from dynamic table inputs."""
        # This will be populated by JavaScript on form submit
        # JavaScript stores the final JSON in the hidden field
        return data.get(name, "{}")
