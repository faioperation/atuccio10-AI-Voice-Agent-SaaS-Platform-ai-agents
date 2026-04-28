import asyncio
import base64
import json
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from app.config import settings
from app.utils.logger import logger


class TwilioVoiceClient:
    def __init__(self):
        self.account_sid  = settings.TWILIO_ACCOUNT_SID
        self.auth_token   = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        # Real Twilio REST client
        self.client = Client(self.account_sid, self.auth_token)
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, list] = defaultdict(list)

    async def initiate_call(
        self,
        phone_number: str,
        customer_name: str,
        on_speech: Optional[Callable] = None,
        on_call_end: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Trigger a real Twilio outbound call."""
        base_url      = settings.SERVER_BASE_URL.rstrip("/")
        twiml_url     = f"{base_url}{settings.API_V1_STR}/twiml/{{call_sid}}"
        status_cb_url = f"{base_url}{settings.API_V1_STR}/webhook/twilio"

        loop = asyncio.get_event_loop()

        def _make_call():
            return self.client.calls.create(
                to=phone_number,
                from_=self.phone_number,
                # Twilio replaces {call_sid} with the actual CallSid automatically
                # via TwiML — we point to our /twiml endpoint that builds the XML
                url=f"{base_url}{settings.API_V1_STR}/twiml/placeholder",
                status_callback=status_cb_url,
                status_callback_method="POST",
                status_callback_event=["initiated", "ringing", "answered", "completed"],
            )

        call = await loop.run_in_executor(None, _make_call)
        call_sid = call.sid

        self.active_calls[call_sid] = {
            "phone_number":  phone_number,
            "customer_name": customer_name,
            "status":        "initiated",
            "transcript":    [],
            "on_speech":     on_speech,
            "on_call_end":   on_call_end,
        }

        logger.info(f"Twilio call initiated: {call_sid} → {phone_number}")
        return {
            "call_sid": call_sid,
            "status":   "initiated",
            "message":  f"Call initiated to {phone_number}",
        }

    def generate_twiml(self, call_sid: str) -> str:
        """Return TwiML that connects the call to our WebSocket media stream."""
        base_url   = settings.SERVER_BASE_URL.rstrip("/")
        # Build wss:// URL from the server base (strip scheme)
        ws_base    = base_url.replace("https://", "wss://").replace("http://", "ws://")
        stream_url = f"{ws_base}{settings.API_V1_STR}/stream/{call_sid}"

        response = VoiceResponse()
        connect  = Connect()
        connect.append(Stream(url=stream_url))
        response.append(connect)
        return str(response)

    async def handle_webhook(self, call_sid: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch on Twilio event type and invoke registered callbacks."""
        event_type = event.get("EventType") or event.get("CallStatus", "")

        if call_sid not in self.active_calls:
            logger.warning(f"Webhook for unknown call_sid: {call_sid}")
            return {"status": "error", "message": "Call not found"}

        call = self.active_calls[call_sid]

        # Fix: was "call Initiated" (typo with space) — now canonical dot-notation
        if event_type in ("call.initiated", "initiated"):
            call["status"] = "ringing"
        elif event_type in ("call.answered", "in-progress"):
            call["status"] = "in-progress"
        elif event_type in ("call.hangup", "completed", "failed", "busy", "no-answer"):
            call["status"] = "completed"
            if call.get("on_call_end"):
                await call["on_call_end"](call_sid, call)
        elif event_type == "stream":
            if event.get("event") == "media":
                audio_payload = event.get("media", {}).get("payload")
                if audio_payload and call.get("on_speech"):
                    audio_bytes = base64.b64decode(audio_payload)
                    await call["on_speech"](call_sid, audio_bytes)

        return {"status": "ok"}

    async def end_call(self, call_sid: str) -> Dict[str, Any]:
        """Programmatically terminate a live call via Twilio API."""
        if call_sid not in self.active_calls:
            return {"status": "error", "message": "Call not found"}

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: self.client.calls(call_sid).update(status="completed"),
            )
            self.active_calls[call_sid]["status"] = "ended"
            return {"status": "success", "message": "Call ended"}
        except Exception as e:
            logger.error(f"Twilio end_call error: {e}")
            return {"status": "error", "message": str(e)}

    def get_call(self, call_sid: str) -> Optional[Dict[str, Any]]:
        return self.active_calls.get(call_sid)

    def remove_call(self, call_sid: str):
        self.active_calls.pop(call_sid, None)


twilio_client = TwilioVoiceClient()