import asyncio
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from app.config import settings
from app.utils.logger import logger

class WhisperClient:
    def __init__(self):
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE
    
    def load_model(self):
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("Whisper model loaded successfully")
    
    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        self.load_model()
        
        loop = asyncio.get_event_loop()
        
        def transcribe_sync():
            segments, _ = self.model.transcribe(
                audio_data,
                language=language,
                beam_size=1,
                vad_filter=True
            )
            return " ".join([seg.text for seg in segments])
        
        return await loop.run_in_executor(None, transcribe_sync)
    
    async def transcribe_audio_file(self, file_path: str, language: str = "en") -> str:
        self.load_model()
        
        loop = asyncio.get_event_loop()
        
        def transcribe_sync():
            segments, _ = self.model.transcribe(
                file_path,
                language=language,
                beam_size=1,
                vad_filter=True
            )
            return " ".join([seg.text for seg in segments])
        
        return await loop.run_in_executor(None, transcribe_sync)

whisper_client = WhisperClient()