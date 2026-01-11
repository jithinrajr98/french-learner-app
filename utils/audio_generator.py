"""Audio generation utilities for French text-to-speech."""

import io
from gtts import gTTS
import streamlit as st


def play_french_audio(text: str) -> bool:
    """
    Generate and play audio for French text.

    Args:
        text: French text to convert to speech

    Returns:
        True if audio played successfully, False otherwise
    """
    if not text or not text.strip():
        return False

    try:
        tts = gTTS(text=text, lang='fr', slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format='audio/mp3')
        return True
    except Exception as e:
        st.caption(f"Audio unavailable: {e}")
        return False
