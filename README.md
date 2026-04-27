# 🤖 Agentic Interview Bot

A fully local, voice-powered AI interview agent that runs entirely on a **MacBook Air M1 (8GB RAM)** — no GPU required. Practice technical interviews with a conversational AI that listens to your answers, evaluates them in real-time, asks intelligent follow-up questions, and generates a detailed performance report at the end.

---

## ✨ Features

- 🎤 **Voice Input** — Speak your answers using whisper.cpp (M1-optimized, runs fully offline)
- 🔊 **Voice Output** — AI interviewer speaks questions using Kokoro TTS (CPU-only, ~300MB)
- 🧠 **Adaptive AI** — Gemini 2.0 Flash generates context-aware questions and follow-ups
- 📄 **Resume & JD Parsing** — Upload your resume (PDF/DOCX) and paste a job description
- 📊 **Live Evaluation** — Every answer is scored on 4 dimensions in real-time
- 📈 **Final Report** — Overall score, cracking probability, strengths, improvements, hiring recommendation
- 💬 **Text Fallback** — Type answers if microphone isn't available
- 🌑 **Beautiful Dark UI** — Glassmorphism design with animated avatar and live waveform visualizer
- 💰 **Near-Zero Cost** — Only the Gemini API call costs money (~$0.05 per interview)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        BROWSER (Frontend)                            │
│                                                                      │
│   ┌──────────────────┐   ┌─────────────────┐   ┌────────────────┐   │
│   │  Setup Screen    │   │ Interview Screen │   │ Report Screen  │   │
│   │  (Form + Upload) │   │ (Avatar + Chat) │   │ (Score + Stats)│   │
│   └────────┬─────────┘   └────────┬────────┘   └───────-┬───────┘   │
│            │                      │                      │           │
│   fetch POST /api/interview/start  │ WebSocket /ws/{id}  │           │
└────────────┼──────────────────────┼──────────────────────┼───────────┘
             │                      │                      │
┌────────────▼──────────────────────▼──────────────────────▼───────────┐
│                       FASTAPI BACKEND                                │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │                   LangGraph Agent                           │    │
│   │                                                             │    │
│   │   [generate_question] → [evaluate_answer] → [decide_next]  │    │
│   │          ↑                                       │          │    │
│   │          └────────────── loop ───────────────────┘          │    │
│   │                              │ end                          │    │
│   │                       [generate_report]                     │    │
│   └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────┬──────────────────┬──────────────────┬─────────────────────┘
           │                  │                  │
    ┌──────▼──────┐   ┌───────▼──────┐   ┌──────▼──────┐
    │ whisper.cpp │   │  Kokoro TTS  │   │ Gemini API  │
    │    (STT)    │   │   (Speech)   │   │   (Brain)   │
    │  ~142MB RAM │   │  ~300MB RAM  │   │  External   │
    └─────────────┘   └──────────────┘   └─────────────┘
```

### Data Flow

```
User speaks
    → MediaRecorder captures WebM audio
    → Base64 encoded, sent over WebSocket
    → whisper.cpp transcribes to text
    → LangGraph agent evaluates the answer (Gemini)
    → Agent decides: follow-up? next topic? end?
    → Agent generates next question (Gemini)
    → Kokoro TTS synthesizes speech
    → Base64 WAV returned over WebSocket
    → AudioContext decodes and plays in browser
    → Avatar animates, waveform visualizes
```

---

## 🗂️ Project Structure

```
interview-agent/
│
├── app/                          # Backend (Python / FastAPI)
│   ├── main.py                   # FastAPI entry point, mounts routes + static files
│   ├── config.py                 # Settings loaded from .env
│   │
│   ├── agents/                   # LangGraph-style interview orchestrator
│   │   ├── graph.py              # InterviewGraph — orchestrates the full flow
│   │   ├── nodes.py              # Node functions: generate, evaluate, decide
│   │   └── prompts.py            # System prompt constants
│   │
│   ├── models/                   # Pydantic schemas + state dataclasses
│   │   ├── schemas.py            # Request/response models
│   │   └── state.py              # InterviewState (mutable session data)
│   │
│   ├── services/                 # External service wrappers
│   │   ├── stt_whisper_cpp.py    # Calls whisper.cpp binary via subprocess
│   │   ├── tts_kokoro.py         # Kokoro TTS pipeline (singleton)
│   │   ├── llm_gemini.py         # Gemini API calls + JSON extraction
│   │   ├── resume_parser.py      # PDF / DOCX → plain text
│   │   └── evaluator.py          # Score aggregation helper
│   │
│   └── api/
│       ├── routes.py             # REST endpoints (/api/interview/*)
│       └── websocket.py          # WebSocket handler (/ws/{session_id})
│
├── frontend/                     # Pure HTML/CSS/JS (no framework)
│   ├── index.html                # All 3 screens: Setup, Interview, Report
│   ├── styles.css                # Dark glassmorphism design system
│   └── app.js                    # Recording, WebSocket, audio playback, UI logic
│
├── whisper.cpp/                  # Cloned whisper.cpp repo (built separately)
│   └── models/
│       └── ggml-base.en.bin      # ~142MB STT model (downloaded by setup.sh)
│
├── requirements.txt              # Python dependencies
├── setup.sh                      # One-shot M1 setup script
└── .env                          # API keys and config (not committed)
```

---

## ⚙️ Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Backend** | FastAPI + Uvicorn | Async, WebSocket support, fast |
| **Agent Logic** | Custom state machine (LangGraph-style) | Full control, lightweight |
| **STT** | [whisper.cpp](https://github.com/ggerganov/whisper.cpp) | 72% less RAM than Python Whisper, M1-optimized via Metal/NEON |
| **TTS** | [Kokoro 82M](https://huggingface.co/hexgrad/Kokoro-82M) | CPU-only, Apache 2.0, high quality, ~300MB |
| **LLM** | Gemini 2.0 Flash API | Best speed/cost/quality ratio |
| **Frontend** | Vanilla HTML/CSS/JS | Zero bundle overhead, served directly by FastAPI |
| **PDF Parsing** | PyPDF2 + python-docx | Lightweight, no extra services |

### RAM Budget (8GB M1)

| Service | RAM |
|---------|-----|
| whisper.cpp (base.en) | ~142MB |
| Kokoro TTS | ~300MB |
| FastAPI + Python | ~150MB |
| Browser | ~600MB |
| macOS | ~2.0GB |
| **Total used** | **~3.2GB** |
| **Free headroom** | **~4.8GB** |

---

## 🚀 Setup & Installation

### Prerequisites

- macOS on Apple Silicon (M1/M2/M3)
- Python 3.10+ installed (`python3 --version`)
- [Homebrew](https://brew.sh) installed

### Step 1 — Run the Setup Script

```bash
git clone <your-repo-url> interview-agent
cd interview-agent
chmod +x setup.sh
./setup.sh
```

The script will:
1. Install `ffmpeg` and `cmake` via Homebrew
2. Create a Python virtual environment (`venv/`)
3. Install all Python packages from `requirements.txt`
4. Compile `whisper.cpp` with Apple Metal optimizations
5. Download the `base.en` model (~142MB)
6. Create a `.env` file template

### Step 2 — Add Your Gemini API Key

```bash
# Get a free key at: https://aistudio.google.com/app/apikey
nano .env
```

```env
GEMINI_API_KEY=your_actual_key_here
```

### Step 3 — Start the Server

```bash
source venv/bin/activate
python -m app.main
```

### Step 4 — Open the App

Open your browser and go to: **http://localhost:8000**

---

## 🎯 How to Use

### Starting an Interview

1. **Upload Resume** (optional) — PDF or DOCX format
2. **Enter Job Description / Topic** — Paste a full JD or just type a topic like `"Senior Python Engineer"` or `"System Design"`
3. **Choose Duration** — 10, 15, 20, or 30 minutes
4. **Choose Difficulty** — Easy (entry level), Mid (intermediate), Hard (senior/staff)
5. Click **Start Interview**

### During the Interview

- 🎤 Click the **mic button** to record your answer — click again to stop and submit
- ⌨️ Or type your answer in the text field and press **Enter** or the send button
- The AI will speak the next question and show it in the chat
- Watch the **progress bar** to see how far along you are
- The **topic badge** shows the current interview phase

### Interview Phases

| Phase | Focus |
|-------|-------|
| **Introduction** | Background, motivation, career goals |
| **Technical** | Skills from your resume / JD — deep technical questions |
| **Experience** | Project stories, challenges, problem-solving approach |
| **Behavioral** | Teamwork, leadership, conflict resolution |
| **Closing** | Wrap-up, candidate questions |

### After the Interview

The **Report Screen** shows:
- **Overall Score** (0–100) — animated ring chart
- **Cracking Probability** — estimated chance of getting the role
- **Hiring Recommendation** — Strong No / No / Maybe / Yes / Strong Yes
- **Topic Breakdown** — animated score bars per topic
- **Technical Strengths** — what you did well
- **Areas for Improvement** — where to focus
- **Specific Recommendations** — actionable next steps
- **Executive Summary** — 2–3 sentence overview

---

## 🔌 API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/interview/start` | Start a session, returns first question + audio |
| `GET` | `/api/interview/{id}/progress` | Get current session progress |
| `POST` | `/api/interview/{id}/end` | Force end and get report |
| `GET` | `/api/health` | Health check |

**`POST /api/interview/start`** — `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | File | No | PDF or DOCX resume |
| `job_description` | string | No* | Pasted job description |
| `topic` | string | No* | Interview topic (used if no JD) |
| `duration` | int | No | Minutes (default: 15) |
| `difficulty` | string | No | easy / mid / hard |

*At least one of `resume`, `job_description`, or `topic` is required.

**Response:**
```json
{
  "session_id": "abc123def",
  "first_question": {
    "question_text": "Tell me about yourself...",
    "question_type": "introduction",
    "question_number": 1,
    "total_questions": 7,
    "topic_phase": "introduction"
  },
  "audio": "<base64 WAV>",
  "progress": { "questions_asked": 0, "total_questions": 7, "current_topic": "introduction" }
}
```

### WebSocket Protocol

Connect to `ws://localhost:8000/ws/{session_id}`

**Client → Server messages:**

```jsonc
// Send audio (base64-encoded WebM)
{ "action": "audio", "data": "<base64>" }

// Send text answer directly
{ "action": "text", "text": "My answer here..." }

// Force end interview
{ "action": "end" }
```

**Server → Client messages:**

```jsonc
// Status update
{ "type": "status", "message": "Transcribing..." }

// Transcription of recorded audio
{ "type": "transcription", "text": "The candidate said..." }

// Next question + evaluation of previous answer
{
  "type": "question",
  "text": "Can you elaborate on that?",
  "question_number": 3,
  "total_questions": 7,
  "topic_phase": "technical",
  "audio": "<base64 WAV>",
  "evaluation": {
    "technical_accuracy": 80,
    "communication_clarity": 75,
    "depth_of_knowledge": 70,
    "relevance_to_role": 85,
    "needs_follow_up": false
  },
  "is_complete": false,
  "progress": { ... }
}

// Final report (when interview ends)
{
  "type": "report",
  "report": {
    "overall_score": 78,
    "cracking_probability": 65,
    "technical_strengths": ["..."],
    "areas_for_improvement": ["..."],
    "specific_recommendations": ["..."],
    "hiring_recommendation": "Yes",
    "summary": "Strong candidate...",
    "topic_scores": { "technical": 75, "communication": 80 }
  }
}

// Error
{ "type": "error", "message": "Could not understand audio." }
```

---

## 🧩 Agent Logic (Deep Dive)

The interview brain is a **state machine** implemented without external LangGraph dependencies:

```
InterviewState (dataclass)
    ├── resume_text, jd_text, duration, difficulty
    ├── history: List[InterviewEntry]     ← full Q&A transcript
    ├── scores: List[Dict]                ← per-question evaluations
    ├── current_topic: str                ← current phase
    ├── follow_up_count: int              ← 0–2 before moving on
    └── questions_asked / max_questions   ← pacing control
```

**Decision rules (decide_next_node):**

```python
if questions_asked >= max_questions:   → "end"
if elapsed_time >= duration * 60:      → "end"
if needs_follow_up and follow_up < 2:  → "follow_up"  (re-runs generate_question in follow-up mode)
else:                                  → "continue"    (advance topic, generate next question)
```

**Topic progression:**

```
introduction → technical → technical → experience → technical → behavioral → closing
```

(Scales with duration — more technical questions are inserted for longer sessions.)

---

## ⚡ Performance on M1 8GB

| Model | Transcription Time | RAM |
|-------|-------------------|-----|
| `tiny.en` (75MB) | ~194ms | 75MB |
| `base.en` (142MB) ✅ **recommended** | ~380ms | 142MB |
| `small.en` (466MB) | ~1250ms | 466MB |

**TTS latency:** ~0.5–1.5s per sentence (Kokoro on CPU)
**LLM latency:** ~1–3s per question (Gemini 2.0 Flash)
**Total response time:** ~3–6s per exchange

---

## 💸 Cost Analysis

| Component | Solution | Cost per Interview |
|-----------|----------|-------------------|
| Speech-to-Text | whisper.cpp (local) | $0.00 |
| Text-to-Speech | Kokoro (local) | $0.00 |
| Avatar & UI | CSS/JS (local) | $0.00 |
| LLM | Gemini 2.0 Flash API | ~$0.02–0.08 |
| **Total** | | **~$0.02–0.08** |

Monthly (10 interviews/day × 30 days):
- **This setup:** ~$6–25/month
- **Commercial equivalent:** $1,800–3,600/month

---

## 🛠️ Configuration Reference

All settings live in `.env`:

```env
# Required
GEMINI_API_KEY=your_key_here

# Whisper.cpp
WHISPER_MODEL_PATH=whisper.cpp/models/ggml-base.en.bin
WHISPER_CPP_PATH=whisper.cpp/build/bin/whisper-cli
WHISPER_THREADS=4

# TTS (Kokoro voices)
# American Female: af_heart, af_bella, af_sarah
# American Male:   am_adam, am_michael
# British Female:  bf_emma
# British Male:    bm_george
TTS_VOICE=af_heart
TTS_LANGUAGE=a

# Server
HOST=0.0.0.0
PORT=8000

# Interview behavior
MAX_FOLLOW_UPS=2
DEFAULT_DURATION=15
```

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY not set" error
Edit `.env` and add your key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### whisper.cpp not found / segfault
```bash
cd whisper.cpp
make clean
make  # Without Metal if Metal causes issues
```
Or rebuild with cmake:
```bash
mkdir -p build && cd build
cmake .. -DWHISPER_METAL=ON
cmake --build . --config Release -j4
```

### "Could not understand audio" on every answer
1. Check microphone permissions in browser (click the lock icon in address bar)
2. Verify whisper model path in `.env`
3. Try a smaller model: `./whisper.cpp/models/download-ggml-model.sh tiny.en`

### Out of memory / slow responses
Switch to `tiny.en` model (75MB):
```bash
cd whisper.cpp && bash ./models/download-ggml-model.sh tiny.en
```
Update `.env`:
```env
WHISPER_MODEL_PATH=whisper.cpp/models/ggml-tiny.en.bin
```

### TTS sounds robotic or fails
Ensure kokoro is installed correctly:
```bash
pip install --upgrade kokoro soundfile
```

### Browser can't play audio ("AudioContext not allowed")
Click anywhere on the page before starting the interview. The app automatically resumes the AudioContext on first user interaction.

### Port 8000 already in use
```bash
lsof -i :8000
kill -9 <PID>
# Or change port in .env: PORT=8001
```

---

## 🔒 Security Notes

- The backend only accepts connections from `localhost` by default
- Audio is processed entirely in memory — no files are stored permanently
- Temp `.wav` files are deleted immediately after transcription
- The Gemini API key is loaded from `.env` and never exposed to the frontend
- WebSocket sessions are cleaned up on disconnect

---

## 🗺️ Roadmap

| Feature | Status |
|---------|--------|
| Core voice interview loop | ✅ Done |
| Resume + JD parsing | ✅ Done |
| Real-time evaluation | ✅ Done |
| Final report with scores | ✅ Done |
| Text-input fallback | ✅ Done |
| Animated avatar + waveform | ✅ Done |
| Interview history persistence (SQLite) | 🔲 Planned |
| Multiple concurrent sessions | 🔲 Planned |
| Export report as PDF | 🔲 Planned |
| Custom question sets | 🔲 Planned |
| MuseTalk avatar (GPU required) | 🔲 Future |

---

## 📦 Dependencies

```
fastapi          — Web framework
uvicorn          — ASGI server
websockets       — WebSocket support
python-multipart — File upload handling
langgraph        — Agent workflow (graph structure)
langchain        — LLM tooling utilities
kokoro           — Text-to-speech pipeline
soundfile        — WAV encoding/decoding
google-generativeai — Gemini API client
PyPDF2           — PDF text extraction
python-docx      — DOCX text extraction
pydantic         — Data validation
python-dotenv    — .env loading
numpy            — Audio array operations
```

---

## 📄 License

This project uses open-source components:
- **whisper.cpp** — MIT License
- **Kokoro TTS** — Apache 2.0
- **FastAPI** — MIT License
- **LangGraph / LangChain** — MIT License

The Gemini API is a commercial service — see [Google AI pricing](https://ai.google.dev/pricing).

---

*Built for MacBook Air M1 (8GB RAM) · Optimized for low resource usage · March 2026*
