from typing import Any

from django import template
from django.forms import BoundField

register = template.Library()

invalid_field_class_name = "is-invalid"


@register.filter(name="add_invalid_field_class")
def add_invalid_field_class(field: BoundField) -> Any:
    attrs = field.subwidgets[0].data["attrs"]
    if field.errors:
        if "class" in attrs:
            attrs["class"] += f" {invalid_field_class_name}"
        else:
            attrs["class"] = invalid_field_class_name

    return field.as_widget(attrs=attrs)
