# InsureFlow AI Outbound Calling Engine - API Documentation

This document provides a clear overview of the available API endpoints for the InsureFlow AI Outbound Calling Engine.
The service is built with FastAPI and provides programmatic control over AI-powered outbound calls.

## Base URL
All endpoints are prefixed with `/api/v1` (as defined in the settings).

## Endpoints

### 1. Health Check
**GET** `/api/v1/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Outbound Calling Engine"
}
```

### 2. Start Outbound Call
**POST** `/api/v1/start-call`

Initiates an outbound AI call to a specified lead.

**Request Body:**
```json
{
  "lead": {
    "name": "John Doe",
    "phone_number": "+1234567890",
    "context": "Interested in health insurance for a family of 4.",
    "metadata": {
      "context": "Additional context for the call (optional)",
      "contact_id": "GHL contact ID (optional)",
      "calendar_id": "GHL calendar ID (optional)"
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "Call initiated successfully"
}
```

**Notes:**
- The `call_sid` is the Twilio Call SID used to track the call.
- The AI agent will be initialized for this call and will handle the conversation.
- If the lead shows interest and requests an appointment, the system will attempt to book it via GoHighLevel (if configured).

### 3. Twilio Webhook Handler
**POST** `/api/v1/webhook/twilio`

Handles incoming webhooks from Twilio (call status updates, media streams, etc.).

**Request Body:**
```json
{
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "event": {
    // Twilio event payload
    // Common events: "call.initiated", "ringing", "in-progress", "completed", "media", etc.
  }
}
```

**Response:**
```json
{
  "status": "ok"
}
```

**Notes:**
- This endpoint should be configured in your Twilio phone number or TwiML App as the webhook for incoming calls and media streams.
- The service uses this to:
  - Detect when a call is answered or ended
  - Receive audio streams for real-time transcription (via Whisper)
  - Send back AI-generated responses (via OpenAI TTS or ElevenLabs)

### 4. Process Message (Manual)
**POST** `/api/v1/process-message`

Manually process a conversation turn (useful for testing or as a fallback).

**Request Body:**
```json
{
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "transcript": "Hello, I am interested in your insurance plans.",
  "context": "Additional context for this turn (optional)"
}
```

**Response:**
```json
{
  "role": "assistant",
  "content": "Hello! I'd be happy to help you with insurance options. Can you tell me a bit more about what you're looking for?"
}
```

**Notes:**
- This endpoint allows you to inject a message into an ongoing conversation.
- The AI will process the transcript, retrieve relevant knowledge from the RAG system, and generate a response.
- Primarily used for debugging or testing the AI agent outside of a live call.

### 5. End Call
**POST** `/api/v1/end-call/{call_sid}`

Manually end a call and retrieve the final result.

**URL Parameters:**
- `call_sid`: The Twilio Call SID of the call to end.

**Response:**
```json
{
  "status": "completed",
  "outcome": "appointment",
  "summary": "The customer expressed interest in health insurance and requested an appointment for tomorrow at 2 PM.",
  "transcript": [
    {"role": "user", "content": "Hello, I'm looking for health insurance."},
    {"role": "assistant", "content": "Hello! I'd be happy to help you find the right plan..."},
    // ... full conversation
  ],
  "appointment_created": true
}
```

**Possible Outcomes:**
- `interested`: Customer showed interest but did not request an appointment
- `booked` / `appointment`: Customer requested and an appointment was booked
- `not_interested`: Customer declined or showed no interest
- `objection`: Customer raised specific objections (price, timing, etc.)
- `callback_request`: Customer asked to be called back later

### 6. Upload Knowledge Base File
**POST** `/api/v1/upload-knowledge`

Upload a DOCX file to the knowledge base for the RAG (Retrieval-Augmented Generation) system.

**Request:**
- Form-data with a file field named `file` containing a `.docx` file.

**Response:**
```json
{
  "status": "success",
  "message": "File sample_policy.docx indexed successfully."
}
```

**Notes:**
- Only `.docx` files are accepted.
- Upon upload, the RAG index is automatically rebuilt to include the new document.
- The knowledge base directory is configured via `KNOWLEDGE_BASE_DIR` in `.env` (default: `knowledge`).

## Authentication & Security

- The API does not implement authentication by design for simplicity in controlled environments.
- For production, consider placing the service behind an API gateway, VPN, or adding middleware for authentication.
- All sensitive credentials (API keys, etc.) are managed via environment variables (`.env` file).

## Environment Variables

Key environment variables that affect API behavior:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required for GPT-4 and optional TTS |
| `OPENAI_MODEL` | GPT-4 model to use (default: `gpt-4-turbo-preview`) |
| `OPENAI_TTS_MODEL` | TTS model (default: `tts-1`) |
| `OPENAI_TTS_VOICE` | TTS voice (default: `alloy`) |
| `ELEVENLABS_API_KEY` | Optional - enables premium ElevenLabs voice |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID (default: `21m00Tcm4TlvDq8ikWAM`) |
| `TWILIO_ACCOUNT_SID` | Required for Twilio telephony |
| `TWILIO_AUTH_TOKEN` | Required for Twilio telephony |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number (E.164 format) |
| `WHISPER_MODEL` | Whisper model size (default: `base`) |
| `WHISPER_DEVICE` | Device for Whisper (`cpu` or `cuda`, default: `cpu`) |
| `WHISPER_COMPUTE_TYPE` | Compute type for Whisper (default: `float32`) |
| `GHL_API_KEY` | Optional - for GoHighLevel CRM integration |
| `GHL_LOCATION_ID` | Optional - GoHighLevel Location ID |
| `KNOWLEDGE_BASE_DIR` | Directory for DOCX knowledge files (default: `knowledge`) |
| `EMBEDDING_MODEL` | Sentence transformer model for RAG (default: `all-MiniLM-L6-v2`) |

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (e.g., call not found for end-call)
- `500`: Internal Server Error (with error message in JSON response)

Error responses follow the format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Example Workflow

1. **Start a call:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/start-call" \
        -H "Content-Type: application/json" \
        -d '{"lead":{"name":"Jane Smith","phone_number":"+15551234567","context":"Needs life insurance quote"}}'
   ```

2. **Twilio calls your number** -> Your Twilio webhook is configured to point to `https://yourdomain.com/api/v1/webhook/twilio`

3. **During the call:**
   - Twilio sends media chunks to the webhook
   - Service transcribes with Whisper
   - AI agent generates response using GPT-4 + RAG
   - Response converted to speech (OpenAI or ElevenLabs TTS)
   - Audio sent back to Twilio to play to the customer

4. **End the call** (manually or when customer hangs up):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/end-call/CAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
   ```
   Returns the full call outcome, transcript, and whether an appointment was booked.

## Interactive Documentation

When the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These provide live, interactive documentation with the ability to test endpoints directly.
