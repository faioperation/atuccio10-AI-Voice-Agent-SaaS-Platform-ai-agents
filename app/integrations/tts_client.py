import asyncio
import io
import base64
from typing import Optional
import openai
from app.config import settings
from app.utils.logger import logger

class TTSClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_TTS_MODEL
        self.voice = settings.OPENAI_TTS_VOICE
    
    async def generate_speech(self, text: str) -> bytes:
        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="ulaw"
            )
            audio_bytes = await response.aread()
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS Error: {str(e)}")
            raise
    
    async def generate_speech_base64(self, text: str) -> str:
        audio = await self.generate_speech(text)
        return base64.b64encode(audio).decode("utf-8")
    
    async def stream_speech(self, text: str):
        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="ulaw"
            )
            async for chunk in response.aiter_bytes(chunk_size=1024):
                yield chunk
        except Exception as e:
            logger.error(f"TTS Stream Error: {str(e)}")
            raise

tts_client = TTSClient()