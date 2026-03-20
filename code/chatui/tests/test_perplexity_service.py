"""Unit tests for chatui.perplexity_service — Perplexity theme extraction."""

import json
from unittest.mock import MagicMock, patch

import pytest

from chatui.perplexity_service import (
    ExtractedTheme,
    ExtractionResult,
    _build_extraction_prompt,
    _ensure_readable_theme,
    build_branded_header,
    extract_website_theme,
    get_favicon_url,
    merge_brand_into_generator_prompt,
    merge_brand_into_router_prompt,
)


class TestGetFaviconUrl:
    def test_standard_url(self):
        url = get_favicon_url("https://nvidia.com")
        assert "nvidia.com" in url
        assert "favicons" in url

    def test_url_with_path(self):
        url = get_favicon_url("https://example.com/page/deep")
        assert "example.com" in url

    def test_invalid_url(self):
        url = get_favicon_url("")
        assert url == ""


class TestEnsureReadableTheme:
    def test_no_background_returns_unchanged(self):
        theme = ExtractedTheme(primary_color="#ff0000")
        result = _ensure_readable_theme(theme)
        assert result.primary_color == "#ff0000"
        assert result.text_color is None

    def test_derives_missing_text_color_dark_bg(self):
        theme = ExtractedTheme(background_color="#1a1a2e")
        result = _ensure_readable_theme(theme)
        assert result.text_color is not None
        assert result.text_color == "#ffffff"

    def test_derives_missing_text_color_light_bg(self):
        theme = ExtractedTheme(background_color="#f0f0f0")
        result = _ensure_readable_theme(theme)
        assert result.text_color is not None

    def test_derives_surface_from_background(self):
        theme = ExtractedTheme(background_color="#0f0f23")
        result = _ensure_readable_theme(theme)
        assert result.surface_color is not None
        assert result.surface_color != result.background_color

    def test_derives_secondary_from_primary(self):
        theme = ExtractedTheme(
            background_color="#ffffff", primary_color="#6366f1"
        )
        result = _ensure_readable_theme(theme)
        assert result.secondary_color is not None

    def test_adjusts_low_contrast_primary(self):
        theme = ExtractedTheme(
            background_color="#111111", primary_color="#222222"
        )
        result = _ensure_readable_theme(theme)
        assert result.primary_color != "#222222"

    def test_preserves_good_contrast(self):
        theme = ExtractedTheme(
            background_color="#ffffff",
            primary_color="#0000ff",
            text_color="#000000",
        )
        result = _ensure_readable_theme(theme)
        assert result.text_color == "#000000"


class TestExtractWebsiteTheme:
    def test_invalid_url(self):
        result = extract_website_theme("not-a-url", "fake-key")
        assert result.success is False
        assert "Invalid URL" in result.error

    def test_missing_api_key(self):
        result = extract_website_theme("https://example.com", "")
        assert result.success is False
        assert "API key" in result.error

    def test_whitespace_api_key(self):
        result = extract_website_theme("https://example.com", "   ")
        assert result.success is False

    @patch("chatui.perplexity_service.requests.post")
    def test_api_error_status(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": {"message": "Unauthorized"}}
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-test123")
        assert result.success is False
        assert "Unauthorized" in result.error

    @patch("chatui.perplexity_service.requests.post")
    def test_successful_extraction(self, mock_post):
        theme_data = {
            "primaryColor": "#6366f1",
            "secondaryColor": "#8b5cf6",
            "backgroundColor": "#0f0f23",
            "surfaceColor": "#1a1a3e",
            "textColor": "#e2e8f0",
            "textSecondaryColor": "#94a3b8",
            "fontFamily": "Inter",
            "botName": "Test Assistant",
            "introMessage": "Hello! How can I help?",
            "systemPrompt": "You are a helpful assistant.",
            "sampleQuestions": [
                "What products do you offer?",
                "How do I contact support?",
                "What are your pricing plans?",
                "Where can I find documentation?",
            ],
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-test123")
        assert result.success is True
        assert result.data is not None
        assert result.data.primary_color is not None
        assert result.data.bot_name == "Test Assistant"
        assert result.data.logo_url is not None
        assert result.data.sample_questions is not None
        assert len(result.data.sample_questions) == 4
        assert result.data.sample_questions[0] == "What products do you offer?"

    @patch("chatui.perplexity_service.requests.post")
    def test_handles_markdown_wrapped_json(self, mock_post):
        theme_data = {"primaryColor": "#ff6d5a", "backgroundColor": "#0f0f23"}
        wrapped = f"```json\n{json.dumps(theme_data)}\n```"

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": wrapped}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert result.data.primary_color is not None

    @patch("chatui.perplexity_service.requests.post")
    def test_no_usable_data(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps({"fontFamily": "Arial"})}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is False
        assert "meaningful" in result.error.lower()

    @patch("chatui.perplexity_service.requests.post")
    def test_invalid_json_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "This is not JSON at all"}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is False
        assert "parse" in result.error.lower()

    @patch("chatui.perplexity_service.requests.post")
    def test_timeout_handling(self, mock_post):
        import requests as req
        mock_post.side_effect = req.Timeout("Connection timed out")

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is False
        assert "timed out" in result.error.lower()

    @patch("chatui.perplexity_service.requests.post")
    def test_empty_choices(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"choices": []}
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is False

    @patch("chatui.perplexity_service.requests.post")
    def test_sample_questions_missing(self, mock_post):
        theme_data = {
            "primaryColor": "#6366f1",
            "backgroundColor": "#0f0f23",
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert result.data.sample_questions is None

    @patch("chatui.perplexity_service.requests.post")
    def test_sample_questions_empty_list(self, mock_post):
        theme_data = {
            "primaryColor": "#6366f1",
            "backgroundColor": "#0f0f23",
            "sampleQuestions": [],
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert result.data.sample_questions is None

    @patch("chatui.perplexity_service.requests.post")
    def test_sample_questions_truncated_to_four(self, mock_post):
        theme_data = {
            "primaryColor": "#6366f1",
            "backgroundColor": "#0f0f23",
            "sampleQuestions": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"],
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert len(result.data.sample_questions) == 4
        assert result.data.sample_questions == ["Q1", "Q2", "Q3", "Q4"]

    @patch("chatui.perplexity_service.requests.post")
    def test_sample_questions_null_from_api(self, mock_post):
        theme_data = {
            "primaryColor": "#6366f1",
            "backgroundColor": "#0f0f23",
            "sampleQuestions": None,
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert result.data.sample_questions is None


class TestMergeBrandIntoGeneratorPrompt:
    LLAMA_PROMPT = (
        '<|begin_of_text|><|start_header_id|>system<|end_header_id|> \n'
        'You are an assistant for question-answering tasks.\n\n'
        '<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n'
        'Question: {question} \nContext: {context} \n\nAnswer: \n\n'
        '<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n'
    )
    MISTRAL_PROMPT = (
        '<s>[INST] You are an assistant for question-answering tasks.\n\n'
        'Question: {question} \nContext: {context} \n\nAnswer: [/INST]\n'
    )

    def test_empty_brand_returns_original(self):
        result = merge_brand_into_generator_prompt(self.LLAMA_PROMPT, "")
        assert result == self.LLAMA_PROMPT

    def test_none_brand_returns_original(self):
        result = merge_brand_into_generator_prompt(self.LLAMA_PROMPT, None)
        assert result == self.LLAMA_PROMPT

    def test_llama_format_preserves_rag_instructions(self):
        brand = "You are Acme Corp's friendly assistant."
        result = merge_brand_into_generator_prompt(self.LLAMA_PROMPT, brand, "Acme Bot")
        assert "Acme Corp" in result
        assert "retrieval-augmented generation" in result
        assert "{question}" in result
        assert "{context}" in result
        assert "<|begin_of_text|>" in result

    def test_mistral_format_preserves_rag_instructions(self):
        brand = "You represent TechCo."
        result = merge_brand_into_generator_prompt(self.MISTRAL_PROMPT, brand)
        assert "TechCo" in result
        assert "retrieval-augmented generation" in result
        assert "{question}" in result
        assert "{context}" in result
        assert "[INST]" in result

    def test_unknown_format_returns_original(self):
        custom = "Custom prompt with {question} and {context}"
        result = merge_brand_into_generator_prompt(custom, "brand stuff")
        assert result == custom


class TestMergeBrandIntoRouterPrompt:
    ROUTER_NEW = (
        'Route user questions. Use vectorstore for NVIDIA topics. '
        'if the question could plausibly be answered by loaded documents, use the vectorstore. '
        'Use web_search only for real-time info. Return JSON with datasource key.'
    )
    ROUTER_LEGACY = (
        'Route user questions. Use vectorstore for NVIDIA topics. '
        'Otherwise, use web-search. Return JSON with datasource key.'
    )

    def test_empty_topics_returns_original(self):
        assert merge_brand_into_router_prompt(self.ROUTER_NEW, "") == self.ROUTER_NEW

    def test_none_topics_returns_original(self):
        assert merge_brand_into_router_prompt(self.ROUTER_NEW, None) == self.ROUTER_NEW

    def test_injects_brand_topics_new_marker(self):
        result = merge_brand_into_router_prompt(self.ROUTER_NEW, "pricing, support")
        assert "pricing, support" in result
        assert "plausibly be answered by loaded documents, use the vectorstore." in result

    def test_injects_brand_topics_legacy_marker(self):
        result = merge_brand_into_router_prompt(self.ROUTER_LEGACY, "pricing, support")
        assert "pricing, support" in result
        assert "Otherwise, use web-search." in result

    def test_no_marker_returns_original(self):
        custom = "Just a prompt without the marker"
        result = merge_brand_into_router_prompt(custom, "topics")
        assert result == custom


class TestBuildBrandedHeader:
    def test_default_header(self):
        html = build_branded_header()
        assert "<h1" in html
        assert "Agentic RAG" in html

    def test_with_bot_name(self):
        html = build_branded_header(bot_name="Acme Bot")
        assert "Acme Bot" in html
        assert "Agentic RAG" in html

    def test_with_logo(self):
        html = build_branded_header(logo_url="https://example.com/logo.png")
        assert '<img src="https://example.com/logo.png"' in html

    def test_no_logo_no_img_tag(self):
        html = build_branded_header(bot_name="Test")
        assert "<img" not in html

    def test_custom_subtitle(self):
        html = build_branded_header(bot_name="Bot", subtitle="Custom Sub")
        assert "Bot: Custom Sub" in html


class TestBuildExtractionPrompt:
    def test_includes_sample_questions_field(self):
        prompt = _build_extraction_prompt("https://example.com")
        assert "sampleQuestions" in prompt

    def test_includes_sample_questions_instructions(self):
        prompt = _build_extraction_prompt("https://example.com")
        assert "4 concise, natural questions" in prompt
        assert "under 60 characters" in prompt

    def test_includes_website_url(self):
        prompt = _build_extraction_prompt("https://nvidia.com")
        assert "https://nvidia.com" in prompt


class TestExtractedThemeSampleQuestions:
    def test_default_sample_questions_is_none(self):
        theme = ExtractedTheme()
        assert theme.sample_questions is None

    def test_sample_questions_round_trip(self):
        questions = ["Q1?", "Q2?", "Q3?", "Q4?"]
        theme = ExtractedTheme(sample_questions=questions)
        assert theme.sample_questions == questions
        assert len(theme.sample_questions) == 4

    @patch("chatui.perplexity_service.requests.post")
    def test_extraction_with_sample_questions_and_theme(self, mock_post):
        """End-to-end: Perplexity returns both theme and sample questions."""
        theme_data = {
            "primaryColor": "#76b900",
            "backgroundColor": "#1a1a2e",
            "botName": "GreenBot",
            "introMessage": "Hello!",
            "systemPrompt": "You are GreenBot.",
            "sampleQuestions": [
                "What GPU should I use?",
                "How do I install drivers?",
                "What is CUDA?",
                "Tell me about TensorRT",
            ],
        }
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(theme_data)}}]
        }
        mock_post.return_value = mock_resp

        result = extract_website_theme("https://example.com", "pplx-key")
        assert result.success is True
        assert result.data.bot_name == "GreenBot"
        assert result.data.sample_questions is not None
        assert len(result.data.sample_questions) == 4
        assert "GPU" in result.data.sample_questions[0]


class TestDatabaseThemeWorkflow:
    """Tests for the clear-then-upload pattern used by the theme wizard."""

    @patch("chatui.utils.database.Chroma")
    @patch("chatui.utils.database.NVIDIAEmbeddings")
    def test_clear_then_upload_pattern(self, mock_embeddings, mock_chroma):
        """Verifies clear + upload can run sequentially without error."""
        from chatui.utils import database

        mock_client = MagicMock()
        mock_chroma.return_value._client = mock_client
        mock_chroma.from_documents.return_value = MagicMock()

        database._clear()
        mock_client.delete_collection.assert_called_once_with(name="rag-chroma")
        mock_client.create_collection.assert_called_once_with(name="rag-chroma")

    @patch("chatui.utils.database.WebBaseLoader")
    @patch("chatui.utils.database.Chroma")
    @patch("chatui.utils.database.NVIDIAEmbeddings")
    def test_upload_single_url(self, mock_embeddings, mock_chroma, mock_loader):
        """Simulates uploading a single branded website URL."""
        from langchain_core.documents import Document
        from chatui.utils import database

        doc = Document(page_content="Welcome to Acme Corp", metadata={"source": "https://acme.com"})
        mock_loader.return_value.load.return_value = [doc]
        mock_chroma.from_documents.return_value = MagicMock()

        result = database.upload(["https://acme.com"])
        assert result is not None
        mock_loader.assert_called_once_with("https://acme.com")

    @patch("chatui.utils.database.WebBaseLoader")
    @patch("chatui.utils.database.Chroma")
    @patch("chatui.utils.database.NVIDIAEmbeddings")
    def test_upload_invalid_url_returns_none(self, mock_embeddings, mock_chroma, mock_loader):
        from chatui.utils import database

        result = database.upload(["not-a-url"])
        assert result is None
        mock_loader.assert_not_called()


class TestDefaultSampleQuestions:
    """Validates the DEFAULT_SAMPLE_QUESTIONS constant used by the wizard textboxes."""

    def test_has_exactly_four(self):
        from chatui.pages.converse import DEFAULT_SAMPLE_QUESTIONS
        assert len(DEFAULT_SAMPLE_QUESTIONS) == 4

    def test_all_non_empty_strings(self):
        from chatui.pages.converse import DEFAULT_SAMPLE_QUESTIONS
        for q in DEFAULT_SAMPLE_QUESTIONS:
            assert isinstance(q, str)
            assert len(q.strip()) > 0

    def test_each_under_80_chars(self):
        from chatui.pages.converse import DEFAULT_SAMPLE_QUESTIONS
        for q in DEFAULT_SAMPLE_QUESTIONS:
            assert len(q) < 80, f"Too long: {q}"
