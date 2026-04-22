import asyncio
import aiohttp
import base64
from typing import Optional
from app.config import settings
from app.utils.logger import logger

class ElevenLabsTTSClient:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"
    
    async def generate_speech(self, text: str) -> bytes:
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs TTS Error: {response.status} - {error_text}")
                        raise Exception(f"ElevenLabs TTS failed: {response.status}")
                    
                    return await response.read()
            except Exception as e:
                logger.error(f"ElevenLabs TTS Request Error: {str(e)}")
                raise
    
    async def generate_speech_base64(self, text: str) -> str:
        audio = await self.generate_speech(text)
        return base64.b64encode(audio).decode("utf-8")
    
    async def stream_speech(self, text: str):
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}/stream"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs TTS Stream Error: {response.status} - {error_text}")
                        raise Exception(f"ElevenLabs TTS stream failed: {response.status}")
                    
                    async for chunk in response.content.iter_chunked(1024):
                        yield chunk
            except Exception as e:
                logger.error(f"ElevenLabs TTS Stream Request Error: {str(e)}")
                raise

elevenlabs_tts_client = ElevenLabsTTSClient()