from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class LeadData(BaseModel):
    name: str
    phone_number: str
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IntegrationConfig(BaseModel):
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    ghl_api_key: Optional[str] = None
    ghl_location_id: Optional[str] = None

class CallInitiateRequest(BaseModel):
    lead: LeadData
    integrations: Optional[IntegrationConfig] = None

class CallResponse(BaseModel):
    status: str
    call_id: Optional[str] = None
    message: str

class VapiWebhookEvent(BaseModel):
    message: Dict[str, Any]

class MessageProcessRequest(BaseModel):
    call_id: str
    transcript: str
    context: Optional[str] = None

class CallResult(BaseModel):
    status: str = "completed"
    outcome: str  # interested / booked / not_interested
    summary: str
    transcript: List[Dict[str, str]]
    appointment_created: bool = False
