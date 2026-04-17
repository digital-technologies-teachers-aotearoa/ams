from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import LayoutObject
from crispy_forms.layout import Submit
from django import forms
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ams.resources.models import ResourceCategory


class CategoryTagFilters(LayoutObject):
    TEMPLATE = "resources/category_tag_filters.html"

    def render(self, form, context, **kwargs):
        return render_to_string(
            self.TEMPLATE,
            {
                "form": form,
                "selected_tag_slugs": context.get("selected_tag_slugs", set()),
            },
        )


class ResourceSearchForm(forms.Form):
    q = forms.CharField(
        label=_("Search"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search resources...")}),
    )

    def __init__(self, *args, inline=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.categories = ResourceCategory.objects.prefetch_related("tags").all()
        self.helper = FormHelper()
        self.helper.form_method = "get"
        self.helper.form_action = reverse_lazy("resources:search")
        if inline:
            self.helper.form_show_labels = False
            self.helper.layout = Layout(
                Div(
                    Field("q", wrapper_class="flex-grow-1 mb-0"),
                    Submit("", _("Search"), css_class="btn btn-primary"),
                    css_class="d-flex gap-2 align-items-start",
                ),
            )
        else:
            self.helper.layout = Layout(
                "q",
                CategoryTagFilters(),
                FormActions(Submit("", _("Search"), css_class="btn btn-primary w-100")),
            )
