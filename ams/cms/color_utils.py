# ruff: noqa: PLR2004

"""Pure Python color math utilities for WCAG contrast and theme derivation.

No external dependencies. Implements WCAG 2.1 relative luminance and contrast
ratio calculations for accessible color theming.
"""


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple.

    Accepts 3-digit (#fff) or 6-digit (#ffffff) hex codes, with or without #.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string."""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def relative_luminance(hex_color: str) -> float:
    """Calculate WCAG 2.1 relative luminance of a color.

    See: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    """
    r, g, b = hex_to_rgb(hex_color)
    srgb = []
    for c in (r, g, b):
        c_linear = c / 255.0
        if c_linear <= 0.04045:
            srgb.append(c_linear / 12.92)
        else:
            srgb.append(((c_linear + 0.055) / 1.055) ** 2.4)
    return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2]


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two colors.

    Returns a value between 1:1 and 21:1.
    """
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_rating(ratio: float) -> str:
    """Return WCAG rating for a contrast ratio.

    AAA: >= 7:1
    AA:  >= 4.5:1
    Fail: below 4.5:1
    """
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    return "Fail"


def is_light_background(hex_color: str) -> bool:
    """Return True if the color is perceptually light (luminance > 0.179)."""
    return relative_luminance(hex_color) > 0.179


def auto_theme(hex_color: str) -> str:
    """Return 'light' or 'dark' based on background luminance.

    Returns 'light' for light backgrounds (dark text needed),
    'dark' for dark backgrounds (light text needed).
    """
    return "light" if is_light_background(hex_color) else "dark"


def mix_colors(color1: str, color2: str, weight: float) -> str:
    """Mix two colors together. Weight is the proportion of color1 (0.0 to 1.0).

    mix_colors("#ffffff", "#000000", 0.8) returns 80% white + 20% black.
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    return rgb_to_hex(
        round(r1 * weight + r2 * (1 - weight)),
        round(g1 * weight + g2 * (1 - weight)),
        round(b1 * weight + b2 * (1 - weight)),
    )


def derive_theme_variants(base_color: str) -> dict[str, str]:
    """Derive Bootstrap-compatible theme variants from a single base color.

    Returns:
        dict with keys: bg_subtle, border_subtle, text_emphasis
    """
    return {
        "bg_subtle": mix_colors("#ffffff", base_color, 0.80),
        "border_subtle": mix_colors("#ffffff", base_color, 0.60),
        "text_emphasis": mix_colors("#000000", base_color, 0.40),
    }


def hex_to_rgb_string(hex_color: str) -> str:
    """Convert hex color to CSS RGB string (e.g., '255, 255, 255')."""
    r, g, b = hex_to_rgb(hex_color)
    return f"{r}, {g}, {b}"
