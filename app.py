import os
import subprocess
import streamlit as st
from dotenv import load_dotenv
from core.audio_processor import process_input, cleanup_audio_files
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, stream_answer

load_dotenv()

st.set_page_config(page_title="Briefly AI", layout="wide")

SAMPLE_AUDIO_PATH = os.path.join("samples", "sample_meeting.mp3")


def ensure_sample_exists():
    """Ensure bundled demo meeting audio exists; auto-generate if missing."""
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        generator_script = os.path.join("samples", "generate_sample.py")
        if os.path.exists(generator_script):
            try:
                subprocess.run(["python", generator_script], check=True)
            except Exception as e:
                print(f"Warning: Could not auto-generate sample meeting: {e}")


def run_pipeline(source: str, language: str = "english", is_sample: bool = False) -> dict:
    chunks, temp_files = process_input(source, is_persistent_sample=is_sample)
    try:
        transcript = transcribe_all(chunks, language)
        title = generate_title(transcript)
        summary = summarize(transcript)
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        rag_chain = build_rag_chain(transcript)

        return {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
    finally:
        # Keep container disk clean by deleting audio files after processing
        cleanup_audio_files(temp_files)


# ---- session state ----
if "result" not in st.session_state:
    st.session_state.result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("Briefly AI")
st.caption("AI-Powered Meeting Intelligence, Executive Summaries & Conversational RAG")

with st.sidebar:
    st.header("Briefly AI")

    st.caption("Recruiter 1-Click Demo:")
    sample_clicked = st.button(
        "Load Sample Meeting",
        use_container_width=True,
        help="Run instant demo with bundled sample audio without uploading",
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload Meeting Audio / Video",
        type=["mp3", "wav", "m4a", "mp4", "webm", "ogg", "aac"],
        help="Supports standard audio and video formats",
    )

    language = st.radio("Language", ["english", "hinglish"], horizontal=True)
    run_clicked = st.button("Process", type="primary", use_container_width=True)

# Process Sample Meeting
if sample_clicked:
    ensure_sample_exists()
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        st.sidebar.error("Sample audio file could not be loaded.")
    else:
        with st.spinner("Processing sample meeting — extracting insights..."):
            try:
                st.session_state.result = run_pipeline(
                    SAMPLE_AUDIO_PATH, language="english", is_sample=True
                )
                st.session_state.chat_history = []
            except Exception as e:
                st.sidebar.error(f"Pipeline failed: {e}")

# Process User Upload
elif run_clicked:
    if uploaded_file is None:
        st.sidebar.error("Please upload an audio/video file or click 'Load Sample Meeting'.")
    else:
        os.makedirs("downloads", exist_ok=True)
        target_source = os.path.join("downloads", f"upload_{uploaded_file.name}")
        with open(target_source, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Processing meeting — this can take a moment..."):
            try:
                st.session_state.result = run_pipeline(
                    target_source, language=language, is_sample=False
                )
                st.session_state.chat_history = []
            except Exception as e:
                st.sidebar.error(f"Pipeline failed: {e}")

result = st.session_state.result

if result:
    st.subheader(result["title"])

    tab_summary, tab_actions, tab_decisions, tab_questions, tab_transcript = st.tabs(
        ["Summary", "Action Items", "Key Decisions", "Open Questions", "Transcript"]
    )
    with tab_summary:
        st.write(result["summary"])
    with tab_actions:
        st.write(result["action_items"])
    with tab_decisions:
        st.write(result["key_decisions"])
    with tab_questions:
        st.write(result["open_questions"])
    with tab_transcript:
        st.text_area("Full transcript", result["transcript"], height=300)

    st.divider()
    st.subheader("Chat with your meeting")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("Ask a question about the video...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            response_generator = stream_answer(
                result["rag_chain"], question, st.session_state.chat_history
            )
            answer = st.write_stream(response_generator)
        st.session_state.chat_history.append(("assistant", answer))
else:
    st.info(
        "Upload an audio/video file or click 'Load Sample Meeting' in the sidebar to get started."
    )