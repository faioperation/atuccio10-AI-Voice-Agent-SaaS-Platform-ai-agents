from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "AI Outbound Calling Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI (GPT-4 + TTS)
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TTS_MODEL: str = "tts-1"
    OPENAI_TTS_VOICE: str = "alloy"
    
    # ElevenLabs (Voice)
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = "21m00Tcm4TlvDq8ikWAM" # Default voice
    
    # Twilio (Telephony)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # FasterWhisper (Local Transcription)
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "float32"
    
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