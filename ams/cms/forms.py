from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.layout import Submit
from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(max_length=255, label=_("Name"))
    email = forms.EmailField(label=_("Email"))
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            "name",
            "email",
            "message",
            Submit(
                "contact_form_submit",
                _("Send message"),
                css_class="btn btn-primary",
            ),
        )
