from ams.utils.colours import contrast_colour


class TestContrastColor:
    def test_returns_black_for_light_background(self):
        assert contrast_colour("#ffffff") == "#000000"

    def test_returns_white_for_dark_background(self):
        assert contrast_colour("#000000") == "#ffffff"

    def test_returns_empty_for_no_color(self):
        assert contrast_colour("") == ""
