import aiohttp
import base64
from typing import Optional, AsyncIterator
from app.config import settings
from app.utils.logger import logger

# ElevenLabs output format that matches what Twilio expects:
# μ-law 8kHz mono — same as OpenAI TTS "ulaw" response_format.
_TWILIO_COMPATIBLE_FORMAT = "ulaw_8000"


class ElevenLabsTTSClient:
    """
    ElevenLabs Text-to-Speech client.

    Outputs audio in μ-law 8 kHz format (ulaw_8000) which is directly
    compatible with Twilio Media Streams — no transcoding required.
    """

    def __init__(self):
        self.api_key  = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"

    def _build_url(self, path: str) -> str:
        """Append output_format query param for Twilio compatibility."""
        return f"{self.base_url}{path}?output_format={_TWILIO_COMPATIBLE_FORMAT}"

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "xi-api-key":   self.api_key,
            # audio/basic is the MIME type for μ-law audio
            "Accept":       "audio/basic",
        }

    def _payload(self, text: str) -> dict:
        return {
            "text":     text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability":        0.5,
                "similarity_boost": 0.5,
            },
        }

    async def generate_speech(self, text: str) -> bytes:
        """Return μ-law audio bytes (Twilio-ready) for the given text."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured.")

        url = self._build_url(f"/text-to-speech/{self.voice_id}")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=self._payload(text), headers=self._headers()) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"ElevenLabs TTS error {resp.status}: {error_text}")
                        raise Exception(f"ElevenLabs TTS failed with status {resp.status}")
                    return await resp.read()
            except Exception as e:
                logger.error(f"ElevenLabs TTS request error: {e}")
                raise

    async def generate_speech_base64(self, text: str) -> str:
        """Return Base64-encoded μ-law audio (for embedding in JSON payloads)."""
        audio = await self.generate_speech(text)
        return base64.b64encode(audio).decode("utf-8")

    async def stream_speech(self, text: str) -> AsyncIterator[bytes]:
        """Stream μ-law audio chunks directly (for low-latency playback)."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured.")

        url = self._build_url(f"/text-to-speech/{self.voice_id}/stream")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=self._payload(text), headers=self._headers()) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"ElevenLabs TTS stream error {resp.status}: {error_text}")
                        raise Exception(f"ElevenLabs TTS stream failed with status {resp.status}")
                    async for chunk in resp.content.iter_chunked(1024):
                        yield chunk
            except Exception as e:
                logger.error(f"ElevenLabs TTS stream request error: {e}")
                raise


elevenlabs_tts_client = ElevenLabsTTSClient()