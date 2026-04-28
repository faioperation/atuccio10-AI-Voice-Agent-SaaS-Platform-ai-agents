# 🤖 InsureFlow — AI Outbound Calling Engine

Production-ready standalone microservice built with **FastAPI**, **Twilio**, **OpenAI GPT-4**, **FasterWhisper**, and a **FAISS RAG** pipeline. Features optional ElevenLabs integration for premium voice quality and native GoHighLevel CRM support for automated appointment booking.

---

## 🚀 Key Features

| Feature | Details |
|---|---|
| **Outbound AI Calling** | Trigger real calls via Twilio REST SDK with custom lead context |
| **Natural AI Intelligence** | Powered by OpenAI GPT-4 with a sales-optimised persona |
| **Premium Voice (default)** | OpenAI TTS — fast, cost-effective, μ-law output (Twilio-ready) |
| **Premium Voice (optional)** | ElevenLabs — human-like, configurable voice, outputs ulaw_8000 |
| **Local Speech-to-Text** | FasterWhisper — audio never leaves your server |
| **Real-time WebSocket Stream** | Twilio Media Streams → Whisper → GPT-4 → TTS, all in one loop |
| **CRM Integration** | GoHighLevel / LeadConnector — lead lookup & appointment booking |
| **RAG Knowledge System** | DOCX files → FAISS vector store, persisted to disk |
| **Intent Detection** | Auto-classifies calls: Interested / Not Interested / Objection / Appointment / Callback |
| **API Security** | Optional Bearer token / X-API-Key middleware |

---

## 🏗️ Project Structure

```
autocio57InsureFlow/
├── .env                    # Live secrets (not committed)
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── API_README.md           # Detailed API endpoint reference
├── TESTING.md              # End-to-end testing guide
├── knowledge/              # Place .docx knowledge files here
├── logs/                   # Auto-created log files
└── app/
    ├── main.py             # FastAPI app, CORS, auth middleware
    ├── config.py           # Pydantic settings (env var loader)
    ├── api/
    │   └── endpoints.py    # All REST + WebSocket routes
    ├── agents/
    │   ├── calling_agent.py  # Per-call AI conversation agent
    │   └── prompts.py        # System & intent detection prompts
    ├── integrations/
    │   ├── openai_client.py         # GPT-4 chat + intent detection
    │   ├── tts_client.py            # OpenAI TTS (default)
    │   ├── elevenlabs_tts_client.py # ElevenLabs TTS (premium)
    │   ├── whisper_client.py        # FasterWhisper local STT
    │   ├── twilio_client.py         # Twilio REST SDK + TwiML
    │   └── ghl_client.py            # GoHighLevel CRM client
    ├── rag/
    │   └── engine.py       # FAISS vector store + DOCX pipeline
    ├── schemas/
    │   └── call_schemas.py # Pydantic data models
    └── utils/
        └── logger.py       # Loguru structured logging
```

---

## 🛠️ Setup & Installation

### 1. Requirements
Python **3.9 – 3.12** recommended (Python 3.13 also works via numpy μ-law fallback).

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

#### Required
| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (GPT-4 + TTS) |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Your Twilio number (E.164: `+15551234567`) |
| `SERVER_BASE_URL` | Your public server URL (e.g. ngrok URL for local dev) |

#### Optional
| Variable | Default | Description |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | GPT-4 model version |
| `OPENAI_TTS_MODEL` | `tts-1` | OpenAI TTS model |
| `OPENAI_TTS_VOICE` | `alloy` | OpenAI TTS voice |
| `ELEVENLABS_API_KEY` | _(none)_ | Enables premium ElevenLabs voice |
| `ELEVENLABS_VOICE_ID` | `21m00Tcm4TlvDq8ikWAM` | ElevenLabs voice ID |
| `WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `float32` | Compute precision |
| `GHL_API_KEY` | _(none)_ | GoHighLevel API key |
| `GHL_LOCATION_ID` | _(none)_ | GoHighLevel Location ID |
| `GHL_API_BASE_URL` | `https://services.leadconnectorhq.com` | GHL base URL |
| `KNOWLEDGE_BASE_DIR` | `knowledge` | Directory for DOCX files |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `ALLOWED_ORIGINS` | `*` | CORS origins (comma-separated or `*`) |
| `API_SECRET_KEY` | _(none)_ | Set to enable endpoint authentication |

### 3. Knowledge Base

Place `.docx` files in the `knowledge/` directory. They are automatically indexed on startup and persisted to disk — subsequent restarts load the cached index instantly.

```bash
# Or upload at runtime via API:
curl -X POST http://localhost:8000/api/v1/upload-knowledge \
     -F "file=@your-policy-document.docx"
```

### 4. Run the Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Liveness check |
| `POST` | `/api/v1/start-call` | Trigger outbound AI call |
| `GET` | `/api/v1/twiml/{call_sid}` | TwiML for Twilio (auto-called by Twilio) |
| `WS` | `/api/v1/stream/{call_sid}` | Twilio Media Stream WebSocket |
| `POST` | `/api/v1/webhook/twilio` | Twilio status callback |
| `POST` | `/api/v1/process-message` | Manually inject a transcript turn |
| `POST` | `/api/v1/end-call/{call_sid}` | Finalise call, get outcome + transcript |
| `POST` | `/api/v1/upload-knowledge` | Upload DOCX to RAG knowledge base |

See **[API_README.md](./API_README.md)** for full request/response schemas and examples.

---

## 🧠 AI Call Flow

```
POST /start-call
   │
   ├─ Creates CallingAgent (per-call, isolated history)
   └─ Twilio SDK: initiate outbound call
          │
          ▼
Twilio answers → fetches TwiML from GET /twiml/{call_sid}
          │
          ▼
TwiML instructs Twilio to open WebSocket → WS /stream/{call_sid}
          │
          ┌──────────────────── Real-time loop ────────────────────┐
          │  Twilio streams μ-law audio chunks (base64)            │
          │       ↓                                                 │
          │  FasterWhisper  →  transcript text  (local, private)   │
          │       ↓                                                 │
          │  CallingAgent.generate_response()                       │
          │    ├─ RAGEngine.query()  → relevant DOCX context        │
          │    ├─ GPT-4 (with tool calling)                         │
          │    └─ GHLClient.book_appointment()  (if triggered)      │
          │       ↓                                                 │
          │  TTS (OpenAI or ElevenLabs)  →  μ-law audio            │
          │       ↓                                                 │
          │  Audio sent back to Twilio → played to customer         │
          └────────────────────────────────────────────────────────┘
          │
Customer hangs up → POST /webhook/twilio (call.hangup)
          │
          ▼
finalize_call()
   ├─ GPT-4: detect intent  (INTERESTED / APPOINTMENT_REQUEST / ...)
   ├─ GPT-4: generate call summary
   └─ Returns CallResult{outcome, summary, transcript, appointment_created}
```

---

## 🔒 Security

- **API Authentication** — Set `API_SECRET_KEY` in `.env` to require an `X-API-Key` or `Authorization: Bearer` header on all endpoints (Twilio webhook and `/health` are exempt).
- **CORS** — Set `ALLOWED_ORIGINS` to a comma-separated list of your frontend domains.
- **Secrets** — All credentials are loaded from `.env` (excluded from git via `.gitignore`).
- **Privacy** — Whisper STT runs locally; no customer audio is sent to external services.

---

## 🛡️ Stability & Architecture

- **Async throughout** — `asyncio` + FastAPI for concurrent call handling
- **Isolated agents** — each call gets its own `CallingAgent` instance with independent conversation history
- **Persisted RAG index** — FAISS index saved to disk; no re-encoding on restart
- **Structured logging** — Loguru with dual sinks (stdout + rotating log file)
- **Full type safety** — Pydantic v2 validation on all API inputs/outputs
- **Graceful TTS fallback** — ElevenLabs → OpenAI TTS when key not configured

---

## 📚 Documentation

| File | Contents |
|---|---|
| `README.md` | Project overview, setup, architecture |
| `API_README.md` | Full API reference with request/response examples |
| `TESTING.md` | End-to-end testing guide (manual + real Twilio calls) |
| `/docs` | Swagger UI (available when server is running) |
| `/redoc` | ReDoc (available when server is running) |