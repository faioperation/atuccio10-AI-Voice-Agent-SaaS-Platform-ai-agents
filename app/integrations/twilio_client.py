import asyncio
import base64
import json
import uuid
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from app.config import settings
from app.utils.logger import logger

class TwilioVoiceClient:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, Callable] = defaultdict(list)
    
    async def initiate_call(
        self,
        phone_number: str,
        customer_name: str,
        on_speech: Optional[Callable] = None,
        on_call_end: Optional[Callable] = None
    ) -> Dict[str, Any]:
        call_id = str(uuid.uuid4())
        
        self.active_calls[call_id] = {
            "phone_number": phone_number,
            "customer_name": customer_name,
            "status": "initiated",
            "transcript": [],
            "on_speech": on_speech,
            "on_call_end": on_call_end
        }
        
        logger.info(f"Initiating call {call_id} to {phone_number}")
        
        return {
            "call_sid": call_id,
            "status": "initiated",
            "message": f"Call initiated to {phone_number}"
        }
    
    async def generate_twiml(self, call_sid: str) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://your-server.com/api/v1/stream/{call_sid}" />    
    </Connect>
</Response>"""
    
    async def handle_webhook(self, call_sid: str, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("EventType")
        
        if call_sid not in self.active_calls:
            return {"status": "error", "message": "Call not found"}
        
        call = self.active_calls[call_sid]
        
        if event_type == "call Initiated":
            call["status"] = "ringing"
        elif event_type == "call.answered":
            call["status"] = "in-progress"
        elif event_type == "call.hangup":
            call["status"] = "completed"
            if call.get("on_call_end"):
                await call["on_call_end"](call_sid, call)
        elif event_type == "stream":
            if event.get("event") == "media":
                audio_data = event.get("media", {}).get("payload")
                if audio_data and call.get("on_speech"):
                    text = base64.b64decode(audio_data).decode("mulaw")
                    await call["on_speech"](call_sid, text)
        
        return {"status": "ok"}
    
    async def end_call(self, call_sid: str) -> Dict[str, Any]:
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["status"] = "ended"
            return {"status": "success", "message": "Call ended"}
        return {"status": "error", "message": "Call not found"}
    
    def get_call(self, call_sid: str) -> Optional[Dict[str, Any]]:
        return self.active_calls.get(call_sid)
    
    def remove_call(self, call_sid: str):
        if call_sid in self.active_calls:
            del self.active_calls[call_sid]

twilio_client = TwilioVoiceClient()