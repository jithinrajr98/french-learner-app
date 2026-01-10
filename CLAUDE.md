# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the application
uv run streamlit run app.py
```

## Environment Setup

Requires `GROQ_API_KEY` in `.env` file (see `.env.example`).

## Architecture

Single-file Streamlit application (`app.py`) that:
1. Extracts French transcripts from YouTube videos using `youtube-transcript-api`
2. Translates to English via Groq API (llama-3.3-70b-versatile model)
3. Saves output to `french_transcript.txt` and `english_transcript.txt` (overwritten each run)

Long transcripts are chunked into 4000-character segments for translation.
