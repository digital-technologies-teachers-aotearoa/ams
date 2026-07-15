"""Tests for ams.utils.panels."""

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from modeltranslation.utils import build_localized_fieldname
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.admin.panels import get_edit_handler

from ams.terms.models import Term
from ams.terms.models import TermVersion
from ams.utils.panels import translated_field_panels

pytestmark = pytest.mark.django_db


class TestTranslatedFieldPanels:
    """Tests for translated_field_panels()."""

    def test_returns_multifieldpanel_with_given_heading(self):
        panel = translated_field_panels("name", "Name")

        assert isinstance(panel, MultiFieldPanel)
        assert panel.heading == "Name"

    def test_has_one_fieldpanel_per_enabled_language(self):
        panel = translated_field_panels("name", "Name")

        expected_fields = {
            build_localized_fieldname("name", code)
            for code, _ in settings.ENABLED_LANGUAGES
        }
        actual_fields = {child.field_name for child in panel.children}

        assert actual_fields == expected_fields
        assert all(isinstance(child, FieldPanel) for child in panel.children)


class TestTranslatedFieldsForm:
    """Tests for TranslatedFieldsForm."""

    def test_default_language_field_is_required(self):
        form_class = get_edit_handler(Term).get_form_class()

        form = form_class()

        default_field = build_localized_fieldname(
            "name",
            settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        )
        assert form.fields[default_field].required is True

    def test_non_default_language_field_stays_optional(self):
        form_class = get_edit_handler(Term).get_form_class()
        non_default_languages = [
            code
            for code, _ in settings.ENABLED_LANGUAGES
            if code != settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        ]
        if not non_default_languages:
            pytest.skip("Only one language enabled in this environment.")

        form = form_class()

        for code in non_default_languages:
            field_name = build_localized_fieldname("name", code)
            assert form.fields[field_name].required is False

    def test_termversion_content_is_required(self):
        form_class = get_edit_handler(TermVersion).get_form_class()

        form = form_class()

        default_field = build_localized_fieldname(
            "content",
            settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        )
        assert form.fields[default_field].required is True

    def test_raises_if_required_field_was_originally_optional(self):
        """A field must have been required pre-translation to be listed in
        translated_required_fields. modeltranslation records the original
        field on the localized field's `translated_field` attribute; if that
        was blank=True, forcing it required would contradict the model."""
        default_field = build_localized_fieldname(
            "name",
            settings.MODELTRANSLATION_DEFAULT_LANGUAGE,
        )
        translated_field = Term._meta.get_field(default_field).translated_field  # noqa: SLF001
        original_blank = translated_field.blank
        translated_field.blank = True
        try:
            form_class = get_edit_handler(Term).get_form_class()
            with pytest.raises(ImproperlyConfigured):
                form_class()
        finally:
            translated_field.blank = original_blank
