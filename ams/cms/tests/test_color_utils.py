# ruff: noqa: PLR2004

import pytest

from ams.cms.color_utils import auto_theme
from ams.cms.color_utils import contrast_ratio
from ams.cms.color_utils import derive_theme_variants
from ams.cms.color_utils import hex_to_rgb
from ams.cms.color_utils import hex_to_rgb_string
from ams.cms.color_utils import is_light_background
from ams.cms.color_utils import mix_colors
from ams.cms.color_utils import relative_luminance
from ams.cms.color_utils import rgb_to_hex
from ams.cms.color_utils import wcag_rating


class TestHexToRgb:
    def test_black(self):
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_white(self):
        assert hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_red(self):
        assert hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_without_hash(self):
        assert hex_to_rgb("0d6efd") == (13, 110, 253)

    def test_three_digit(self):
        assert hex_to_rgb("#fff") == (255, 255, 255)

    def test_three_digit_color(self):
        assert hex_to_rgb("#f00") == (255, 0, 0)


class TestRgbToHex:
    def test_black(self):
        assert rgb_to_hex(0, 0, 0) == "#000000"

    def test_white(self):
        assert rgb_to_hex(255, 255, 255) == "#ffffff"

    def test_clamps_overflow(self):
        assert rgb_to_hex(300, -10, 128) == "#ff0080"


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance("#000000") == pytest.approx(0.0)

    def test_white(self):
        assert relative_luminance("#ffffff") == pytest.approx(1.0)

    def test_mid_gray(self):
        # #808080 should have ~0.216 luminance
        lum = relative_luminance("#808080")
        assert 0.2 < lum < 0.25


class TestContrastRatio:
    def test_black_white(self):
        ratio = contrast_ratio("#000000", "#ffffff")
        assert ratio == pytest.approx(21.0)

    def test_same_color(self):
        ratio = contrast_ratio("#0d6efd", "#0d6efd")
        assert ratio == pytest.approx(1.0)

    def test_order_independent(self):
        r1 = contrast_ratio("#000000", "#ffffff")
        r2 = contrast_ratio("#ffffff", "#000000")
        assert r1 == pytest.approx(r2)


class TestWcagRating:
    def test_aaa(self):
        assert wcag_rating(7.0) == "AAA"
        assert wcag_rating(10.0) == "AAA"

    def test_aa(self):
        assert wcag_rating(4.5) == "AA"
        assert wcag_rating(6.9) == "AA"

    def test_fail(self):
        assert wcag_rating(4.4) == "Fail"
        assert wcag_rating(1.0) == "Fail"


class TestIsLightBackground:
    def test_white_is_light(self):
        assert is_light_background("#ffffff") is True

    def test_black_is_dark(self):
        assert is_light_background("#000000") is False

    def test_bootstrap_light_gray(self):
        assert is_light_background("#f8f9fa") is True

    def test_bootstrap_dark(self):
        assert is_light_background("#212529") is False


class TestAutoTheme:
    def test_white_returns_light(self):
        assert auto_theme("#ffffff") == "light"

    def test_black_returns_dark(self):
        assert auto_theme("#000000") == "dark"

    def test_dark_blue_returns_dark(self):
        assert auto_theme("#333333") == "dark"

    def test_light_yellow_returns_light(self):
        assert auto_theme("#ffc107") == "light"


class TestMixColors:
    def test_full_weight_first(self):
        assert mix_colors("#ffffff", "#000000", 1.0) == "#ffffff"

    def test_full_weight_second(self):
        assert mix_colors("#ffffff", "#000000", 0.0) == "#000000"

    def test_even_mix(self):
        result = mix_colors("#ffffff", "#000000", 0.5)
        r, g, b = hex_to_rgb(result)
        assert r == 128
        assert g == 128
        assert b == 128


class TestDeriveThemeVariants:
    def test_returns_expected_keys(self):
        variants = derive_theme_variants("#0d6efd")
        assert "bg_subtle" in variants
        assert "border_subtle" in variants
        assert "text_emphasis" in variants

    def test_bg_subtle_is_lighter(self):
        variants = derive_theme_variants("#0d6efd")
        # bg_subtle should be lighter (higher luminance) than base
        assert relative_luminance(variants["bg_subtle"]) > relative_luminance("#0d6efd")

    def test_text_emphasis_is_darker(self):
        variants = derive_theme_variants("#0d6efd")
        # text_emphasis should be darker (lower luminance) than base
        assert relative_luminance(variants["text_emphasis"]) < relative_luminance(
            "#0d6efd",
        )


class TestHexToRgbString:
    def test_white(self):
        assert hex_to_rgb_string("#ffffff") == "255, 255, 255"

    def test_black(self):
        assert hex_to_rgb_string("#000000") == "0, 0, 0"

    def test_color(self):
        assert hex_to_rgb_string("#0d6efd") == "13, 110, 253"
