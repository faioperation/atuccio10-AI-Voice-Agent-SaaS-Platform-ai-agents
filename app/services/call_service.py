import asyncio
from typing import Dict, Any, Optional, List
from app.config import settings
from app.integrations.twilio_client import twilio_client
from app.integrations.whisper_client import whisper_client
from app.integrations.openai_client import openai_client
from app.integrations.tts_client import tts_client
from app.integrations.elevenlabs_tts_client import elevenlabs_tts_client
from app.agents.calling_agent import CallingAgent
from app.schemas.call_schemas import LeadData, CallResult
from app.utils.logger import logger

# In-memory stores: call_id → agent / transcript list
active_agents:    Dict[str, CallingAgent]         = {}
call_transcripts: Dict[str, List[Dict[str, str]]] = {}


class CallService:

    # ------------------------------------------------------------------
    # Initiate
    # ------------------------------------------------------------------

    async def initiate_call(self, lead: LeadData, integrations: Any = None) -> Dict[str, Any]:
        logger.info(f"Initiating call for {lead.name} at {lead.phone_number}")

        agent = CallingAgent(
            customer_name=lead.name,
            customer_context=lead.metadata or {"context": lead.context},
        )

        response = await twilio_client.initiate_call(
            phone_number=lead.phone_number,
            customer_name=lead.name,
            on_speech=lambda cid, audio: asyncio.create_task(self.handle_audio(cid, audio)),
            on_call_end=lambda cid, call: asyncio.create_task(self.finalize_call(cid, {})),
        )

        call_id = response.get("call_sid")
        if call_id:
            active_agents[call_id]    = agent
            call_transcripts[call_id] = []
            logger.info(f"Call initiated with SID: {call_id}")

        return response

    # ------------------------------------------------------------------
    # Real-time audio handling
    # ------------------------------------------------------------------

    async def handle_audio(self, call_id: str, audio_data: bytes) -> Optional[bytes]:
        agent = active_agents.get(call_id)
        if not agent:
            return None

        try:
            transcript = await whisper_client.transcribe(audio_data)

            if not transcript.strip():
                return None

            call_transcripts[call_id].append({"role": "user", "content": transcript})

            response_text = await agent.generate_response(transcript)

            call_transcripts[call_id].append({"role": "assistant", "content": response_text})

            # Prefer ElevenLabs (premium) when API key is configured
            if settings.ELEVENLABS_API_KEY:
                audio_response = await elevenlabs_tts_client.generate_speech(response_text)
            else:
                audio_response = await tts_client.generate_speech(response_text)

            return audio_response

        except Exception as e:
            logger.error(f"Error handling audio for call {call_id}: {e}")
            return None

    # ------------------------------------------------------------------
    # Webhook dispatch
    # ------------------------------------------------------------------

    async def handle_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        call_sid = event.get("call_sid") or event.get("CallSid")
        if not call_sid:
            return {"status": "error", "message": "No call_sid provided"}

        result = await twilio_client.handle_webhook(call_sid, event)

        if event.get("EventType") in ("call.hangup", "completed"):
            return await self.finalize_call(call_sid, {})

        return result

    # ------------------------------------------------------------------
    # Finalize
    # ------------------------------------------------------------------

    async def finalize_call(self, call_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
        agent           = active_agents.pop(call_id, None)
        transcript_list = call_transcripts.pop(call_id, [])
        transcript_text = " ".join(t["content"] for t in transcript_list)

        if not agent:
            logger.warning(f"finalize_call: no agent found for {call_id}")
            return {"status": "error", "message": "Agent not found"}

        intent  = await openai_client.detect_intent(transcript_text)
        summary = await openai_client.generate_response([
            {"role": "system", "content": "Briefly summarize this sales call transcript and its outcome."},
            {"role": "user",   "content": transcript_text or "(empty call)"},
        ])

        result = CallResult(
            status="completed",
            outcome=intent,
            summary=summary.content,
            transcript=transcript_list,
            appointment_created="appointment" in intent.lower(),
        )

        twilio_client.remove_call(call_id)
        logger.info(f"Call {call_id} finalized — outcome: {intent}")
        return result.dict()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_agent(self, call_id: str) -> Optional[CallingAgent]:
        """Expose the active agent for a call (used by /process-message)."""
        return active_agents.get(call_id)


call_service = CallService()