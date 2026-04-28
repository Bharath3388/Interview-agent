# AI Interview Agent

An AI-powered mock interview system with real-time voice interaction. Upload your resume, paste a job description, and practice with an adaptive AI interviewer that scores every answer, asks follow-ups, and generates a detailed performance report.

### Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [interview-agent-iota.vercel.app](https://interview-agent-iota.vercel.app) |
| **Backend API** | [interview-api-production-031d.up.railway.app](https://interview-api-production-031d.up.railway.app) |

---

## Features

- **Voice Output** — AI interviewer speaks questions aloud via Edge TTS
- **Adaptive Questioning** — Groq LLM generates context-aware questions and probing follow-ups
- **Resume & JD Parsing** — Upload PDF/DOCX resume and paste any job description
- **Live Evaluation** — Every answer scored on 4 dimensions in real-time
- **Final Report** — Overall score, cracking probability, hiring recommendation, topic breakdown
- **Text + Voice Input** — Type answers or use browser speech recognition
- **Auth & History** — Register/login, view past interviews and detailed Q&A
- **Modern Next.js UI** — Dark glassmorphism design with animated avatar

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NEXT.JS FRONTEND (port 3000)                    │
│                                                                     │
│   Auth ──▶ Setup ──▶ Interview (WebSocket) ──▶ Report              │
│                         │                                           │
│            REST /api/*  │  WS /ws/{id}                              │
│           (proxied via  │  next.config.mjs rewrites)                │
└─────────────┬───────────┼───────────────────────────────────────────┘
              │           │
┌─────────────▼───────────▼───────────────────────────────────────────┐
│               FASTAPI BACKEND (Railway)                             │
│                                                                     │
│   api/                                                              │
│   ├── auth_routes.py    POST /api/auth/register, /login, GET /me   │
│   ├── routes.py         POST /api/interview/start, /{id}/end       │
│   ├── websocket.py      WS /ws/{session_id}                        │
│   └── deps.py           Auth dependency (JWT validation)            │
│                                                                     │
│   agents/                                                           │
│   ├── graph.py          InterviewGraph orchestrator                 │
│   └── nodes.py          generate_question → evaluate → decide_next │
│                                                                     │
│   core/security.py      JWT + bcrypt password hashing               │
│   db/                   SQLAlchemy models + CRUD (PostgreSQL)       │
│                                                                     │
└──────────┬─────────────────────────┬────────────────────────────────┘
           │                         │
    ┌──────▼──────┐           ┌──────▼──────┐
    │  Edge TTS   │           │   Groq API  │
    │  (cloud)    │           │   (LLM)     │
    └─────────────┘           └─────────────┘
```

### Data Flow

```
User speaks/types answer
  → Sent over WebSocket as text (browser speech recognition)
  → Agent evaluates the answer (Groq LLM)
  → Agent decides: follow-up? next topic? end?
  → Agent generates next question (Groq LLM)
  → Edge TTS synthesizes speech
  → Base64 audio returned over WebSocket
  → AudioContext decodes and plays in browser
  → Avatar animates while speaking
```

---

## Project Structure

```
Interview-agent/
│
├── app/                            # Backend (Python / FastAPI)
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Settings from environment variables
│   │
│   ├── core/                       # Security layer
│   │   └── security.py             # JWT tokens + password hashing
│   │
│   ├── api/                        # HTTP + WebSocket layer
│   │   ├── deps.py                 # FastAPI dependencies (auth)
│   │   ├── auth_routes.py          # Register, login, me, history
│   │   ├── routes.py               # Interview start/end + session store
│   │   └── websocket.py            # Real-time interview via WebSocket
│   │
│   ├── agents/                     # Interview state machine
│   │   ├── graph.py                # InterviewGraph orchestrator
│   │   ├── nodes.py                # generate_question, evaluate_answer, decide_next
│   │   └── prompts.py              # System prompt constants
│   │
│   ├── models/                     # Data models
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   └── state.py                # InterviewState dataclass
│   │
│   ├── services/                   # External service wrappers
│   │   ├── llm.py                  # Groq LLM (questions, evaluation, reports)
│   │   ├── tts.py                  # Edge TTS (text → audio via MS cloud)
│   │   └── resume_parser.py        # PDF / DOCX → plain text
│   │
│   └── db/                         # Database layer
│       ├── database.py             # SQLAlchemy engine + session factory
│       ├── models.py               # ORM: User, InterviewSession, InterviewQA
│       └── crud.py                 # Create/read/update helpers
│
├── interview-ui/                   # Frontend (Next.js + Tailwind)
│   ├── src/
│   │   ├── app/                    # App router pages
│   │   │   ├── auth/page.tsx       # Login / Register
│   │   │   ├── setup/page.tsx      # Resume upload + config
│   │   │   ├── interview/page.tsx  # Real-time interview + chat
│   │   │   ├── report/page.tsx     # Score ring + detailed report
│   │   │   └── history/page.tsx    # Past interview sessions
│   │   ├── components/ui/          # Reusable UI components
│   │   ├── context/AuthContext.tsx  # Auth state provider
│   │   ├── lib/api.ts              # API client + WebSocket factory
│   │   └── types/index.ts          # TypeScript type definitions
│   ├── next.config.mjs             # API proxy rewrites to backend
│   └── package.json
│
├── configs/
│   └── default_answers.json        # Default candidate profile data
│
├── linkedin_test.py                # LinkedIn Easy Apply automation (separate tool)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── Dockerfile                      # Backend container for Railway
├── Procfile                        # Railway start command
├── railway.json                    # Railway build config
├── nixpacks.toml                   # Nixpacks system deps (ffmpeg)
├── .dockerignore                   # Docker build exclusions
└── .gitignore
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI + Uvicorn | Async HTTP + WebSocket server |
| **Frontend** | Next.js 14 + Tailwind CSS | Modern React UI with dark theme |
| **LLM** | Groq API (Llama 3.3 70B) | Question generation, evaluation, reports |
| **TTS** | Edge TTS (Microsoft) | Cloud text-to-speech (zero memory) |
| **STT** | Browser Web Speech API | Client-side speech recognition |
| **Database** | PostgreSQL + SQLAlchemy | User accounts, session history (Railway) |
| **Hosting** | Vercel + Railway | Frontend on Vercel, backend on Railway |
| **Auth** | JWT + bcrypt | Stateless authentication |
| **PDF Parsing** | PyPDF2 + python-docx | Resume text extraction |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

### 1. Clone and install backend

```bash
git clone https://github.com/Bharath3388/Interview-agent.git
cd Interview-agent

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY and JWT_SECRET
```

### 3. Install frontend

```bash
cd interview-ui
npm install
```

### 4. Start both servers

**Terminal 1 — Backend:**
```bash
source venv/bin/activate
python -m app.main
# Runs on http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd interview-ui
npm run dev
# Runs on http://localhost:3000
```

Open **http://localhost:3000** in your browser.

### 5. Deploy to production

The app is deployed as a split architecture:

**Frontend → Vercel:**
```bash
cd interview-ui
vercel --prod
# Set env vars in Vercel dashboard:
#   NEXT_PUBLIC_API_URL=https://interview-api-production-031d.up.railway.app
#   NEXT_PUBLIC_WS_HOST=interview-api-production-031d.up.railway.app
```

**Backend → Railway:**
```bash
cd ..
railway up
# Set env vars in Railway dashboard:
#   DATABASE_URL (auto-linked from Railway Postgres)
#   GROQ_API_KEY, JWT_SECRET, ALLOWED_ORIGINS
```

---

## How to Use

### Starting an Interview

1. **Register / Login** — Create an account on the auth page
2. **Upload Resume** (optional) — PDF or DOCX format
3. **Enter Job Description** — Paste a full JD or type a topic like "Senior Python Engineer"
4. **Choose Duration** — 5, 10, 15, or 30 minutes
5. **Choose Difficulty** — Easy, Mid, or Hard
6. Click **Start Interview**

### During the Interview

- Click the **mic button** to record via browser speech recognition — it auto-sends after 5s of silence
- Or type your answer and press **Enter**
- The AI speaks each question and shows it in the chat
- Watch the **progress bar** and **topic badge** for current phase
- Click **End Interview** at any time for an early report

### Interview Phases

| Phase | Focus |
|-------|-------|
| Introduction | Background, motivation, career goals |
| Technical | Deep technical questions from resume/JD |
| Experience | Project stories, challenges, problem-solving |
| Behavioral | Teamwork, leadership, conflict resolution |
| Closing | Wrap-up |

### After the Interview

The report shows:
- **Overall Score** (0–100) with animated ring chart
- **Cracking Probability** — estimated chance of getting the role
- **Hiring Recommendation** — Strong No / No / Maybe / Yes / Strong Yes
- **Topic Score Bars** — per-topic breakdown
- **Strengths, Improvements, Recommendations** — actionable feedback
- **Executive Summary**

You can view all past interviews under **History**.

---

## API Reference

### Auth Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login, returns JWT |
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/auth/history` | List completed sessions |
| `GET` | `/api/auth/history/{id}` | Session Q&A detail |

### Interview Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/interview/start` | Start session (multipart/form-data) |
| `GET` | `/api/interview/{id}/progress` | Current progress |
| `POST` | `/api/interview/{id}/end` | Force end + get report |
| `GET` | `/api/health` | Health check |

### WebSocket Protocol

Connect to `ws://localhost:8000/ws/{session_id}`

**Client → Server:**
```json
{ "action": "text", "text": "My answer here..." }
{ "action": "end" }
```

**Server → Client:**
```json
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
    "relevance_to_role": 85
  },
  "is_complete": false,
  "progress": { ... }
}
```

```json
{ "type": "report", "report": { "overall_score": 78, ... } }
{ "type": "error", "message": "An internal error occurred" }
```

---

## Environment Variables

See [.env.example](.env.example) for all options:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key |
| `JWT_SECRET` | Recommended | auto-generated | Secret for signing JWTs |
| `ALLOWED_ORIGINS` | No | `localhost:3000,8000` | CORS allowed origins |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `TTS_VOICE` | No | `en-US-AvaMultilingualNeural` | Edge TTS voice name |
| `DATABASE_URL` | No | `sqlite:///interview_agent.db` | Database URL (use PostgreSQL in prod) |
| `NEXT_PUBLIC_API_URL` | No (Vercel) | `http://localhost:8000` | Backend URL for Next.js rewrites |
| `NEXT_PUBLIC_WS_HOST` | No (Vercel) | `localhost:8000` | WebSocket host for direct WS connection |
| `MAX_FOLLOW_UPS` | No | `2` | Follow-ups before moving on |
| `DEFAULT_DURATION` | No | `15` | Default interview minutes |

---

## Agent Logic

The interview is driven by a state machine (no LangGraph dependency):

```
[generate_question] → user answers → [evaluate_answer] → [decide_next]
       ↑                                                       │
       └──────────── follow_up / continue ─────────────────────┘
                                │ end
                         [generate_report]
```

**Decision rules:**
- `questions_asked >= max_questions` → **end**
- `elapsed_time >= duration × 60` → **end**
- `needs_follow_up && follow_ups < 2` → **follow_up** (probe deeper)
- Otherwise → **continue** (advance to next topic)

**Topic sequence** scales with duration:
```
introduction → technical → technical → experience → technical → behavioral → closing
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "GROQ_API_KEY not set" | Set it in `.env` — get one at [console.groq.com](https://console.groq.com/keys) |
| JWT sessions lost on restart | Set a fixed `JWT_SECRET` in `.env` |
| CORS errors | Add your frontend URL to `ALLOWED_ORIGINS` in `.env` |
| TTS fails | `pip install --upgrade edge-tts` |
| Port 8000 in use | `lsof -i :8000` then `kill <PID>`, or set `PORT=8001` in `.env` |
| Browser mic not working | Allow microphone in browser settings, use HTTPS or localhost |
| Audio won't play | Click anywhere on the page first (AudioContext policy) |

---

## Cost

| Component | Cost |
|-----------|------|
| Groq API (Llama 3.3 70B) | Free tier: 30 req/min |
| Edge TTS (Microsoft) | Free (cloud) |
| Browser STT | Free (client-side) |
| Railway (backend) | Free tier: 500 hrs/month |
| Vercel (frontend) | Free tier: unlimited |
| **Per interview** | **~$0.00 on free tier** |

---

## License

- **FastAPI** — MIT
- **Next.js** — MIT
- **Edge TTS** — MIT

The Groq API has its own [terms of service](https://groq.com/terms-of-use/).
