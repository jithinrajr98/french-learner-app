import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.groq_client import get_groq_client
from utils.sentence_parser import load_and_parse_transcripts
from utils.llm_evaluator import evaluate_translation
from utils.audio_generator import play_french_audio

st.set_page_config(
    page_title="French Writing Practice",
    page_icon="📝",
    layout="wide"
)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "sentences": [],
        "current_index": 0,
        "evaluation_result": None,
        "show_result": False,
        "session_stats": {
            "sentences_completed": 0,
            "total_score": 0,
            "critical_errors": 0,
            "minor_errors": 0,
            "perfect_count": 0
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def display_errors(result: dict):
    """Display errors with visual highlighting."""
    critical_errors = result.get("critical_errors", [])
    minor_errors = result.get("minor_errors", [])

    if not critical_errors and not minor_errors:
        st.success("No errors found! Great job!")
        return

    if critical_errors:
        st.markdown("#### Critical Errors")
        for error in critical_errors:
            st.markdown(
                f"""
                <div style="background-color: #ffcccc; padding: 10px;
                            border-left: 4px solid #ff0000; margin: 10px 0;
                            border-radius: 4px;">
                    <strong style="color: #cc0000;">Type: {error.get('type', 'ERROR')}</strong><br>
                    <span style="color: #666;">You wrote:</span>
                    <span style="text-decoration: line-through; color: #cc0000;">
                        {error.get('student_wrote', '')}
                    </span><br>
                    <span style="color: #666;">Should be:</span>
                    <span style="color: #008800; font-weight: bold;">
                        {error.get('original', '')}
                    </span><br>
                    <span style="color: #444; font-style: italic;">
                        {error.get('explanation', '')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

    if minor_errors:
        st.markdown("#### Minor Errors")
        for error in minor_errors:
            st.markdown(
                f"""
                <div style="background-color: #fff3cd; padding: 10px;
                            border-left: 4px solid #ffc107; margin: 10px 0;
                            border-radius: 4px;">
                    <strong style="color: #856404;">Type: {error.get('type', 'ERROR')}</strong><br>
                    <span style="color: #666;">You wrote:</span>
                    <code>{error.get('student_wrote', '')}</code><br>
                    <span style="color: #666;">Should be:</span>
                    <code style="color: #155724;">{error.get('original', '')}</code><br>
                    <span style="color: #444; font-style: italic;">
                        {error.get('explanation', '')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )


init_session_state()

# --- SIDEBAR: Progress & Stats ---
with st.sidebar:
    st.header("Progress")

    if st.session_state.sentences:
        total = len(st.session_state.sentences)
        current = min(st.session_state.current_index + 1, total)
        progress = current / total
        st.progress(progress)
        st.caption(f"Sentence {current} of {total}")
    else:
        st.info("Load transcripts to begin")

    st.divider()
    st.header("Session Stats")

    stats = st.session_state.session_stats
    if stats["sentences_completed"] > 0:
        avg_score = stats["total_score"] / stats["sentences_completed"]
        st.metric("Average Score", f"{avg_score:.1f}%")
        st.metric("Perfect Sentences", stats["perfect_count"])
        st.metric("Critical Errors", stats["critical_errors"])
        st.metric("Minor Errors", stats["minor_errors"])
    else:
        st.caption("Complete sentences to see stats")

    st.divider()
    if st.button("Reset Session", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- MAIN CONTENT ---
st.title("French Writing Practice")
st.write("Translate English sentences into French and get instant feedback.")

# Load transcripts section
if not st.session_state.sentences:
    st.info("Load transcript files to begin practice.")

    # Check if files exist
    french_path = "french_transcript.txt"
    english_path = "english_transcript.txt"

    french_exists = os.path.exists(french_path)
    english_exists = os.path.exists(english_path)

    if not french_exists or not english_exists:
        st.warning("Transcript files not found. Please extract a video from the main page first.")
        if not french_exists:
            st.caption("Missing: french_transcript.txt")
        if not english_exists:
            st.caption("Missing: english_transcript.txt")
    else:
        if st.button("Load Transcripts", type="primary"):
            try:
                aligned = load_and_parse_transcripts(french_path, english_path)

                if aligned:
                    st.session_state.sentences = aligned
                    st.success(f"Loaded {len(aligned)} sentence pairs!")
                    st.rerun()
                else:
                    st.error("Could not parse sentences from transcripts.")

            except Exception as e:
                st.error(f"Error loading transcripts: {str(e)}")

else:
    # --- PRACTICE INTERFACE ---
    sentences = st.session_state.sentences
    idx = st.session_state.current_index

    if idx < len(sentences):
        french_original, english_ref = sentences[idx]

        # Display English prompt
        st.subheader("Translate this sentence to French:")
        st.markdown(f"**{english_ref}**")

        # User input
        user_input = st.text_area(
            "Your French translation:",
            key=f"user_input_{idx}",
            height=100,
            placeholder="Type your French translation here..."
        )

        # Buttons row
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            submit_disabled = not user_input.strip() or st.session_state.show_result
            if st.button("Check Translation", type="primary", disabled=submit_disabled):
                with st.spinner("Evaluating your translation..."):
                    client = get_groq_client()
                    result = evaluate_translation(
                        french_original,
                        english_ref,
                        user_input,
                        client
                    )
                    st.session_state.evaluation_result = result
                    st.session_state.show_result = True

                    # Update stats
                    stats = st.session_state.session_stats
                    stats["sentences_completed"] += 1
                    stats["total_score"] += result.get("overall_score", 0)
                    stats["critical_errors"] += len(result.get("critical_errors", []))
                    stats["minor_errors"] += len(result.get("minor_errors", []))
                    if result.get("overall_score", 0) >= 95:
                        stats["perfect_count"] += 1

                    st.rerun()

        with col2:
            if st.button("Skip Sentence"):
                st.session_state.current_index += 1
                st.session_state.show_result = False
                st.session_state.evaluation_result = None
                st.rerun()

        with col3:
            if st.button("Show Original"):
                st.info(f"**Original French:** {french_original}")

        # --- EVALUATION RESULTS ---
        if st.session_state.show_result and st.session_state.evaluation_result:
            result = st.session_state.evaluation_result

            st.divider()

            # Score display
            score = result.get("overall_score", 0)
            if score >= 90:
                st.success(f"### Score: {score}/100 - Excellent!")
            elif score >= 70:
                st.info(f"### Score: {score}/100 - Good job!")
            elif score >= 50:
                st.warning(f"### Score: {score}/100 - Keep practicing!")
            else:
                st.error(f"### Score: {score}/100 - Needs improvement")

            # Original vs User comparison
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original French:**")
                st.code(french_original, language=None)
                play_french_audio(french_original)
            with col2:
                st.markdown("**Your Translation:**")
                st.code(user_input, language=None)

            # Error highlighting
            display_errors(result)

            # Feedback
            st.markdown("### Feedback")
            st.write(result.get("feedback", ""))

            # Corrected version
            if result.get("corrected_version"):
                st.markdown("**Suggested correction:**")
                st.success(result["corrected_version"])
                play_french_audio(result["corrected_version"])

            # Next button
            if st.button("Next Sentence", type="primary"):
                st.session_state.current_index += 1
                st.session_state.show_result = False
                st.session_state.evaluation_result = None
                st.rerun()

    else:
        # Session complete
        st.balloons()
        st.success("### Congratulations! You've completed all sentences!")

        stats = st.session_state.session_stats
        avg = stats["total_score"] / stats["sentences_completed"] if stats["sentences_completed"] > 0 else 0

        st.markdown(f"""
        **Final Statistics:**
        - Sentences Completed: {stats['sentences_completed']}
        - Average Score: {avg:.1f}%
        - Perfect Sentences: {stats['perfect_count']}
        - Total Critical Errors: {stats['critical_errors']}
        - Total Minor Errors: {stats['minor_errors']}
        """)

        if st.button("Start Over"):
            st.session_state.current_index = 0
            st.session_state.session_stats = {
                "sentences_completed": 0,
                "total_score": 0,
                "critical_errors": 0,
                "minor_errors": 0,
                "perfect_count": 0
            }
            st.rerun()
