# AI Outbound Calling Engine (InsureFlow)

Production-ready standalone microservice built with FastAPI, Twilio, OpenAI, Whisper, and RAG capabilities. Features optional ElevenLabs integration for premium voice quality.

## 🚀 Key Features

- **Outbound AI Calling**: Trigger calls via Twilio with custom context.
- **Natural AI Intelligence**: Powered by OpenAI GPT-4 with a sales-optimized persona.
- **High-Quality Voice**: 
  - Default: OpenAI TTS (fast, cost-effective)
  - Premium: ElevenLabs integration (human-like conversations, requires API key)
- **Speech-to-Text**: Local FasterWhisper transcription (no external API needed)
- **CRM Integration**: Native support for **GoHighLevel** (LeadConnector) for lead fetching and appointment booking.
- **RAG Knowledge System**: Inject product details or company context from DOCX files dynamically.
- **Intent Detection**: Automatically classifies calls as Interested, Not Interested, Objection, or Appointment Request.

## 🏗️ Project Structure

```
/app
  /api          # FastAPI routes
  /services     # Business logic & call orchestration
  /agents       # AI persona, prompts, and logic
  /rag          # DOCX processing & retrieval engine
  /integrations # Connectors for Twilio, Whisper, OpenAI TTS, ElevenLabs TTS, GoHighLevel
  /schemas      # Pydantic models for type safety
  /utils        # Logging & helpers
```

## 🛠️ Setup & Installation

### 1. Requirements
Ensure you have Python 3.9+ installed.

```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:

- `OPENAI_API_KEY`: Your OpenAI API key (for GPT-4 and optional TTS)
- `OPENAI_MODEL`: GPT-4 model (default: gpt-4-turbo-preview)
- `OPENAI_TTS_MODEL`: OpenAI TTS model (default: tts-1)
- `OPENAI_TTS_VOICE`: OpenAI TTS voice (default: alloy)

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (optional, for premium voice)
- `ELEVENLABS_VOICE_ID`: Your preferred ElevenLabs voice ID (default: 21m00Tcm4TlvDq8ikWAM)

- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number (in E.164 format)

- `WHISPER_MODEL`: Whisper model size (default: base)
- `WHISPER_DEVICE`: Device for Whisper (cpu/cuda, default: cpu)
- `WHISPER_COMPUTE_TYPE`: Compute type for Whisper (default: float32)

- `GHL_API_KEY`: Your GoHighLevel (LeadConnector) API key (optional)
- `GHL_LOCATION_ID`: Your GHL Location ID (optional)
- `GHL_API_BASE_URL`: GHL API base URL (default: https://services.leadconnectorhq.com)

- `KNOWLEDGE_BASE_DIR`: Directory for DOCX knowledge base (default: knowledge)
- `EMBEDDING_MODEL`: Sentence transformer model for RAG (default: all-MiniLM-L6-v2)

### 3. Knowledge Base
Place your `.docx` files in the `knowledge/` directory. These will be automatically indexed on startup for the RAG engine.

### 4. Run the Service
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### Start Outbound Call
`POST /api/v1/start-call`
```json
{
  "lead": {
    "name": "John Doe",
    "phone_number": "+1234567890",
    "context": "Interested in health insurance for a family of 4."
  }
}
```

### Webhook (Twilio)
`POST /api/v1/webhook/twilio`
Handle Twilio status updates, transcripts, and call ending events.

### Health Check
`GET /api/v1/health`

### Process Message (Manual)
`POST /api/v1/process-message`
Manually process a conversation turn or use as a fallback brain.

### End Call
`POST /api/v1/end-call/{call_sid}`
Finalize and return the result for a given call.

### Upload Knowledge
`POST /api/v1/upload-knowledge`
Upload a DOCX file to the knowledge base and re-index the RAG engine.

## 🧠 AI Flow

1. **Initiate**: App triggers Twilio call.
2. **Conversation**: 
   - Twilio streams audio to your server via WebSocket
   - Whisper converts speech to text locally
   - App provides intelligence via GPT-4 + RAG
   - Response converted to speech via OpenAI TTS (or ElevenLabs if configured)
   - Audio played back via Twilio
3. **RAG**: For every query, the App retrieves relevant data from DOCX files.
4. **Intent**: On call end, the system analyzes the full transcript to determine the outcome.
5. **Action**: If "Appointment" intent is detected, it triggers the GoHighLevel booking tool.

## 🛡️ Stability & Safety

- **Async Architecture**: Scalable handling of multiple concurrent calls.
- **Structured Logging**: Loguru setup for debugging and production monitoring.
- **Type Safety**: Full Pydantic validation for all API inputs and outputs.
- **Local STT**: Whisper runs locally, ensuring privacy and no external API dependencies for transcription.