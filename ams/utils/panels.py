"""Custom Wagtail panels"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from modeltranslation.utils import build_localized_fieldname
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import MultiFieldPanel


def translated_field_panels(field_name, heading):
    """One FieldPanel per enabled language, grouped under a single heading.

    Wagtail snippet editing has no equivalent of the Django admin's
    TabbedTranslationAdmin, so a translated field would otherwise render as a
    single box writing whichever language is active. Driven by
    settings.ENABLED_LANGUAGES, so a deployment with only English enabled sees
    one box.
    """
    return MultiFieldPanel(
        [
            FieldPanel(build_localized_fieldname(field_name, code), heading=name)
            for code, name in settings.ENABLED_LANGUAGES
        ],
        heading=heading,
    )


class TranslatedFieldsForm(WagtailAdminModelForm):
    """Make each translated field required in the default language only.

    Mirrors how TabbedTranslationAdmin handles required-ness in the Django
    admin: modeltranslation makes every language column blank=True, so without
    this a snippet could save with no content in any language.

    Raises ImproperlyConfigured if a field listed in translated_required_fields
    was actually blank=True on the original model field, since that would
    force requiredness onto something the model author intended as optional.
    """

    translated_required_fields: tuple[str, ...] = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default = settings.MODELTRANSLATION_DEFAULT_LANGUAGE
        for field_name in self.translated_required_fields:
            default_field = build_localized_fieldname(field_name, default)
            if default_field in self.fields:
                original_field = self._meta.model._meta.get_field(  # noqa: SLF001
                    default_field,
                ).translated_field
                if original_field.blank:
                    msg = (
                        f"{type(self).__name__}.translated_required_fields lists "
                        f"{field_name!r}, but that field is blank=True on "
                        f"{self._meta.model.__name__}. Remove it from "
                        f"translated_required_fields or make the field "
                        "required on the model."
                    )
                    raise ImproperlyConfigured(msg)
                self.fields[default_field].required = True
