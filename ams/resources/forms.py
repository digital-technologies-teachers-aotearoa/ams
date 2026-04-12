from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


class ResourceSearchForm(forms.Form):
    q = forms.CharField(
        label=_("Search"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search resources...")}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.form_action = reverse_lazy("resources:search")
        self.helper.layout = Layout(
            "q",
            FormActions(
                Submit("", _("Search"), css_class="btn btn-primary"),
            ),
        )
