from typing import Any

from django import template
from django.forms import BoundField

register = template.Library()

invalid_field_class_name = "is-invalid"


def add_class_to_widget(widget: Any, class_name: str) -> None:
    attrs = widget.data["attrs"]
    if "class" in attrs:
        attrs["class"] += f" {class_name}"
    else:
        attrs["class"] = class_name


@register.filter(name="add_form_field_classes")
def add_form_field_classes(field: BoundField) -> Any:
    if not field.subwidgets:
        return field

    widget = field.subwidgets[0]
    attrs = field.subwidgets[0].data["attrs"]

    add_class_to_widget(widget, "form-control")
    if field.errors:
        add_class_to_widget(widget, invalid_field_class_name)

    return field.as_widget(attrs=attrs)
