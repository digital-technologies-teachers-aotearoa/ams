"""Forms for terms acceptance."""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.utils.translation import gettext_lazy as _


class TermAcceptanceForm(forms.Form):
    """Form for accepting a term version."""

    next = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, term_version=None, **kwargs):
        """Initialize form with term version context."""
        self.term_version = term_version
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "next",
            Submit("submit", _("I Accept"), css_class="btn btn-primary"),
        )
