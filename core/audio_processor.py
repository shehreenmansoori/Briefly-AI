import os
import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def cleanup_audio_files(file_paths: list) -> None:
    """Safely delete temporary audio files and chunks to keep container disk clean."""
    if not file_paths:
        return
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                # Never delete bundled persistent samples
                norm_parts = os.path.abspath(path).split(os.sep)
                if "samples" in norm_parts:
                    continue
                os.remove(path)
        except Exception as e:
            print(f"Warning: Failed to clean up {path}: {e}")


def download_youtube_audio(url: str) -> str:
    """Download audio from YouTube using video ID for safe, collision-free filename."""
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id")
        filename = os.path.join(DOWNLOAD_DIR, f"{video_id}.wav")

    if not os.path.exists(filename):
        prepared = ydl.prepare_filename(info)
        filename = os.path.splitext(prepared)[0] + ".wav"

    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert any audio or video file (mp3, wav, m4a, mp4, etc.) to 16kHz mono WAV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # 16khz mono
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 5) -> list:
    """
    Split WAV file into 5-minute chunks (~9.6MB each).
    Keeps chunks well below Groq Whisper's 25MB payload limit.
    """
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str, is_persistent_sample: bool = False) -> tuple[list, list]:
    """
    Process YouTube URL, uploaded audio/video, or sample file into 16kHz WAV chunks.
    Returns: (chunks_list, all_created_temp_files_for_cleanup)
    """
    temp_files = []
    source_clean = source.strip()

    if source_clean.startswith("http://") or source_clean.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source_clean)
        temp_files.append(wav_path)
    else:
        normalized = os.path.abspath(source_clean)
        if not os.path.exists(normalized) or not os.path.isfile(normalized):
            raise ValueError(f"File not found: {source_clean}")

        # If it's a temporary upload in downloads/, track for cleanup
        if not is_persistent_sample and DOWNLOAD_DIR in normalized:
            temp_files.append(normalized)

        print("Converting audio to 16kHz mono WAV...")
        wav_path = convert_to_wav(normalized)
        temp_files.append(wav_path)

    print("Chunking audio into 5-minute segments...")
    chunks = chunk_audio(wav_path, chunk_minutes=5)
    temp_files.extend(chunks)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks, temp_files
