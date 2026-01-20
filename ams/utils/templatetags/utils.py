"""Template tags for custom widgets."""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if not dictionary:
        return ""
    return dictionary.get(key, "")
