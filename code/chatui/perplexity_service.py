"""Perplexity API service for AI-powered website theme extraction.

Calls the Perplexity Sonar model to analyze a website URL and extract
branding colors, fonts, bot name, intro message, and system prompt.
Applies WCAG 2.1 contrast validation to ensure readable themes.

Ported from cognect/n8n_chat_ux perplexityService.ts.
"""

import json
import logging
import os
from dataclasses import dataclass, replace
from typing import Optional
from urllib.parse import urlparse

import requests

from chatui.utils.color_utils import (
    darken_color,
    ensure_text_contrast,
    get_contrast_ratio,
    is_dark_color,
    lighten_color,
)

_LOGGER = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"


@dataclass
class ExtractedTheme:
    """Theme data extracted from a website via Perplexity."""

    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    background_color: Optional[str] = None
    surface_color: Optional[str] = None
    text_color: Optional[str] = None
    text_secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    bot_name: Optional[str] = None
    input_background: Optional[str] = None
    intro_message: Optional[str] = None
    system_prompt: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result wrapper for theme extraction attempts."""

    success: bool
    data: Optional[ExtractedTheme] = None
    error: Optional[str] = None


def get_favicon_url(website_url: str) -> str:
    """Generate a favicon URL using Google's favicon service."""
    try:
        parsed = urlparse(website_url)
        if not parsed.hostname:
            return ""
        return f"https://www.google.com/s2/favicons?domain={parsed.hostname}&sz=128"
    except Exception:
        return ""


def _build_extraction_prompt(website_url: str) -> str:
    return (
        f"Analyze the website at {website_url} and extract its color scheme, "
        "branding, and create appropriate AI assistant messaging. Return ONLY a "
        "valid JSON object (no markdown, no explanation) with the following structure:\n\n"
        "{\n"
        '  "primaryColor": "main brand color in hex format (e.g., #6366f1)",\n'
        '  "secondaryColor": "secondary/accent brand color in hex format",\n'
        '  "backgroundColor": "main page background color in hex format",\n'
        '  "surfaceColor": "card/container background color in hex format",\n'
        '  "textColor": "main text color in hex format",\n'
        '  "textSecondaryColor": "secondary/muted text color in hex format",\n'
        '  "fontFamily": "primary font family name (just the font name, e.g., \'Inter\')",\n'
        '  "botName": "a friendly assistant name based on the brand",\n'
        '  "introMessage": "a welcoming intro message incorporating the brand personality (1-2 sentences)",\n'
        '  "systemPrompt": "a professional system prompt defining the assistant role, personality, '
        'and behavior based on the brand (3-5 sentences)"\n'
        "}\n\n"
        "For introMessage, make it friendly and aligned with the brand's voice.\n"
        "For systemPrompt, include: the assistant's role, the brand context, "
        "communication style, and key behaviors.\n\n"
        "If you cannot determine a value, use null for that field. "
        "Focus on extracting the dominant brand colors visible on the website."
    )


def _ensure_readable_theme(theme: ExtractedTheme) -> ExtractedTheme:
    """Validate and adjust extracted theme colors for WCAG readability.

    Derives missing colors from available ones, then ensures all text
    colors meet minimum contrast requirements against their backgrounds.
    """
    if not theme.background_color:
        return theme

    bg = theme.background_color
    bg_dark = is_dark_color(bg)
    updates = {}

    text = theme.text_color or ("#ffffff" if bg_dark else "#1a1a2e")
    updates["text_color"] = text

    updates["text_secondary_color"] = theme.text_secondary_color or (
        darken_color(text, 35) if bg_dark else lighten_color(text, 35)
    )

    surface = theme.surface_color or (
        lighten_color(bg, 8) if bg_dark else darken_color(bg, 5)
    )
    updates["surface_color"] = surface

    updates["input_background"] = theme.input_background or (
        darken_color(surface, 15) if bg_dark else lighten_color(surface, 5)
    )

    primary = theme.primary_color
    secondary = theme.secondary_color
    if not secondary and primary:
        secondary = lighten_color(primary, 15) if bg_dark else darken_color(primary, 15)
        updates["secondary_color"] = secondary

    # --- Ensure WCAG contrast ---
    text = ensure_text_contrast(updates["text_color"], bg, 4.5)
    if get_contrast_ratio(text, surface) < 4.5:
        text = ensure_text_contrast(text, surface, 4.5)
    input_bg = updates["input_background"]
    if input_bg and get_contrast_ratio(text, input_bg) < 4.5:
        text = ensure_text_contrast(text, input_bg, 4.5)
    updates["text_color"] = text

    ts = ensure_text_contrast(updates["text_secondary_color"], bg, 3.0)
    if get_contrast_ratio(ts, surface) < 3.0:
        ts = ensure_text_contrast(ts, surface, 3.0)
    updates["text_secondary_color"] = ts

    if primary and get_contrast_ratio(primary, bg) < 3.0:
        primary = lighten_color(primary, 25) if bg_dark else darken_color(primary, 25)
        updates["primary_color"] = primary
        if secondary:
            updates["secondary_color"] = (
                lighten_color(primary, 15) if bg_dark else darken_color(primary, 15)
            )

    return replace(theme, **{k: v for k, v in updates.items() if v is not None})


def get_api_key() -> Optional[str]:
    """Retrieve Perplexity API key from environment variable."""
    return os.environ.get("PERPLEXITY_API_KEY")


def extract_website_theme(
    website_url: str,
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> ExtractionResult:
    """Extract theme and branding from a website URL using Perplexity API.

    Args:
        website_url: Full URL of the website to analyze.
        api_key: Perplexity API key.
        model: Perplexity model to use (default: sonar).

    Returns:
        ExtractionResult with extracted theme data or error details.
    """
    try:
        parsed = urlparse(website_url)
        if not parsed.scheme or not parsed.hostname:
            return ExtractionResult(
                success=False,
                error="Invalid URL format. Please enter a valid website URL (e.g. https://example.com).",
            )
    except Exception:
        return ExtractionResult(
            success=False, error="Invalid URL format."
        )

    if not api_key or not api_key.strip():
        return ExtractionResult(
            success=False,
            error="Perplexity API key is required. Set PERPLEXITY_API_KEY env var or enter it in the UI.",
        )

    try:
        response = requests.post(
            PERPLEXITY_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a web design analyst. You analyze websites and "
                            "extract their branding, color schemes, and visual identity. "
                            "Always respond with valid JSON only, no additional text or "
                            "markdown formatting."
                        ),
                    },
                    {
                        "role": "user",
                        "content": _build_extraction_prompt(website_url),
                    },
                ],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            timeout=60,
        )

        if not response.ok:
            try:
                error_data = response.json()
            except Exception:
                error_data = {}
            error_msg = (
                error_data.get("error", {}).get("message")
                or f"API request failed with status {response.status_code}"
            )
            return ExtractionResult(success=False, error=error_msg)

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content")

        if not content:
            return ExtractionResult(
                success=False, error="No content received from Perplexity API"
            )

        clean = content.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        extracted = json.loads(clean)

        theme = ExtractedTheme(
            primary_color=extracted.get("primaryColor"),
            secondary_color=extracted.get("secondaryColor"),
            background_color=extracted.get("backgroundColor"),
            surface_color=extracted.get("surfaceColor"),
            text_color=extracted.get("textColor"),
            text_secondary_color=extracted.get("textSecondaryColor"),
            font_family=extracted.get("fontFamily"),
            bot_name=extracted.get("botName"),
            input_background=extracted.get("inputBackground"),
            intro_message=extracted.get("introMessage"),
            system_prompt=extracted.get("systemPrompt"),
        )

        if not (theme.primary_color or theme.background_color or theme.secondary_color):
            return ExtractionResult(
                success=False,
                error="Could not extract meaningful theme data from the website",
            )

        theme.logo_url = get_favicon_url(website_url)
        theme = _ensure_readable_theme(theme)
        return ExtractionResult(success=True, data=theme)

    except json.JSONDecodeError:
        _LOGGER.error("Failed to parse Perplexity response: %s", content if 'content' in dir() else "N/A")
        return ExtractionResult(
            success=False, error="Failed to parse theme data from API response"
        )
    except requests.Timeout:
        return ExtractionResult(
            success=False, error="Request timed out. Please try again."
        )
    except Exception as e:
        _LOGGER.error("Perplexity API error: %s", str(e))
        return ExtractionResult(success=False, error=str(e))


def merge_brand_into_generator_prompt(
    original_prompt: str, brand_system_prompt: str, bot_name: Optional[str] = None
) -> str:
    """Merge extracted brand personality into the generator prompt.

    Replaces the generic assistant identity in the generator system section
    with the brand-specific personality while preserving RAG instructions,
    the user/assistant turn structure, and template variables ({question}, {context}).
    """
    if not brand_system_prompt:
        return original_prompt

    identity = bot_name or "a branded assistant"
    rag_addendum = (
        "Additionally, you have retrieval-augmented generation (RAG) capabilities. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, just say that you don't know. "
        "Use five sentences maximum and keep the answer concise but helpful."
    )

    merged_system = f"{brand_system_prompt}\n\n{rag_addendum}"

    if "<|begin_of_text|>" in original_prompt:
        return (
            "<|begin_of_text|><|start_header_id|>system<|end_header_id|> \n"
            f"{merged_system}\n\n"
            "<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
            "Question: {question} \nContext: {context} \n\nAnswer: \n\n"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
        )
    elif "<s>[INST]" in original_prompt:
        return (
            f"<s>[INST] {merged_system}\n\n"
            "Question: {question} \nContext: {context} \n\nAnswer: [/INST]\n"
        )
    return original_prompt


def merge_brand_into_router_prompt(
    original_prompt: str, brand_topics: Optional[str] = None
) -> str:
    """Inject brand context into the router prompt.

    Adds brand-related topic keywords to the vectorstore routing list
    while keeping the existing routing logic and format intact.
    """
    if not brand_topics:
        return original_prompt
    brand_clause = (
        f" Also use the vectorstore for questions related to: {brand_topics}."
    )
    markers = [
        "if the question could plausibly be answered by loaded documents, use the vectorstore.",
        "Otherwise, use web-search.",
    ]
    for marker in markers:
        if marker in original_prompt:
            return original_prompt.replace(marker, f"{marker}{brand_clause}")
    return original_prompt


def build_branded_header(
    bot_name: Optional[str] = None,
    logo_url: Optional[str] = None,
    subtitle: str = "Agentic RAG",
) -> str:
    """Build an HTML header with logo and branded name."""
    parts = ['<div style="display:flex;align-items:center;gap:12px;padding:4px 0;">']
    if logo_url:
        parts.append(
            f'<img src="{logo_url}" width="40" height="40" '
            f'style="border-radius:6px;object-fit:contain;" alt="logo" />'
        )
    title = f"{bot_name}: {subtitle}" if bot_name else subtitle
    parts.append(f'<h1 style="margin:0;font-size:1.6rem;">{title}</h1>')
    parts.append("</div>")
    return "".join(parts)
