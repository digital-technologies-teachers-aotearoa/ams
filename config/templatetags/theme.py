"""Template tags for theme customization."""

from django import template

register = template.Library()


@register.filter
def hex_to_rgb(hex_color):
    """Convert hex color to RGB string for CSS.

    Args:
        hex_color: Hex color string (e.g., "#ffffff" or "#fff")

    Returns:
        String of "r, g, b" format for CSS rgb values
    """
    hex_color = hex_color.lstrip("#")

    # Handle 3-digit hex codes
    if len(hex_color) == 3:  # noqa: PLR2004
        hex_color = "".join([c * 2 for c in hex_color])

    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
