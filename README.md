# AI Outbound Calling Engine (InsureFlow)

Production-ready standalone microservice built with FastAPI, Vapi, OpenAI, and RAG capabilities.

## 🚀 Key Features
- **Outbound AI Calling**: Trigger calls via Vapi with custom context.
- **Natural AI Intelligence**: Powered by OpenAI GPT-4 with a sales-optimized persona.
- **High-Quality Voice**: Integration with **ElevenLabs** for human-like conversations.
- **CRM Integration**: Native support for **GoHighLevel** (LeadConnector) for lead fetching and appointment booking.
- **RAG Knowledge System**: Inject product details or company context from DOCX files dynamically.
- **Intent Detection**: Automatically classifies calls as Interested, Not Interested, Objection, or Appointment Request.

## 🏗️ Project Structure
```text
/app
  /api          # FastAPI routes
  /services     # Business logic & call orchestration
  /agents       # AI persona, prompts, and logic
  /rag          # DOCX processing & retrieval engine
  /integrations # Connectors for Vapi, OpenAI, CRM
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
- `OPENAI_API_KEY`: Your OpenAI API key.
- `VAPI_API_KEY`: Your Vapi API key.
- `VAPI_ASSISTANT_ID`: The ID of your pre-configured Vapi assistant.
- `VAPI_PHONE_NUMBER_ID`: The ID of your Vapi phone number.
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key.
- `ELEVENLABS_VOICE_ID`: Your preferred ElevenLabs voice ID.
- `GHL_API_KEY`: Your GoHighLevel (LeadConnector) API key.
- `GHL_LOCATION_ID`: Your GHL Location ID.

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

### Webhook (Vapi)
`POST /api/v1/webhook/vapi`
Handle Vapi events like `call-started`, `transcript`, and `end-of-call-report`.

### Health Check
`GET /api/v1/health`

## 🧠 AI Flow
1. **Initiate**: App triggers Vapi call.
2. **Conversation**: Vapi streams voice; App provides intelligence.
3. **RAG**: For every query, the App retrieves relevant data from DOCX files.
4. **Intent**: On call end, the system analyzes the full transcript to determine the outcome.
5. **Action**: If "Appointment" intent is detected, it triggers the booking tool.

## 🛡️ Stability & Safety
- **Async Architecture**: Scalable handling of multiple concurrent calls.
- **Structured Logging**: Loguru setup for debugging and production monitoring.
- **Type Safety**: Full Pydantic validation for all API inputs and outputs.
