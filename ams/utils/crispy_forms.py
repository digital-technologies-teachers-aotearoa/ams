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
