import re

from django import template
from django.template.loader import render_to_string
from django.utils.html import format_html

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
        svg = re.sub(r'(<svg[^>]*class=")([^"]*)"', rf'\1\2 {classes}"', svg, count=1)
    return format_html("{}", svg)
