# Theme Wizard — AI-Powered White-Labeling

The Theme Wizard uses the [Perplexity Sonar API](https://docs.perplexity.ai/) to analyze any website and extract its branding — colors, fonts, bot personality, sample questions, and more — then applies it to the Agentic RAG chat UI in one click. The wizard also loads the website as a RAG document source so the assistant can answer questions about the brand. All extracted colors are validated against WCAG 2.1 accessibility standards.

## Table of Contents
- [Quick Start](#quick-start)
- [What Gets Extracted](#what-gets-extracted)
- [What Gets Applied](#what-gets-applied)
- [Editable Sample Questions](#editable-sample-questions)
- [RAG Context Integration](#rag-context-integration)
- [How It Works](#how-it-works)
- [WCAG 2.1 Color Accessibility](#wcag-21-color-accessibility)
- [Prompt Merging](#prompt-merging)
- [Direct Answer Routing](#direct-answer-routing)
- [Files and Modules](#files-and-modules)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Caveats](#caveats)

---

## Quick Start

1. **Get a Perplexity API key** from [perplexity.ai](https://www.perplexity.ai/settings/api)
2. **Set the key** — either:
   - Add it as the `PERPLEXITY_API_KEY` environment variable in AI Workbench (recommended), or
   - Paste it directly into the API Key field in the Theme Wizard tab
3. **Open the chat UI** and expand the **Settings** panel on the right
4. **Go to the Theme Wizard tab** (tab 5)
5. **Enter a website URL** (e.g. `https://nvidia.com`) and click **Run Wizard**
6. **Review the results** — the wizard shows extracted colors, bot name, intro message, system prompt, and sample questions
7. **(Optional)** Edit the sample questions, bot name, intro, or system prompt before applying
8. Click **Apply Theme** to rebrand the entire UI, update sample questions, and load the website into RAG context
9. Click **Reset Theme** at any time to revert everything to the default appearance and clear branded context

---

## What Gets Extracted

The Perplexity Sonar model analyzes the target website and returns:

| Field | Description | Example |
|-------|-------------|---------|
| `primaryColor` | Main brand color | `#76b900` |
| `secondaryColor` | Accent/secondary color | `#1a1a2e` |
| `backgroundColor` | Page background | `#000000` |
| `surfaceColor` | Card/container background | `#1a1a2e` |
| `textColor` | Primary text color | `#ffffff` |
| `textSecondaryColor` | Muted/secondary text | `#a0a0a0` |
| `fontFamily` | Primary font family | `NVIDIA Sans` |
| `botName` | A branded assistant name | `NV Assist` |
| `introMessage` | Welcome greeting for the chat | `Welcome! I'm NV Assist, your AI-powered guide...` |
| `systemPrompt` | LLM personality/behavior prompt | `You are NV Assist, an AI assistant for NVIDIA...` |
| `sampleQuestions` | 4 brand-relevant starter questions | `["What GPUs do you offer?", "How do I install CUDA?", ...]` |

A favicon/logo is also retrieved automatically via Google's favicon service.

---

## What Gets Applied

When you click **Apply Theme**, the wizard updates these parts of the UI:

| Component | What Changes |
|-----------|-------------|
| **Page header** | Shows the favicon logo and branded bot name (e.g. "NV Assist: Agentic RAG") |
| **CSS colors** | Background, surface, text, primary, secondary, and input colors are injected as CSS overrides |
| **Font family** | The extracted font is applied to the entire UI |
| **Chat greeting** | The intro message appears as the first bot message in the conversation |
| **Input placeholder** | Changes to "Ask {BotName} anything..." |
| **Sample questions** | The 4 clickable sample question buttons below the chat input are updated to brand-relevant questions |
| **Generator prompt** | The brand personality is merged into the RAG generator system prompt |
| **Router prompt** | Brand-specific topics (if provided) are added to the vectorstore routing keywords |
| **RAG context** | The existing vector store is cleared and the website is scraped and embedded as the new document source |
| **Documents tab** | The URL textbox updates to show the branded website URL |

Clicking **Reset Theme** reverts all of the above to their defaults, clears the vector store, and restores the default NVIDIA doc URLs in the Documents tab.

---

## Editable Sample Questions

The Theme Wizard tab includes 4 editable textboxes for the sample questions displayed below the chat input. There are three ways to manage them:

### 1. Wizard auto-fill
When you click **Run Wizard**, the Perplexity API extracts 4 brand-relevant sample questions and fills the textboxes automatically. You can then edit them before clicking **Apply Theme**.

### 2. Manual editing
You can edit the sample question textboxes at any time — no wizard run required. Click the **Update Sample Questions** button to push your edits to the chat UI immediately, without triggering a full theme apply.

### 3. Apply Theme
Clicking **Apply Theme** reads the current values from the sample question textboxes (whether auto-filled by the wizard or manually edited) and updates the chat buttons.

### 4. Reset
Clicking **Reset Theme** restores both the sample question textboxes and the chat buttons to the built-in defaults:
- "How do I add an integration in the CLI?"
- "How do I fix an inaccessible remote Location?"
- "What are the NVIDIA-provided default base environments?"
- "How do I create a support bundle for troubleshooting?"

---

## RAG Context Integration

The Theme Wizard automatically manages the RAG document context when applying or resetting a theme.

### On Apply Theme
1. The existing vector store (ChromaDB) is **cleared** — all previously loaded documents are removed
2. The wizard **scrapes the website URL** using `WebBaseLoader` from LangChain
3. The scraped content is **chunked and embedded** into ChromaDB using NVIDIA embeddings
4. The **Documents tab** updates to show the branded website URL as the current context source

This means the assistant can immediately answer questions about the brand's website content after applying a theme.

### On Reset Theme
1. The vector store is **cleared** — branded content is removed
2. The **Documents tab** is restored to the default NVIDIA AI Workbench URLs
3. The context is **empty** — click "Add to Context" in the Documents tab to reload the default docs

---

## How It Works

```
 ┌───────────────┐     ┌───────────────────┐     ┌──────────────────┐
 │  User enters  │────→│  Perplexity Sonar  │────→│  Parse JSON +    │
 │  website URL  │     │  analyzes website  │     │  build theme     │
 └───────────────┘     └───────────────────┘     └────────┬─────────┘
                                                          │
                       ┌──────────────────┐               │
                       │  Adjust colors   │←──────────────┘
                       │  for WCAG 2.1    │
                       └────────┬─────────┘
                                │
    ┌───────────────────┬───────┼───────────┬───────────────────┐
    │                   │       │           │                   │
    ▼                   ▼       ▼           ▼                   ▼
┌──────────┐  ┌──────────┐ ┌────────┐ ┌──────────┐  ┌──────────────┐
│  CSS     │  │  Merge   │ │ Update │ │  Sample  │  │ Clear DB +   │
│ overrides│  │ prompts  │ │ header │ │ questions│  │ scrape site  │
│  <style> │  │ gen+rtr  │ │ + chat │ │ buttons  │  │ into ChromaDB│
└──────────┘  └──────────┘ └────────┘ └──────────┘  └──────────────┘
```

### Step-by-step

1. **`extract_website_theme()`** sends the URL to the Perplexity Sonar model with a structured prompt asking for JSON output (including `sampleQuestions`).
2. The raw API response is parsed into an `ExtractedTheme` dataclass (with the new `sample_questions` field).
3. **`_ensure_readable_theme()`** post-processes the colors:
   - Derives missing colors (surface, input background, secondary) from what's available.
   - Validates all text/background pairs against WCAG contrast ratios.
   - Iteratively adjusts colors that fail, falling back to pure white or black if needed.
4. The extracted sample questions populate the editable textboxes in the Theme Wizard tab.
5. **`generate_css_overrides()`** converts the theme into a `<style>` block targeting Gradio's CSS custom properties.
6. **`merge_brand_into_generator_prompt()`** injects the brand personality into the LLM generator prompt while preserving RAG template variables (`{question}`, `{context}`).
7. **`merge_brand_into_router_prompt()`** optionally adds brand-specific topics to the vectorstore routing keywords.
8. **`build_branded_header()`** generates an HTML snippet with the favicon and branded title.
9. **`database._clear()`** wipes the existing ChromaDB collection.
10. **`database.upload()`** scrapes the website via `WebBaseLoader`, chunks the content, and embeds it into ChromaDB.

---

## WCAG 2.1 Color Accessibility

All extracted colors pass through accessibility validation before being applied:

| Check | Minimum Ratio | Applied To |
|-------|--------------|------------|
| Normal text contrast | 4.5:1 | `textColor` vs `backgroundColor`, `surfaceColor`, `inputBackground` |
| Secondary text contrast | 3.0:1 | `textSecondaryColor` vs `backgroundColor`, `surfaceColor` |
| Primary color visibility | 3.0:1 | `primaryColor` vs `backgroundColor` |

The algorithm in `color_utils.py`:
- Converts hex to RGB and calculates relative luminance per the [WCAG 2.1 formula](https://www.w3.org/WAI/GL/wiki/Relative_luminance).
- Computes contrast ratios using `(L1 + 0.05) / (L2 + 0.05)`.
- Iteratively lightens or darkens colors (up to 20 steps) until the target ratio is met.
- Falls back to `#ffffff` or `#000000` if the target cannot be reached.

---

## Prompt Merging

The wizard merges extracted brand personality into the existing RAG prompts without breaking retrieval functionality.

### Generator Prompt

`merge_brand_into_generator_prompt()` replaces the generic system section with the brand personality, then appends the RAG instructions. It detects the prompt format automatically:

- **Llama3 format** — uses `<|begin_of_text|>` / `<|start_header_id|>` markers
- **Mistral format** — uses `<s>[INST]` / `[/INST]` markers

The `{question}` and `{context}` template variables are always preserved so the RAG pipeline continues to work.

### Router Prompt

`merge_brand_into_router_prompt()` inserts brand-specific topics (e.g. "NVIDIA GPUs, CUDA, deep learning") into the vectorstore routing clause. This helps the router direct brand-related questions to the local document store instead of web search.

---

## Direct Answer Routing

When the theme wizard assigns a personality to the assistant, identity questions like "Who are you?" need to be answered from the system prompt rather than from retrieved documents or web search. The agent graph includes a **direct answer** path for this:

```
route_question ──→ direct_answer ──→ direct_generate ──→ END
```

- The **router prompt** (both Llama3 and Mistral) includes `direct_answer` as a third routing option alongside `vectorstore` and `web_search`. The router is instructed to prefer `vectorstore` as the default for all substantive questions — local RAG context is always checked first. `web_search` is reserved for questions that explicitly require real-time information. The vectorstore path has a built-in fallback: if retrieved documents are graded as irrelevant, the pipeline automatically falls back to web search.
- The **`direct_generate` node** uses the generator LLM but provides a special context instructing it to answer from its system prompt identity.
- The edge goes directly to `END`, bypassing hallucination grading — since the answer comes from the system prompt, not from documents.

This prevents the infinite-loop scenario where the hallucination grader rejects identity answers for not being grounded in retrieved content.

---

## Files and Modules

| File | Purpose |
|------|---------|
| `code/chatui/perplexity_service.py` | Perplexity API client, theme + sample questions extraction, prompt merging, header builder |
| `code/chatui/utils/database.py` | ChromaDB vector store — `upload()`, `_clear()`, `get_retriever()`, `WebBaseLoader` integration |
| `code/chatui/utils/color_utils.py` | Hex/RGB conversion, luminance, contrast ratio, lighten/darken, WCAG enforcement |
| `code/chatui/assets/__init__.py` | `generate_css_overrides()` — converts theme to Gradio CSS; `format_theme_preview()` — HTML preview |
| `code/chatui/pages/converse.py` | Theme Wizard tab UI (including editable sample questions), `_run_theme_wizard`, `_apply_theme`, `_update_sample_questions`, `_reset_theme` handlers |
| `code/chatui/prompts/prompts_llama3.py` | Router prompt with `direct_answer` option (Llama3 format) |
| `code/chatui/prompts/prompts_mistral.py` | Router prompt with `direct_answer` option (Mistral format) |
| `code/chatui/utils/graph.py` | `direct_generate` node for identity/conversational answers |
| `code/chatui/utils/compile.py` | Wires `direct_answer → direct_generate → END` in the LangGraph |
| `code/chatui/tests/test_color_utils.py` | Unit tests for color utilities |
| `code/chatui/tests/test_perplexity_service.py` | Unit tests for extraction, sample questions, prompt merging, header building, database workflow |
| `code/chatui/tests/test_theme_generation.py` | Unit tests for CSS override and preview generation |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PERPLEXITY_API_KEY` | For Theme Wizard | API key from [perplexity.ai](https://www.perplexity.ai/settings/api). Can also be entered in the UI. |
| `NVIDIA_API_KEY` | Yes | Required for LLM inference (separate from the wizard). |
| `TAVILY_API_KEY` | Yes | Required for web search in the RAG pipeline. |

### Perplexity Model

The default model is `sonar`. You can change this by modifying `DEFAULT_MODEL` in `perplexity_service.py`. Other options include `sonar-pro` for higher-quality extraction at increased cost.

---

## Running Tests

```bash
cd /project
python3 -m pytest code/chatui/tests/ -v
```

There are 91 tests covering:
- Color conversion, luminance, and contrast ratio calculations
- WCAG contrast enforcement and edge cases (pure white/black fallbacks)
- Perplexity API response parsing and error handling
- Sample questions extraction (missing, empty, null, truncation to 4)
- Extraction prompt validation (includes `sampleQuestions` field and instructions)
- Default sample questions constant validation
- Prompt merging for both Llama3 and Mistral formats
- Router prompt augmentation with brand topics
- Branded header HTML generation
- Database theme workflow (clear + upload pattern, single URL upload)
- CSS override generation and theme preview formatting

---

## Caveats

- **API cost** — Each wizard run makes one Perplexity API call. The `sonar` model is inexpensive but not free.
- **Extraction accuracy** — Results depend on how well Perplexity can analyze the target website. Some sites with heavy JavaScript rendering may yield less accurate colors or sample questions.
- **RAG context replacement** — Applying a theme **clears all existing documents** from the vector store and replaces them with content scraped from the wizard URL. If you had custom documents loaded, you'll need to re-upload them after resetting the theme.
- **Website scraping limits** — `WebBaseLoader` fetches the HTML of the given URL. Sites that rely heavily on JavaScript rendering, require authentication, or block scrapers may yield limited or no RAG content.
- **Font loading** — The extracted font name is applied via CSS `font-family`, but the font file itself is not loaded. If the user's browser doesn't have the font, it falls back to the system default.
- **Session-only** — Applied themes are not persisted across server restarts. The theme lives in Gradio component state for the active session.
- **Single user** — The theme applies to the Gradio session. In a multi-user deployment, each user would need to run the wizard independently.
- **Favicon availability** — The logo is fetched from Google's favicon service, which may not have icons for all websites.
