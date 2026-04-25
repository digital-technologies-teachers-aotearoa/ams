_LUMINANCE_THRESHOLD = 0.5


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
