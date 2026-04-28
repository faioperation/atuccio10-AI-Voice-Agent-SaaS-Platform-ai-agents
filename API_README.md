# InsureFlow — API Reference

Complete reference for all REST and WebSocket endpoints.

**Base URL:** `/api/v1` | **Docs:** `/docs` (Swagger) · `/redoc`

---

## Authentication

When `API_SECRET_KEY` is set in `.env`, all endpoints except `/health` and `/webhook/twilio` require:

```
X-API-Key: your-secret-key
# OR
Authorization: Bearer your-secret-key
```

---

## Endpoints

### 1. Health Check — `GET /api/v1/health`

```json
{"status": "healthy", "service": "AI Outbound Calling Engine"}
```

---

### 2. Start Outbound Call — `POST /api/v1/start-call`

Triggers a real Twilio outbound call and initialises an AI agent for the lead.

**Request:**
```json
{
  "lead": {
    "name": "John Doe",
    "phone_number": "+1234567890",
    "context": "Interested in health insurance for a family of 4.",
    "metadata": {
      "contact_id": "GHL contact ID (optional)",
      "calendar_id": "GHL calendar ID (optional)"
    }
  }
}
```

**Response `200`:**
```json
{
  "status": "success",
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "Call initiated successfully"
}
```

> `SERVER_BASE_URL` must point to a publicly reachable URL so Twilio can reach your `/twiml` and `/stream` endpoints.

---

### 3. TwiML — `GET /api/v1/twiml/{call_sid}`

Returns XML that Twilio fetches when the call is answered. Tells Twilio to open a WebSocket Media Stream.

**Response `200` (`application/xml`):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://your-server.com/api/v1/stream/CAxxxx" />
  </Connect>
</Response>
```

> Called automatically by Twilio — you do not need to call this yourself.

---

### 4. WebSocket Media Stream — `WS /api/v1/stream/{call_sid}`

Real-time Twilio Media Streams WebSocket. Handles the full AI audio loop.

**Inbound events from Twilio:**

| Event | Description |
|---|---|
| `connected` | Handshake confirmed |
| `start` | Stream live |
| `media` | Audio chunk: `{"media": {"payload": "<base64-mulaw>"}}` |
| `stop` | Call ended → triggers `finalize_call()` |

**Pipeline per `media` event:**
1. Base64 decode → μ-law bytes
2. μ-law → float32 numpy → **FasterWhisper** (local STT)
3. **GPT-4 + RAG** → response text
4. **TTS** (OpenAI or ElevenLabs) → μ-law audio
5. Audio sent back to Twilio

---

### 5. Twilio Webhook — `POST /api/v1/webhook/twilio`

Handles Twilio status callbacks. Always auth-exempt.

**Request:**
```json
{
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "event": {"CallStatus": "completed", "EventType": "call.hangup"}
}
```

**Handled events:** `initiated` · `in-progress` · `completed` · `call.hangup` · `failed` · `busy` · `no-answer`

---

### 6. Process Message — `POST /api/v1/process-message`

Manually inject a transcript turn into an active call's AI agent. Use for testing without a real phone call.

**Request:**
```json
{
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "transcript": "I'd like to book an appointment for tomorrow at 2 PM."
}
```

**Response `200`:**
```json
{"role": "assistant", "content": "Excellent! I can book that right away..."}
```

**Response `404`:** No active agent found — call `POST /start-call` first.

---

### 7. End Call — `POST /api/v1/end-call/{call_sid}`

Finalise a call and get the full outcome report.

**Response `200`:**
```json
{
  "status": "completed",
  "outcome": "APPOINTMENT_REQUEST",
  "summary": "Customer requested an appointment for tomorrow at 2 PM.",
  "transcript": [
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "appointment_created": true
}
```

**Possible `outcome` values:**

| Value | Meaning |
|---|---|
| `INTERESTED` | Showed interest, no booking yet |
| `APPOINTMENT_REQUEST` | Appointment booked |
| `NOT_INTERESTED` | Declined |
| `OBJECTION` | Raised specific objection |
| `CALLBACK_REQUEST` | Asked to be called back |

---

### 8. Upload Knowledge — `POST /api/v1/upload-knowledge`

Upload a `.docx` file to rebuild the RAG index (saved to disk automatically).

```bash
curl -X POST http://localhost:8000/api/v1/upload-knowledge \
     -H "X-API-Key: your-key" \
     -F "file=@products.docx"
```

**Response `200`:**
```json
{"status": "success", "message": "File products.docx indexed successfully."}
```

**Response `400`:** Only `.docx` files accepted.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ | — | GPT-4 + TTS |
| `TWILIO_ACCOUNT_SID` | ✅ | — | Twilio SID |
| `TWILIO_AUTH_TOKEN` | ✅ | — | Twilio token |
| `TWILIO_PHONE_NUMBER` | ✅ | — | Caller ID (E.164) |
| `SERVER_BASE_URL` | ✅ | — | Public URL for Twilio webhooks |
| `OPENAI_MODEL` | No | `gpt-4-turbo-preview` | Model version |
| `OPENAI_TTS_MODEL` | No | `tts-1` | TTS model |
| `OPENAI_TTS_VOICE` | No | `alloy` | TTS voice |
| `ELEVENLABS_API_KEY` | No | _(none)_ | Enables premium voice |
| `ELEVENLABS_VOICE_ID` | No | `21m00Tcm4TlvDq8ikWAM` | Voice |
| `WHISPER_MODEL` | No | `base` | `tiny`/`base`/`small`/`medium` |
| `WHISPER_DEVICE` | No | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | No | `float32` | Precision |
| `GHL_API_KEY` | No | _(none)_ | GoHighLevel CRM |
| `GHL_LOCATION_ID` | No | _(none)_ | GHL Location |
| `GHL_API_BASE_URL` | No | `https://services.leadconnectorhq.com` | GHL URL |
| `KNOWLEDGE_BASE_DIR` | No | `knowledge` | DOCX directory |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | RAG embeddings |
| `ALLOWED_ORIGINS` | No | `*` | CORS origins (comma-separated) |
| `API_SECRET_KEY` | No | _(none)_ | Enables API auth |

---

## Error Handling

| Code | Meaning |
|---|---|
| `200` | Success |
| `400` | Bad request |
| `401` | Invalid/missing API key |
| `404` | Resource not found |
| `500` | Internal server error |

```json
{"detail": "Descriptive error message"}
```

---

## Quick Examples

**Real call:**
```bash
curl -X POST http://localhost:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-key" \
     -d '{"lead":{"name":"Jane Smith","phone_number":"+15551234567","context":"Needs life insurance"}}'
```

**Manual AI test:**
```bash
# Start call → get call_sid
curl -X POST http://localhost:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -d '{"lead":{"name":"Test","phone_number":"+10000000000","context":"test"}}'

# Chat with the AI
curl -X POST http://localhost:8000/api/v1/process-message \
     -H "Content-Type: application/json" \
     -d '{"call_sid":"CALL_SID_HERE","transcript":"What plans do you offer?"}'

# Get results
curl -X POST http://localhost:8000/api/v1/end-call/CALL_SID_HERE
```

For a full step-by-step guide, see **[TESTING.md](./TESTING.md)**.
