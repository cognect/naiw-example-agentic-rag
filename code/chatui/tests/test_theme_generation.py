"""Unit tests for chatui.assets theme generation utilities."""

import pytest

from chatui.assets import format_theme_preview, generate_css_overrides
from chatui.perplexity_service import ExtractedTheme


class TestGenerateCssOverrides:
    def test_empty_theme_returns_empty(self):
        theme = ExtractedTheme()
        assert generate_css_overrides(theme) == ""

    def test_primary_only(self):
        theme = ExtractedTheme(primary_color="#6366f1")
        css = generate_css_overrides(theme)
        assert "--button-primary-background-fill: #6366f1" in css
        assert "<style>" in css

    def test_full_theme(self):
        theme = ExtractedTheme(
            primary_color="#6366f1",
            secondary_color="#8b5cf6",
            background_color="#0f0f23",
            surface_color="#1a1a3e",
            text_color="#e2e8f0",
            text_secondary_color="#94a3b8",
            input_background="#151530",
            font_family="Inter",
        )
        css = generate_css_overrides(theme)
        assert "--body-background-fill: #0f0f23" in css
        assert "--body-text-color: #e2e8f0" in css
        assert "--font: 'Inter'" in css
        assert "--link-text-color: #8b5cf6" in css
        assert "--input-background-fill: #151530" in css

    def test_dark_bg_generates_light_border(self):
        theme = ExtractedTheme(background_color="#111111")
        css = generate_css_overrides(theme)
        assert "--border-color-primary" in css

    def test_light_bg_generates_dark_border(self):
        theme = ExtractedTheme(background_color="#f0f0f0")
        css = generate_css_overrides(theme)
        assert "--border-color-primary" in css

    def test_dark_primary_gets_white_text(self):
        theme = ExtractedTheme(primary_color="#1a1a2e")
        css = generate_css_overrides(theme)
        assert "--button-primary-text-color: #ffffff" in css

    def test_light_primary_gets_dark_text(self):
        theme = ExtractedTheme(primary_color="#76b900")
        css = generate_css_overrides(theme)
        assert "--button-primary-text-color: #202020" in css


class TestFormatThemePreview:
    def test_empty_theme(self):
        theme = ExtractedTheme()
        html = format_theme_preview(theme)
        assert "<div" in html

    def test_colors_displayed(self):
        theme = ExtractedTheme(
            primary_color="#ff0000", background_color="#ffffff"
        )
        html = format_theme_preview(theme)
        assert "#ff0000" in html
        assert "#ffffff" in html
        assert "Primary" in html
        assert "Background" in html

    def test_metadata_displayed(self):
        theme = ExtractedTheme(
            bot_name="TestBot",
            font_family="Roboto",
            intro_message="Welcome!",
            logo_url="https://example.com/favicon.ico",
        )
        html = format_theme_preview(theme)
        assert "TestBot" in html
        assert "Roboto" in html
        assert "Welcome!" in html
        assert "favicon.ico" in html
