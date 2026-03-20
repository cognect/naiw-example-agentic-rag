"""WCAG 2.1 compliant color contrast utilities for theme validation.

Ported from the n8n_chat_ux perplexityService.ts color utilities.
Provides hex/RGB conversion, luminance calculation, contrast ratio
checking, and color lightening/darkening to meet accessibility standards.
"""

import math
import re
from typing import Optional, Tuple


def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """Convert a hex color string to an (R, G, B) tuple."""
    match = re.match(r"^#?([a-fA-F\d]{2})([a-fA-F\d]{2})([a-fA-F\d]{2})$", hex_color)
    if not match:
        return None
    return (int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16))


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """Convert RGB values (0-255) to a hex color string."""
    ri = max(0, min(255, round(r)))
    gi = max(0, min(255, round(g)))
    bi = max(0, min(255, round(b)))
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def get_relative_luminance(hex_color: str) -> float:
    """Calculate relative luminance per WCAG 2.1.

    Reference: https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return 0.0
    channels = []
    for c in rgb:
        s = c / 255
        channels.append(
            s / 12.92 if s <= 0.03928 else math.pow((s + 0.055) / 1.055, 2.4)
        )
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def get_contrast_ratio(color1: str, color2: str) -> float:
    """Calculate contrast ratio between two colors.

    WCAG recommends 4.5:1 for normal text, 3:1 for large text.
    """
    l1 = get_relative_luminance(color1)
    l2 = get_relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_dark_color(hex_color: str) -> bool:
    """Return True if the color is considered dark (luminance < 0.179)."""
    return get_relative_luminance(hex_color) < 0.179


def lighten_color(hex_color: str, percent: float) -> str:
    """Lighten a color by the given percentage (0-100)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return hex_color
    factor = percent / 100
    return rgb_to_hex(
        rgb[0] + (255 - rgb[0]) * factor,
        rgb[1] + (255 - rgb[1]) * factor,
        rgb[2] + (255 - rgb[2]) * factor,
    )


def darken_color(hex_color: str, percent: float) -> str:
    """Darken a color by the given percentage (0-100)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return hex_color
    factor = 1 - (percent / 100)
    return rgb_to_hex(
        rgb[0] * factor,
        rgb[1] * factor,
        rgb[2] * factor,
    )


def ensure_text_contrast(
    text_color: str, background_color: str, min_contrast: float = 4.5
) -> str:
    """Ensure text has sufficient contrast against a background.

    Iteratively adjusts the text color. Falls back to pure white/black
    if the target contrast cannot be reached in 20 iterations.
    """
    contrast = get_contrast_ratio(text_color, background_color)
    if contrast >= min_contrast:
        return text_color

    bg_is_dark = is_dark_color(background_color)
    adjusted = text_color
    for _ in range(20):
        adjusted = lighten_color(adjusted, 10) if bg_is_dark else darken_color(adjusted, 10)
        contrast = get_contrast_ratio(adjusted, background_color)
        if contrast >= min_contrast:
            return adjusted

    return "#ffffff" if bg_is_dark else "#000000"
