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

### Phase 3: Dynamic Sample Questions
- [x] **ExtractedTheme.sample_questions** — Added `sample_questions` field to dataclass; Perplexity prompt now requests 4 brand-relevant sample questions
- [x] **converse.py sample buttons** — Sample question buttons update dynamically when theme is applied; reset restores defaults
- [x] **Wizard event wiring** — `wizard_sample_questions` state flows through run → apply → reset lifecycle

### Phase 4: RAG Context Integration
- [x] **Apply Theme loads website into RAG** — `_apply_theme` clears existing vector store, scrapes the wizard website URL via `WebBaseLoader`, embeds into ChromaDB, and updates the Documents tab to reflect the new context
- [x] **Reset Theme clears context** — `_reset_theme` clears the vector store and restores the default NVIDIA doc URLs in the Documents tab; user can re-ingest defaults via "Add to Context"
- [x] **Documents tab sync** — URL textbox, upload/clear buttons all stay in sync with apply/reset lifecycle

### Phase 5: Editable Sample Questions UI
- [x] **Editable textboxes in Theme Wizard** — 4 `gr.Textbox` fields in the Theme Wizard tab, pre-filled with defaults, editable anytime
- [x] **Update Sample Questions button** — Standalone button applies edited questions to chat buttons without requiring full theme apply
- [x] **Wizard auto-fills textboxes** — `_run_theme_wizard` populates the textboxes with Perplexity-extracted questions
- [x] **Apply Theme reads textboxes** — `_apply_theme` uses the current textbox values (user edits respected)
- [x] **Reset Theme restores textbox defaults** — `_reset_theme` resets both the chat buttons and the wizard textboxes to `DEFAULT_SAMPLE_QUESTIONS`

### Testing
- [x] **91 unit tests** — All passing. Covers color_utils, perplexity_service (extraction, sample questions parsing, prompt merging, header building, router merging), database theme workflow (clear + upload pattern), default sample questions validation, and CSS/preview generation

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
4. Review extracted colors, bot name, intro message, system prompt, and sample questions
5. (Optional) Edit the sample questions in the textboxes before applying
6. (Optional) Enter brand-specific topics for router augmentation
7. Click **Apply Theme** to rebrand the entire UI: colors, header/logo, prompts, chatbot greeting, input placeholder, sample questions, and RAG context (website scraped into ChromaDB)
8. To update just sample questions without a full theme apply, edit the textboxes and click **Update Sample Questions**
9. Click **Reset Theme** to revert everything to defaults, clear the vector store, and restore default NVIDIA doc URLs
