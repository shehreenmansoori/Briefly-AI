import os
import time
import requests
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# Cloud STT configs
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")
SARVAM_PIECE_SECONDS = 25

_groq_client = None


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set in environment / .env. "
                "Get a free API key at https://console.groq.com/keys for fast, 0MB-RAM cloud Whisper."
            )
        from groq import Groq
        _groq_client = Groq(api_key=key)
    return _groq_client


def transcribe_chunk_groq(chunk_path: str) -> str:
    """
    Transcribe audio chunk using Groq Cloud Whisper API (whisper-large-v3-turbo).
    Ultra-fast (~2-4 seconds for 10 min audio), high accuracy, 0 MB container RAM.
    """
    client = get_groq_client()
    print(f"Sending {os.path.basename(chunk_path)} to Groq Cloud Whisper API...")

    with open(chunk_path, "rb") as f:
        file_bytes = f.read()

    transcription = client.audio.transcriptions.create(
        file=(os.path.basename(chunk_path), file_bytes),
        model="whisper-large-v3-turbo",
        language="en",
        temperature=0.0,
    )
    return getattr(transcription, "text", str(transcription)).strip()


def _send_to_sarvam(piece_path: str, is_translation: bool = True) -> str:
    """Send one <=30s WAV piece to Sarvam AI with retry logic."""
    headers = {"api-subscription-key": SARVAM_API_KEY}
    url = SARVAM_STT_TRANSLATE_URL if is_translation else SARVAM_STT_URL

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(piece_path, "rb") as f:
                files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
                data = {"model": SARVAM_MODEL, "with_diarization": "false"}
                if not is_translation:
                    data["language_code"] = "hi-IN"

                response = requests.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60,
                )

            if response.ok:
                return response.json().get("transcript", "")

            if response.status_code == 429:
                time.sleep(2 * (attempt + 1))
                continue

            print(f"Sarvam returned {response.status_code}: {response.text}")
            response.raise_for_status()

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)

    return ""


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API accepts <=30s audio. Split chunk into 25-second pieces,
    send each with error handling, and concatenate results.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    full_text = []
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  -> Sarvam piece {i + 1}/{total_pieces} ...")
            transcript_piece = _send_to_sarvam(piece_path, is_translation=True)
            if transcript_piece:
                full_text.append(transcript_piece)
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return " ".join(full_text).strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route audio chunk depending on language selection:
    - english  -> Groq Cloud Whisper (falls back to Sarvam if Groq key not set)
    - hinglish -> Sarvam AI STT-Translate
    """
    lang_lower = language.lower().strip()
    if lang_lower == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    if os.getenv("GROQ_API_KEY"):
        return transcribe_chunk_groq(chunk_path)
    elif os.getenv("SARVAM_API_KEY"):
        print("GROQ_API_KEY missing, falling back to Sarvam STT for English...")
        return transcribe_chunk_sarvam(chunk_path)
    else:
        raise RuntimeError(
            "Neither GROQ_API_KEY nor SARVAM_API_KEY is configured. "
            "Set GROQ_API_KEY in .env for instant Whisper transcription."
        )


def transcribe_all(chunks: list, language: str = "english") -> str:
    """Transcribe all audio chunks and return unified transcript."""
    full_transcript = []
    engine = "Sarvam AI" if language.lower().strip() == "hinglish" else "Groq Cloud Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language)
        if text:
            full_transcript.append(text)

    print("Transcription complete.")
    return " ".join(full_transcript).strip()
