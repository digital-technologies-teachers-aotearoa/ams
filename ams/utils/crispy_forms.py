from crispy_forms.layout import LayoutObject
from django.template.loader import render_to_string
from django.urls import reverse


class Cancel(LayoutObject):
    """Layout object that displays a cancel button.

    Uses an <a> tag for correct HTML syntax.

    url (str): A URL for the Cancel button link to target.
    """

    TEMPLATE = "utils/crispy_forms/cancel.html"

    def __init__(self, url=None, **kwargs):
        if url:
            self.url = url
        else:
            self.url = reverse("root_redirect")

    def render(self, form, context, **kwargs):
        return render_to_string(
            self.TEMPLATE,
            {
                "url": self.url,
            },
        )


class PricingCardsRadio(LayoutObject):
    """Renders ModelChoiceField as Bootstrap pricing cards with radio buttons.

    Designed for MembershipOption selection with full model data display.

    Args:
        field_name (str): Name of the field to render
        show_org_fields (bool): Show organisation-specific fields
    """

    TEMPLATE = "utils/crispy_forms/card_radio.html"

    def __init__(self, field_name, show_org_fields=False, **kwargs):  # noqa: FBT002
        self.field_name = field_name
        self.show_org_fields = show_org_fields

    def render(self, form, context, **kwargs):
        field = form[self.field_name]
        return render_to_string(
            self.TEMPLATE,
            {
                "field": field,
                "show_org_fields": self.show_org_fields,
            },
        )
