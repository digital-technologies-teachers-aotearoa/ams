import re

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def icon(name, classes=""):
    """
    Renders an SVG icon inline, injecting extra classes into the <svg> tag.
    Usage: {% icon "arrow-right" "icon-lg text-primary" %}
    """
    icon_template = f"icons/{name}.svg"
    svg = render_to_string(icon_template)
    if classes:
        # Only allow safe class names
        if not re.match(r"^[\w\s-]*$", classes):
            classes = ""
        else:
            svg = re.sub(
                r'(<svg[^>]*class=")([^"]*)"',
                rf'\1\2 {classes}"',
                svg,
                count=1,
            )
    return mark_safe(svg)  # noqa: S308
