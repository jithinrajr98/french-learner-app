import os
from dotenv import load_dotenv
from groq import Groq
import streamlit as st

load_dotenv()

_client = None


def get_groq_client() -> Groq:
    """Get or create singleton Groq client."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("GROQ_API_KEY not found in environment variables.")
            st.stop()
        _client = Groq(api_key=api_key)
    return _client
