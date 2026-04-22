from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class LeadData(BaseModel):
    name: str
    phone_number: str
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CallInitiateRequest(BaseModel):
    lead: LeadData

class CallResponse(BaseModel):
    status: str
    call_sid: Optional[str] = None
    message: str

class TwilioWebhookEvent(BaseModel):
    call_sid: str
    event: Dict[str, Any]

class MessageProcessRequest(BaseModel):
    call_sid: str
    transcript: str

class CallResult(BaseModel):
    status: str = "completed"
    outcome: str
    summary: str
    transcript: List[Dict[str, str]]
    appointment_created: bool = False