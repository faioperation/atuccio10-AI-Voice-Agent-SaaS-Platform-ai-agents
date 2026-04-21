from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "AI Outbound Calling Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Vapi
    VAPI_API_KEY: str
    VAPI_BASE_URL: str = "https://api.vapi.ai"
    VAPI_ASSISTANT_ID: Optional[str] = None
    VAPI_PHONE_NUMBER_ID: Optional[str] = None
    
    # ElevenLabs (Voice)
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = "21m00Tcm4TlvDq8ikWAM" # Default voice
    
    # Deepgram (Transcription)
    DEEPGRAM_API_KEY: Optional[str] = None
    
    # Twilio (Telephony)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # GoHighLevel (CRM)
    GHL_API_KEY: Optional[str] = None
    GHL_LOCATION_ID: Optional[str] = None
    GHL_API_BASE_URL: str = "https://services.leadconnectorhq.com"
    
    # RAG Configuration
    KNOWLEDGE_BASE_DIR: str = "knowledge"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"

settings = Settings()
