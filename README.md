# Briefly AI — Meeting Intelligence & Conversational RAG

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Groq LPU](https://img.shields.io/badge/Groq-Whisper%20%26%20GPT--OSS%20120B-F55036.svg)](https://groq.com/)
[![Mistral AI](https://img.shields.io/badge/Mistral-Embeddings-orange.svg)](https://mistral.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

> **Briefly AI** is a lightweight, production-grade AI Meeting Assistant that transforms audio/video recordings into structured executive summaries, actionable task matrices, and interactive, history-aware conversational RAG. Built with a zero-local-weight architecture optimized for low-memory cloud containers (e.g., Render Free Tier with 512MB RAM).

---

## Key Highlights

- **0 MB Container RAM Audio Transcription:** Offloads Whisper inference to **Groq Cloud Whisper API** (`whisper-large-v3-turbo`) for ~3-second transcriptions without loading heavy PyTorch wheels.
- **Pure File Upload Architecture:** Secure direct upload for audio and video files (MP3, WAV, M4A, MP4, WEBM, OGG, AAC) with zero dependency on fragile web scrapers.
- **Multilingual Support:** Handles English via Groq Whisper and Hinglish audio translation via **Sarvam AI**.
- **Real-Time Token Streaming:** Delivers meeting Q&A at 300+ tokens/second powered by **Groq LPU (GPT-OSS 120B)** with graceful fallback to Mistral.
- **Ephemeral Session Vector Store:** Uses **Mistral API Embeddings** (`mistral-embed`) with LangChain's `InMemoryVectorStore` to ensure strict tenant isolation with zero cross-user collisions or disk leaks.
- **1-Click Recruiter Demo:** Bundled with a sample meeting recording for instant one-click testing without file uploads.
- **Automatic Ephemeral Cleanup:** Audio files and temporary chunk slices are purged immediately after processing to maintain a clean filesystem.

---

## Architecture

```
[Uploaded Audio/Video or 1-Click Sample]
                   │
                   ▼
     [Audio Processor (16kHz Mono)] ──► [5-Min Chunking Engine]
                                                     │
                                                     ▼
                                    [Groq Cloud Whisper / Sarvam]
                                                     │
                                                     ▼
                                          [Unified Transcript]
                                                     │
                      ┌──────────────────────────────┴──────────────────────────────┐
                      ▼                                                             ▼
        [Executive Intelligence (Groq 120B)]                         [Dense Semantic Indexing]
        • Title Generation                                           • Mistral Embeddings
        • Topic-Grouped Summary                                      • InMemoryVectorStore (Ephemeral)
        • Action Items (Owner + Deadline)                                           │
        • Key Decisions & Open Questions                                            ▼
                      │                                              [Conversational RAG Engine]
                      │                                              • Multi-turn Pronoun Resolution
                      │                                              • Context Retrieval
                      └──────────────────────────────┬──────────────────────────────┘
                                                     ▼
                                      [Streamlit Responsive UI]
                                      • 5 Categorized Tabs
                                      • Live Token Streaming Chat
```

---

## Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/shehreenmansoori/Briefly-AI.git
cd Briefly-AI
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and provide your API keys:
```bash
cp .env.example .env
```
Edit `.env`:
```env
# Required for dense embeddings & fallback generation
MISTRAL_API_KEY=your_mistral_api_key

# Required for fast cloud Whisper & 120B generation
GROQ_API_KEY=your_groq_api_key
GROQ_CHAT_MODEL=openai/gpt-oss-120b

# Optional: Required for Hinglish translation
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_STT_MODEL=saaras:v2.5
```

### 4. Run the Application
```bash
streamlit run app.py
```

---

## Deploying on Render (Free Tier: 512MB RAM)

This project includes a production `Dockerfile` with system `ffmpeg` pre-configured.

1. Create a new **Web Service** on [Render Dashboard](https://dashboard.render.com/).
2. Connect this GitHub repository.
3. Select **Docker** as the Runtime.
4. Select the **Free** instance plan (512MB RAM).
5. Add the Environment Variables:
   - `MISTRAL_API_KEY`
   - `GROQ_API_KEY`
   - `SARVAM_API_KEY` (optional)
6. Click **Deploy Web Service**. Build completes in under 3 minutes and runs stably under ~85MB RAM.

---

## Repository Structure

```
├── core/
│   ├── audio_processor.py   # Safe audio conversion, 5-min chunking & disk cleanup
│   ├── transcriber.py       # Cloud Groq Whisper & Sarvam translation router
│   ├── vector_store.py      # Mistral dense embeddings & InMemoryVectorStore
│   ├── rag_engine.py        # History-aware conversational RAG & token streamer
│   ├── summarize.py         # Single-pass & map-reduce executive summarizer
│   └── extractor.py         # Structured action items & key decision extractors
├── samples/
│   └── generate_sample.py   # Bundled demo audio generator script
├── tests/
│   ├── test_llm.py             # Unit test verifying LLM model selection
│   ├── test_audio_processor.py # Unit test verifying pure file upload
│   └── test_app_ui.py          # Unit test verifying UI clean labels
├── app.py                   # Streamlit web application with live token streaming
├── main.py                  # CLI entry point
├── requirements.txt         # Lightweight dependency manifest (zero-PyTorch, zero-yt-dlp)
├── Dockerfile               # Optimized container build with system ffmpeg
├── .dockerignore
├── .gitignore
└── README.md
```

---

## Author

Developed by **Shehreen Mansoori**  
*GenAI / ML Developer*
