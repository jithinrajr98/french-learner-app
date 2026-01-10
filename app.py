import os
import re
from typing import Optional
from dotenv import load_dotenv
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from groq import Groq

load_dotenv()

st.set_page_config(page_title="French YouTube Translator", page_icon="🇫🇷")


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_french_transcript(video_id: str) -> Optional[str]:
    """Fetch French transcript from YouTube video."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # Try to get French transcript (manual or auto-generated)
        try:
            transcript = transcript_list.find_transcript(['fr'])
        except NoTranscriptFound:
            return None

        transcript_data = transcript.fetch()
        full_text = ' '.join([snippet.text for snippet in transcript_data])
        return full_text

    except TranscriptsDisabled:
        return None
    except Exception:
        return None


def translate_to_english(french_text: str) -> Optional[str]:
    """Translate French text to English using Groq API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY not found in environment variables.")
        return None

    client = Groq(api_key=api_key)

    # Handle long texts by chunking if necessary
    max_chunk_size = 4000
    chunks = [french_text[i:i + max_chunk_size] for i in range(0, len(french_text), max_chunk_size)]

    translated_chunks = []
    for chunk in chunks:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate the following French text to English. Provide only the translation, no explanations."
                },
                {
                    "role": "user",
                    "content": chunk
                }
            ],
            temperature=0.3,
        )
        translated_chunks.append(response.choices[0].message.content)

    return ' '.join(translated_chunks)


def save_transcript(content: str, filename: str) -> None:
    """Save transcript content to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)


# Streamlit UI
st.title("French YouTube Transcript Translator")
st.write("Enter a French YouTube video URL to extract and translate its transcript.")

url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Process Video", type="primary"):
    if not url:
        st.error("Please enter a YouTube URL.")
    else:
        video_id = extract_video_id(url)

        if not video_id:
            st.error("Invalid YouTube URL. Please check the URL and try again.")
        else:
            with st.spinner("Extracting French transcript..."):
                french_text = get_french_transcript(video_id)

            if not french_text:
                st.error("No French transcript available for this video.")
            else:
                save_transcript(french_text, "french_transcript.txt")
                st.success("French transcript extracted and saved!")

                with st.spinner("Translating to English..."):
                    english_text = translate_to_english(french_text)

                if english_text:
                    save_transcript(english_text, "english_transcript.txt")
                    st.success("English translation complete and saved!")

                    with st.expander("French Transcript", expanded=True):
                        st.text_area("", french_text, height=300, key="french")

                    with st.expander("English Translation", expanded=True):
                        st.text_area("", english_text, height=300, key="english")

                    st.info("Files saved: `french_transcript.txt` and `english_transcript.txt`")
                else:
                    st.error("Translation failed. Please check your API key.")
