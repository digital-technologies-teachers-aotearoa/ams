from ams.utils.colours import contrast_colour
from ams.utils.colours import darken
from ams.utils.colours import hex_to_hsl
from ams.utils.colours import hsl_to_hex
from ams.utils.colours import interpolate_colour


class TestContrastColor:
    def test_returns_black_for_light_background(self):
        assert contrast_colour("#ffffff") == "#000000"

    def test_returns_white_for_dark_background(self):
        assert contrast_colour("#000000") == "#ffffff"

    def test_returns_empty_for_no_color(self):
        assert contrast_colour("") == ""


class TestHexHslRoundTrip:
    def test_white_round_trips(self):
        h, s, lightness = hex_to_hsl("#ffffff")
        assert hsl_to_hex(h, s, lightness) == "#ffffff"

    def test_black_round_trips(self):
        h, s, lightness = hex_to_hsl("#000000")
        assert hsl_to_hex(h, s, lightness) == "#000000"

    def test_arbitrary_colour_round_trips(self):
        h, s, lightness = hex_to_hsl("#3a86ff")
        assert hsl_to_hex(h, s, lightness) == "#3a86ff"


class TestDarken:
    def test_reduces_lightness(self):
        _, _, original_l = hex_to_hsl("#3a86ff")
        _, _, darkened_l = hex_to_hsl(darken("#3a86ff"))
        assert darkened_l < original_l

    def test_clamps_at_black(self):
        assert darken("#000000") == "#000000"


class TestInterpolateColour:
    def test_position_zero_returns_start_colour(self):
        assert interpolate_colour("#ffff00", "#ff0000", 0) == "#ffff00"

    def test_position_one_returns_end_colour(self):
        assert interpolate_colour("#ffff00", "#ff0000", 1) == "#ff0000"

    def test_midpoint_is_between_start_and_end(self):
        assert interpolate_colour("#000000", "#ffffff", 0.5) == "#808080"

    def test_deterministic_for_same_inputs(self):
        first = interpolate_colour("#3a86ff", "#ff006e", 0.4)
        second = interpolate_colour("#3a86ff", "#ff006e", 0.4)
        assert first == second

    def test_same_start_and_end_returns_that_colour_at_any_position(self):
        assert interpolate_colour("#3a86ff", "#3a86ff", 0.7) == "#3a86ff"

    def test_position_below_zero_clamps_to_start(self):
        assert interpolate_colour("#ffff00", "#ff0000", -0.5) == "#ffff00"

    def test_position_above_one_clamps_to_end(self):
        assert interpolate_colour("#ffff00", "#ff0000", 1.5) == "#ff0000"
