# TODO — Perplexity Theme Wizard Feature

## Completed

### Phase 1: Core Theme Extraction
- [x] **color_utils.py** — WCAG 2.1 color contrast utilities (hex/RGB conversion, luminance, contrast ratio, lighten/darken, auto-adjustment)
- [x] **perplexity_service.py** — Perplexity API client for AI-powered website theme extraction (branding, colors, fonts, bot identity)
- [x] **assets/__init__.py** — Dynamic CSS override generation + visual theme preview from extracted colors
- [x] **converse.py** — "Theme Wizard" tab added to Gradio UI with run/apply/reset workflow

### Phase 2: Full UI Branding Integration
- [x] **Dynamic page header** — Static `# Agentic RAG: Chat UI` replaced with updatable HTML header supporting logo + branded name
- [x] **Branded header builder** — `build_branded_header()` generates header with favicon logo + "BotName: Agentic RAG" title
- [x] **Generator prompt merging** — `merge_brand_into_generator_prompt()` injects brand personality while preserving RAG instructions (`{question}`, `{context}` variables), supports both Llama3 and Mistral prompt formats
- [x] **Router prompt augmentation** — `merge_brand_into_router_prompt()` adds brand topics to vectorstore routing keywords
- [x] **Intro message injection** — Apply Theme prepends the extracted greeting as the first bot message in the chatbot
- [x] **Input placeholder branding** — Placeholder text changes to "Ask {BotName} anything..."
- [x] **Reset Theme** — Restores header, prompts, chatbot, and placeholder to defaults

### Testing
- [x] **74 unit tests** — All passing. Covers color_utils, perplexity_service (extraction, prompt merging, header building, router merging), and CSS/preview generation

### Routing — Vectorstore-First Design
- [x] **Router prompts (llama3 + mistral)** — Vectorstore is now the default path for all substantive questions; web_search reserved for explicit real-time/current-events queries; router prefers local RAG context before falling back to web search via grade_documents pipeline
- [x] **merge_brand_into_router_prompt** — Updated insertion marker to match new prompt wording, with legacy fallback
- [x] **75 unit tests** — All passing (added legacy marker test)

### Documentation
- [x] **README.md** — Updated with API keys table, Theme Wizard links, architecture diagram, key files reference, and vectorstore-first routing description
- [x] **theme-wizard.md** — Standalone guide covering quick start, extraction details, WCAG accessibility, prompt merging, direct answer routing, file map, configuration, and testing

## Usage

1. Set `PERPLEXITY_API_KEY` environment variable (or enter in the UI)
2. Open the chat UI and navigate to the **Theme Wizard** tab in settings
3. Enter a website URL and click **Run Wizard**
4. Review extracted colors, bot name, intro message, and system prompt
5. (Optional) Enter brand-specific topics for router augmentation
6. Click **Apply Theme** to rebrand the entire UI: colors, header/logo, prompts, chatbot greeting, and input placeholder
7. Click **Reset Theme** to revert everything to the default NVIDIA Kaizen theme
