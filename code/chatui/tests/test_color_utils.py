"""Unit tests for chatui.utils.color_utils — WCAG color utilities."""

import pytest

from chatui.utils.color_utils import (
    darken_color,
    ensure_text_contrast,
    get_contrast_ratio,
    get_relative_luminance,
    hex_to_rgb,
    is_dark_color,
    lighten_color,
    rgb_to_hex,
)


class TestHexToRgb:
    def test_standard_hex(self):
        assert hex_to_rgb("#ff0000") == (255, 0, 0)
        assert hex_to_rgb("#00ff00") == (0, 255, 0)
        assert hex_to_rgb("#0000ff") == (0, 0, 255)

    def test_without_hash(self):
        assert hex_to_rgb("ff0000") == (255, 0, 0)

    def test_mixed_case(self):
        assert hex_to_rgb("#aAbBcC") == (170, 187, 204)

    def test_black_white(self):
        assert hex_to_rgb("#000000") == (0, 0, 0)
        assert hex_to_rgb("#ffffff") == (255, 255, 255)

    def test_invalid_returns_none(self):
        assert hex_to_rgb("not-a-color") is None
        assert hex_to_rgb("#fff") is None  # 3-char shorthand not supported
        assert hex_to_rgb("") is None


class TestRgbToHex:
    def test_standard_values(self):
        assert rgb_to_hex(255, 0, 0) == "#ff0000"
        assert rgb_to_hex(0, 255, 0) == "#00ff00"
        assert rgb_to_hex(0, 0, 255) == "#0000ff"

    def test_clamping(self):
        assert rgb_to_hex(300, -10, 128) == "#ff0080"

    def test_rounding(self):
        assert rgb_to_hex(127.6, 0.4, 255.9) == "#8000ff"


class TestRelativeLuminance:
    def test_white_luminance(self):
        assert get_relative_luminance("#ffffff") == pytest.approx(1.0, abs=0.01)

    def test_black_luminance(self):
        assert get_relative_luminance("#000000") == pytest.approx(0.0, abs=0.001)

    def test_invalid_color(self):
        assert get_relative_luminance("invalid") == 0.0

    def test_mid_gray(self):
        lum = get_relative_luminance("#808080")
        assert 0.15 < lum < 0.25


class TestContrastRatio:
    def test_black_on_white(self):
        ratio = get_contrast_ratio("#000000", "#ffffff")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_same_color(self):
        ratio = get_contrast_ratio("#808080", "#808080")
        assert ratio == pytest.approx(1.0, abs=0.01)

    def test_symmetry(self):
        r1 = get_contrast_ratio("#ff0000", "#0000ff")
        r2 = get_contrast_ratio("#0000ff", "#ff0000")
        assert r1 == pytest.approx(r2, abs=0.01)


class TestIsDarkColor:
    def test_black_is_dark(self):
        assert is_dark_color("#000000") is True

    def test_white_is_not_dark(self):
        assert is_dark_color("#ffffff") is False

    def test_nvidia_green_is_not_dark(self):
        assert is_dark_color("#76b900") is False

    def test_dark_blue(self):
        assert is_dark_color("#0f0f23") is True


class TestLightenColor:
    def test_lighten_black(self):
        result = lighten_color("#000000", 50)
        rgb = hex_to_rgb(result)
        assert rgb is not None
        assert all(c > 100 for c in rgb)

    def test_lighten_by_zero(self):
        assert lighten_color("#808080", 0) == "#808080"

    def test_lighten_invalid(self):
        assert lighten_color("invalid", 50) == "invalid"


class TestDarkenColor:
    def test_darken_white(self):
        result = darken_color("#ffffff", 50)
        rgb = hex_to_rgb(result)
        assert rgb is not None
        assert all(c < 140 for c in rgb)

    def test_darken_by_zero(self):
        assert darken_color("#808080", 0) == "#808080"

    def test_darken_invalid(self):
        assert darken_color("invalid", 50) == "invalid"


class TestEnsureTextContrast:
    def test_already_sufficient(self):
        result = ensure_text_contrast("#000000", "#ffffff", 4.5)
        assert result == "#000000"

    def test_adjusts_low_contrast(self):
        result = ensure_text_contrast("#888888", "#999999", 4.5)
        ratio = get_contrast_ratio(result, "#999999")
        assert ratio >= 4.5

    def test_dark_bg_returns_light_text(self):
        result = ensure_text_contrast("#333333", "#111111", 4.5)
        ratio = get_contrast_ratio(result, "#111111")
        assert ratio >= 4.5

    def test_light_bg_returns_dark_text(self):
        result = ensure_text_contrast("#cccccc", "#eeeeee", 4.5)
        lum = get_relative_luminance(result)
        assert lum < 0.3

    def test_fallback_to_white_on_black(self):
        result = ensure_text_contrast("#010101", "#000000", 4.5)
        ratio = get_contrast_ratio(result, "#000000")
        assert ratio >= 4.5
