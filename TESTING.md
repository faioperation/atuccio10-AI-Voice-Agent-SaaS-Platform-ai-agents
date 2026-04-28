# 🧪 InsureFlow — Testing Guide

End-to-end testing for the AI Outbound Calling Engine. Two tracks:

- **Track 1 — Manual** (no Twilio account, no phone needed — start here)
- **Track 2 — Real Call** (live outbound call to your phone via Twilio)

---

## Prerequisites

Start the server before running any tests:

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ Track 1 — Manual Testing (No Phone Needed)

Tests every AI layer locally: RAG retrieval, GPT-4 conversation, tool calling, intent detection, and call summarisation.

---

### Step 1 — Health Check

```bash
curl http://127.0.0.1:8000/api/v1/health
```

**Expected:**
```json
{"status": "healthy", "service": "AI Outbound Calling Engine"}
```

---

### Step 2 — Prepare a Knowledge Base Document

Create a `.docx` file in the `knowledge/` folder with sample product content:

```
InsureFlow offers three plans:
- Basic Shield: $99/month. Covers emergency care and hospitalization.
- Family Guard: $249/month. Full family coverage including dental and vision.
- Premier Plus: $499/month. Premium coverage with zero deductible and worldwide coverage.

All plans include 24/7 nurse hotline and telehealth visits.
Pre-existing conditions are covered after a 6-month waiting period.
```

Save it as `knowledge/insureflow_products.docx`, then upload via API:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/upload-knowledge \
     -F "file=@knowledge/insureflow_products.docx"
```

**Expected:**
```json
{"status": "success", "message": "File insureflow_products.docx indexed successfully."}
```

The FAISS index is now saved to disk — the next server restart loads it instantly.

---

### Step 3 — Start a Simulated Call

```bash
curl -X POST http://127.0.0.1:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -d '{
       "lead": {
         "name": "John Smith",
         "phone_number": "+10000000000",
         "context": "Looking for family health insurance",
         "metadata": {
           "contact_id": "TEST_CONTACT_001",
           "calendar_id": "TEST_CALENDAR_001"
         }
       }
     }'
```

**Expected:**
```json
{"status": "success", "call_sid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "message": "Call initiated successfully"}
```

> Copy the `call_sid` — you'll need it for all following steps.

> **Note:** With real Twilio credentials in `.env`, this will also place a real phone call. With placeholder credentials, only the in-memory agent is created (Twilio will error, but the agent still exists).

---

### Step 4 — Chat With the AI via `/process-message`

This is the core AI test. Each call exercises: RAG retrieval → GPT-4 → conversation history → tool calling.

```bash
# Turn 1 — Greeting
curl -X POST http://127.0.0.1:8000/api/v1/process-message \
     -H "Content-Type: application/json" \
     -d '{
       "call_sid": "PASTE_CALL_SID_HERE",
       "transcript": "Hi, I am looking for health insurance for my family of 4."
     }'

# Turn 2 — Ask about products (tests RAG)
curl -X POST http://127.0.0.1:8000/api/v1/process-message \
     -H "Content-Type: application/json" \
     -d '{
       "call_sid": "PASTE_CALL_SID_HERE",
       "transcript": "What plans do you have and how much do they cost?"
     }'

# Turn 3 — Book appointment (triggers GPT-4 tool calling → GHL)
curl -X POST http://127.0.0.1:8000/api/v1/process-message \
     -H "Content-Type: application/json" \
     -d '{
       "call_sid": "PASTE_CALL_SID_HERE",
       "transcript": "I am interested! Can we book an appointment for tomorrow at 2 PM?"
     }'
```

**Expected for Turn 2:** Response mentions plan names and prices from your DOCX.  
**Expected for Turn 3:** Response acknowledges appointment booking.

---

### Step 5 — End the Call and Verify the Result

```bash
curl -X POST http://127.0.0.1:8000/api/v1/end-call/PASTE_CALL_SID_HERE
```

**Expected:**
```json
{
  "status": "completed",
  "outcome": "APPOINTMENT_REQUEST",
  "summary": "Customer John Smith expressed interest in family health insurance...",
  "transcript": [...],
  "appointment_created": true
}
```

---

### Step 6 — Use Swagger UI

Open **http://127.0.0.1:8000/docs** in your browser to run all the above steps interactively with a visual interface.

---

### Manual Test Checklist

| # | Test | Pass Criteria |
|---|---|---|
| 1 | `GET /health` | `{"status": "healthy"}` |
| 2 | Upload DOCX | `indexed successfully` |
| 3 | `POST /start-call` | Returns a `call_sid` |
| 4 | AI responds to greeting | Non-empty `content` field |
| 5 | AI uses RAG (ask about plans) | Mentions plan names/prices from your DOCX |
| 6 | Appointment tool fires | Response acknowledges booking |
| 7 | `POST /end-call` | `outcome` is one of the 5 intent classes |
| 8 | Call summary | Non-empty `summary` field |

---

## 📞 Track 2 — Real Call Testing (With Twilio)

### Prerequisites

| Requirement | Where to Get |
|---|---|
| Twilio account | [twilio.com](https://www.twilio.com) — free trial includes ~$15 credit |
| Twilio phone number | Twilio Console → Phone Numbers → Buy a Number |
| ngrok | [ngrok.com](https://ngrok.com) — free tier |
| OpenAI API key | [platform.openai.com](https://platform.openai.com) |

---

### Step 1 — Fill In Your `.env`

```bash
OPENAI_API_KEY=sk-your-real-key

TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+15551234567

# Fill in after Step 2
SERVER_BASE_URL=https://XXXX-XX-XX-XX-XX.ngrok-free.app
```

---

### Step 2 — Expose Your Local Server with ngrok

Open a **second terminal**:

```bash
# Install ngrok
brew install ngrok/ngrok/ngrok

# Authenticate (one-time — get your token from ngrok dashboard)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL from ngrok's output.

---

### Step 3 — Update `.env` and Restart

```bash
SERVER_BASE_URL=https://xxxx.ngrok-free.app
```

Restart the server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 4 — Verify Public Access

```bash
curl https://xxxx.ngrok-free.app/api/v1/health
```

Expected: `{"status": "healthy", ...}`

---

### Step 5 — Trigger a Real Outbound Call

Replace `+1YOUR_PHONE` with your own mobile number:

```bash
curl -X POST https://xxxx.ngrok-free.app/api/v1/start-call \
     -H "Content-Type: application/json" \
     -d '{
       "lead": {
         "name": "Test User",
         "phone_number": "+1YOUR_PHONE_NUMBER",
         "context": "Testing the AI calling engine"
       }
     }'
```

**What happens automatically:**
```
1. Server calls Twilio API → Twilio dials your phone
2. You answer → Twilio fetches TwiML from /twiml/{call_sid}
3. TwiML opens WebSocket to /stream/{call_sid}
4. Your speech → Whisper STT → GPT-4 + RAG → TTS → played back to you
5. On hangup → intent detected → summary generated → result stored
```

---

### Step 6 — Monitor Server Logs

Watch the uvicorn terminal during the call:

```
INFO  | call_service:initiate_call     - Initiating call for Test User at +1...
INFO  | twilio_client:initiate_call    - Twilio call initiated: CAxxxxxxx → +1...
INFO  | endpoints:websocket_stream     - WebSocket stream connected for call: CAxxxxxxx
INFO  | endpoints:websocket_stream     - Twilio stream started — call: CAxxxxxxx
INFO  | endpoints:websocket_stream     - Twilio stream stopped — call: CAxxxxxxx
INFO  | call_service:finalize_call     - Call CAxxxxxxx finalized — outcome: APPOINTMENT_REQUEST
```

---

### Step 7 — Retrieve the Call Result

```bash
curl -X POST http://localhost:8000/api/v1/end-call/CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🔒 Testing API Authentication

If `API_SECRET_KEY=mysecret` is set in `.env`:

```bash
# Should return 401:
curl http://localhost:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -d '{"lead":{"name":"X","phone_number":"+1"}}'

# Should work (X-API-Key header):
curl http://localhost:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -H "X-API-Key: mysecret" \
     -d '{"lead":{"name":"X","phone_number":"+1"}}'

# Should work (Bearer token):
curl http://localhost:8000/api/v1/start-call \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer mysecret" \
     -d '{"lead":{"name":"X","phone_number":"+1"}}'
```

---

## 🛠️ Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `401 Unauthorized` | API key not sent | Add `X-API-Key: your-key` header |
| `404` on `/process-message` | No active agent for that call_sid | Call `/start-call` first |
| Twilio `Error 20003` | Wrong Account SID / Auth Token | Check Twilio console |
| Twilio `Error 21211` | Invalid `to` number | Use E.164 format: `+15551234567` |
| Twilio `Error 21212` | Invalid `from` number | Must match your Twilio number exactly |
| WebSocket not connecting | Wrong ngrok URL in `.env` | Verify `SERVER_BASE_URL` matches ngrok |
| Whisper returns empty | No speech / VAD filter | Speak clearly; avoid long silences |
| RAG returns no context | No DOCX in `knowledge/` | Upload via `/upload-knowledge` |
| AI doesn't mention products | DOCX not indexed yet | Re-upload after placing file in `knowledge/` |
| `APPOINTMENT_REQUEST` not detected | Vague phrasing | Say "I want to book an appointment for [time]" |

---

## Recommended Test Order

```
Track 1 (5 min):
  Health → Upload DOCX → start-call → process-message ×3 → end-call

Track 2 (15 min):
  Fill .env → ngrok up → Restart server → Verify /health via ngrok
  → start-call → Answer phone → Talk naturally → Hang up
  → Check logs → end-call → Review outcome
```
