import colorsys

_LUMINANCE_THRESHOLD = 0.5


def hex_to_hsl(hex_colour: str) -> tuple[float, float, float]:
    """Convert a CSS hex colour to (hue, saturation, lightness), each in [0, 1].

    Thin wrapper over `colorsys.rgb_to_hls`, reordered to the more common HSL
    naming (colorsys uses HLS).
    """
    r, g, b = (
        int(hex_colour[1:3], 16) / 255,
        int(hex_colour[3:5], 16) / 255,
        int(hex_colour[5:7], 16) / 255,
    )
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    return hue, saturation, lightness


def hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    """Convert (hue, saturation, lightness), each in [0, 1], to a CSS hex colour."""
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def darken(hex_colour: str, amount: float = 0.3) -> str:
    """Return *hex_colour* with its lightness reduced by *amount* (clamped at 0)."""
    hue, saturation, lightness = hex_to_hsl(hex_colour)
    return hsl_to_hex(hue, saturation, max(lightness - amount, 0.0))


def interpolate_colour(start_colour: str, end_colour: str, position: float) -> str:
    """Return the hex colour *position* of the way from *start_colour* to *end_colour*.

    Linear interpolation per RGB channel. *position* is clamped to [0, 1], so
    0 returns *start_colour* and 1 returns *end_colour* exactly. Used to build a
    sequential gradient across a category's tags — e.g. lightest to darkest for
    an ordered set like year levels, or yellow to red for an ascending numeric
    scale — driven by each tag's position in the category's existing display
    order, with no state stored per tag.
    """
    position = min(max(position, 0.0), 1.0)
    start_r, start_g, start_b = (
        int(start_colour[1:3], 16),
        int(start_colour[3:5], 16),
        int(start_colour[5:7], 16),
    )
    end_r, end_g, end_b = (
        int(end_colour[1:3], 16),
        int(end_colour[3:5], 16),
        int(end_colour[5:7], 16),
    )
    r = round(start_r + (end_r - start_r) * position)
    g = round(start_g + (end_g - start_g) * position)
    b = round(start_b + (end_b - start_b) * position)
    return f"#{r:02x}{g:02x}{b:02x}"


def contrast_colour(hex_colour: str) -> str:
    """Return the highest-contrast foreground colour for a given background colour.

    Uses a simplified perceived-luminance formula (ITU-R BT.601 coefficients) to weight
    the red, green, and blue channels according to human colour sensitivity, then picks
    black or white text depending on which side of the midpoint the result falls on.

    Args:
        hex_colour: A CSS hex colour string in the form #rrggbb (e.g. "#3a86ff").
            Pass an empty string when no colour has been set.

    Returns:
        "#000000" (black) when the background is light enough that dark text is more
        readable; "#ffffff" (white) when the background is dark enough that light text
        is more readable; or "" when *hex_colour* is empty.

    Example::

        contrast_colour("#ffffff")  # → "#000000"  (black on white)
        contrast_colour("#000000")  # → "#ffffff"  (white on black)
        contrast_colour("")         # → ""          (no colour set)
    """
    if not hex_colour:
        return ""
    r, g, b = (
        int(hex_colour[1:3], 16),
        int(hex_colour[3:5], 16),
        int(hex_colour[5:7], 16),
    )
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > _LUMINANCE_THRESHOLD else "#ffffff"
