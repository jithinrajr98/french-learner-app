# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (virtual environment at .venv)
uv venv && uv pip install -r requirements.txt && uv pip install pytest

# Run the application
uv run streamlit run app.py

# Run tests
uv run pytest tests/ -v

# Run a single test
uv run pytest tests/test_llm_evaluator.py::TestExtractJson::test_defense_attachment_case -v
```

## Environment Setup

Requires `GROQ_API_KEY` in `.env` file (see `.env.example`).

## Architecture

Multi-page Streamlit application with shared utilities:

**Pages:**
- `app.py` - Main page: extracts French transcripts from YouTube videos and translates to English via Groq API
- `pages/1_Writing_Practice.py` - Practice page: users translate English sentences to French and receive LLM-powered feedback

**Utilities (`utils/`):**
- `groq_client.py` - Singleton Groq client shared across pages
- `sentence_parser.py` - Parses transcripts into sentences, handles French abbreviations and punctuation edge cases
- `llm_evaluator.py` - Evaluates user translations using LLM, extracts JSON from potentially markdown-wrapped responses

**Data Flow:**
1. User provides YouTube URL → French transcript extracted → translated to English → saved to `french_transcript.txt` and `english_transcript.txt`
2. Writing Practice loads these files, parses into sentence pairs, shows English → user inputs French → LLM evaluates and scores

**LLM Integration:**
- Model: `llama-3.3-70b-versatile` via Groq API
- Long texts chunked into 4000-character segments
- JSON responses may be wrapped in markdown code blocks - `extract_json()` handles this
