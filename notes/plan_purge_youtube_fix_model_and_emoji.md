# Execution Plan: Purge YouTube Subsystem, Fix Groq Model 404, and Remove UI Emojis

## Root Cause Analysis: 404 Model Not Found

**The Error:**
```text
Pipeline failed: Error code: 404 - {'error': {'message': "The model `llama-3.3-70b-versatile` does not exist or you do not have access to it.", 'type': 'invalid_request_error', 'code': 'model_not_found'}}
```

**Why it happened:**
We probed the Groq API directly using the configured `GROQ_API_KEY`. The account endpoint (`/openai/v1/models`) confirmed the active models for this key are:
- `openai/gpt-oss-120b` (Frontier 120B parameter text completion)
- `qwen/qwen3.8-27b` (High-speed 27B text completion)
- `whisper-large-v3-turbo` (STT audio transcription)

The specific model `llama-3.3-70b-versatile` is not provisioned or enabled on this Groq account tier. Calling it triggered the 404 `model_not_found` error.

**The Fix:**
Update `get_llm()` across `core/rag_engine.py`, `core/summarize.py`, and `core/extractor.py` to use `openai/gpt-oss-120b` (or support `GROQ_CHAT_MODEL` env var defaulting to `openai/gpt-oss-120b`), while retaining the automatic graceful fallback to `mistral-small-latest`.

---

### Objective
Completely remove the YouTube download dependency and code, fix the Groq 404 model error by switching to `openai/gpt-oss-120b`, and remove the lightning bolt emoji from the sample meeting button.

### Allowed Paths
- `c:\exclusive\sara files\Video assisstant\app.py`
- `c:\exclusive\sara files\Video assisstant\core\audio_processor.py`
- `c:\exclusive\sara files\Video assisstant\core\rag_engine.py`
- `c:\exclusive\sara files\Video assisstant\core\summarize.py`
- `c:\exclusive\sara files\Video assisstant\core\extractor.py`
- `c:\exclusive\sara files\Video assisstant\main.py`
- `c:\exclusive\sara files\Video assisstant\requirements.txt`
- `c:\exclusive\sara files\Video assisstant\README.md`
- `c:\exclusive\sara files\Video assisstant\.env.example`

### Forbidden Paths
- `c:\exclusive\sara files\Video assisstant\.env` (Must preserve local secrets)
- `c:\exclusive\sara files\Medic-main/**`
- `c:\exclusive\sara files\Doc chatbot/**`
- `c:\exclusive\sara files\Video assisstant\samples/sample_meeting.mp3`

---

### Steps

1. **Remove UI Emoji & YouTube UI from `app.py`:**
   - Change button label `"⚡ Load Sample Meeting"` to `"Load Sample Meeting"`.
   - Remove the `st.expander("Or enter YouTube URL")` block and `youtube_url` variable.
   - Adjust `run_clicked` logic to strictly check `uploaded_file`.

2. **Purge YouTube Downloading from `core/audio_processor.py`:**
   - Remove `import yt_dlp`.
   - Delete `download_youtube_audio()` entirely.
   - In `process_input(source, is_persistent_sample)`, remove URL prefix checks (`http://`, `https://`). Ensure it strictly validates and converts local file paths.

3. **Update CLI Entrypoint in `main.py`:**
   - Change prompt `input("Enter YouTube URL or local file path: ")` to `input("Enter audio/video file path: ")`.

4. **Drop `yt-dlp` from `requirements.txt`:**
   - Remove `yt-dlp>=2024.4.9`. This cuts out an external web scraper and further speeds up Docker builds.

5. **Fix Groq Model 404 in `core/rag_engine.py`, `core/summarize.py`, `core/extractor.py`:**
   - Update `get_llm()` to check `os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-120b")`.
   - Pass this verified model to `ChatGroq(model=..., api_key=groq_key, temperature=...)`.

6. **Update Documentation in `README.md` and `.env.example`:**
   - Update references mentioning YouTube to pure audio/video file uploads.
   - Update model descriptions from `Llama 3.3` to `Groq LPU (GPT-OSS 120B)`.

7. **Push Cleaned Codebase to GitHub (`shehreenmansoori/Briefly-AI`):**
   - Push updated files to `main` so Render automatically triggers a clean, error-free rebuild.

---

### Verification Commands

1. **Test Groq LLM Generation:**
   ```powershell
   python -c "from core.extractor import get_llm; llm = get_llm(); print(llm.invoke('Hello').content)"
   ```
2. **Run Pipeline on Sample Meeting:**
   ```powershell
   python -c "from app import run_pipeline; res = run_pipeline('samples/sample_meeting.mp3', language='english', is_sample=True); print('Success:', res['title'])"
   ```
3. **Verify yt-dlp is not imported:**
   ```powershell
   python -c "import core.audio_processor; assert not hasattr(core.audio_processor, 'yt_dlp')"
   ```

---

### Deferred Findings
- `core/audio_processor.py` can add explicit file extension checking (`.mp3`, `.wav`, `.m4a`, etc.) before calling `convert_to_wav` to provide instant user-friendly validation.
