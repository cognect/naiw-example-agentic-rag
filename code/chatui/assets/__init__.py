# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module contains theming assets and dynamic theme generation."""
import os.path
from typing import TYPE_CHECKING, Tuple

import gradio as gr

from chatui.utils.color_utils import darken_color, is_dark_color, lighten_color

if TYPE_CHECKING:
    from chatui.perplexity_service import ExtractedTheme

_ASSET_DIR = os.path.dirname(__file__)


def load_theme(name: str) -> Tuple[gr.Theme, str]:
    """Load a pre-defined chatui theme.

    :param name: The name of the theme to load.
    :type name: str
    :returns: A tuple containing the Gradio theme and custom CSS.
    :rtype: Tuple[gr.Theme, str]
    """
    theme_json_path = os.path.join(_ASSET_DIR, f"{name}-theme.json")
    theme_css_path = os.path.join(_ASSET_DIR, f"{name}-theme.css")
    return (
        gr.themes.Default().load(theme_json_path),
        open(theme_css_path, encoding="UTF-8").read(),
    )


def generate_css_overrides(theme: "ExtractedTheme") -> str:
    """Generate CSS custom property overrides from an extracted theme.

    Produces a <style> block that overrides Gradio's CSS variables to
    match the extracted website branding. Supports both light and dark
    mode variables.
    """
    rules = []
    bg = theme.background_color
    primary = theme.primary_color
    secondary = theme.secondary_color
    surface = theme.surface_color
    text = theme.text_color
    text_secondary = theme.text_secondary_color
    input_bg = theme.input_background
    font = theme.font_family

    if not (bg or primary):
        return ""

    bg_dark = is_dark_color(bg) if bg else False

    if bg:
        rules.append(f"--body-background-fill: {bg} !important;")
        rules.append(f"--background-fill-primary: {surface or bg} !important;")
        if surface:
            rules.append(f"--background-fill-secondary: {surface} !important;")
            rules.append(f"--block-background-fill: {surface} !important;")

    if text:
        rules.append(f"--body-text-color: {text} !important;")
        rules.append(f"--block-title-text-color: {text} !important;")
    if text_secondary:
        rules.append(f"--body-text-color-subdued: {text_secondary} !important;")

    if primary:
        rules.append(f"--color-accent: {primary} !important;")
        primary_hover = darken_color(primary, 12) if not bg_dark else lighten_color(primary, 12)
        rules.append(f"--button-primary-background-fill: {primary} !important;")
        rules.append(f"--button-primary-background-fill-hover: {primary_hover} !important;")
        rules.append(f"--button-primary-border-color: {primary} !important;")
        rules.append(f"--button-primary-border-color-hover: {primary_hover} !important;")
        btn_text = "#ffffff" if is_dark_color(primary) else "#202020"
        rules.append(f"--button-primary-text-color: {btn_text} !important;")
        rules.append(f"--button-primary-text-color-hover: {btn_text} !important;")
        rules.append(f"--checkbox-background-color-selected: {primary} !important;")
        rules.append(f"--checkbox-border-color-selected: {primary} !important;")
        rules.append(f"--slider-color: {primary} !important;")
        rules.append(f"--loader-color: {primary} !important;")

    if secondary:
        rules.append(f"--link-text-color: {secondary} !important;")
        rules.append(f"--link-text-color-active: {secondary} !important;")
        sec_hover = darken_color(secondary, 15) if not bg_dark else lighten_color(secondary, 15)
        rules.append(f"--link-text-color-hover: {sec_hover} !important;")
        rules.append(f"--input-background-fill-focus: {secondary} !important;")

    if input_bg:
        rules.append(f"--input-background-fill: {input_bg} !important;")

    if bg:
        border = lighten_color(bg, 15) if bg_dark else darken_color(bg, 10)
        rules.append(f"--border-color-primary: {border} !important;")
        rules.append(f"--block-border-color: {border} !important;")
        rules.append(f"--input-border-color: {border} !important;")

    if font:
        rules.append(f"--font: '{font}', ui-sans-serif, system-ui, sans-serif !important;")

    if not rules:
        return ""

    css_block = "\n    ".join(rules)
    return f"<style>\n  :root, .dark {{\n    {css_block}\n  }}\n</style>"


def format_theme_preview(theme: "ExtractedTheme") -> str:
    """Build an HTML preview showing extracted color swatches and metadata."""
    parts = []
    colors = [
        ("Primary", theme.primary_color),
        ("Secondary", theme.secondary_color),
        ("Background", theme.background_color),
        ("Surface", theme.surface_color),
        ("Text", theme.text_color),
        ("Text Secondary", theme.text_secondary_color),
        ("Input Background", theme.input_background),
    ]

    parts.append('<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0;">')
    for label, color in colors:
        if color:
            parts.append(
                f'<div style="text-align:center;">'
                f'<div style="width:48px;height:48px;background:{color};'
                f'border:1px solid #888;border-radius:4px;"></div>'
                f'<small>{label}<br/>{color}</small></div>'
            )
    parts.append("</div>")

    if theme.font_family:
        parts.append(f"<p><strong>Font:</strong> {theme.font_family}</p>")
    if theme.bot_name:
        parts.append(f"<p><strong>Bot Name:</strong> {theme.bot_name}</p>")
    if theme.intro_message:
        parts.append(f"<p><strong>Intro:</strong> {theme.intro_message}</p>")
    if theme.logo_url:
        parts.append(
            f'<p><strong>Favicon:</strong> <img src="{theme.logo_url}" '
            f'width="32" height="32" style="vertical-align:middle;" /></p>'
        )

    return "\n".join(parts)
