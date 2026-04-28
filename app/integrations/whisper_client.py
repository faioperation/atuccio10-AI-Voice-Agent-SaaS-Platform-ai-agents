import asyncio
import io
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel
from app.config import settings
from app.utils.logger import logger

# audioop is built-in for Python ≤ 3.12; removed in 3.13.
# We provide a pure-numpy μ-law fallback so the code works on all versions.
try:
    import audioop
    _HAS_AUDIOOP = True
except ImportError:
    _HAS_AUDIOOP = False
    logger.warning("audioop not available (Python 3.13+). Using pure-numpy μ-law decoder.")


def _mulaw_to_float32(mulaw_bytes: bytes) -> np.ndarray:
    """
    Convert 8-bit μ-law encoded bytes (as sent by Twilio) to a float32
    numpy array normalised to [-1.0, 1.0] at 8 kHz, suitable for Whisper.

    Two paths:
      1. audioop (fast, built-in, Python ≤ 3.12)
      2. Pure-numpy ITU G.711 μ-law decoder (Python 3.13+)
    """
    if _HAS_AUDIOOP:
        # audioop.ulaw2lin converts μ-law → signed 16-bit PCM bytes
        pcm_bytes = audioop.ulaw2lin(mulaw_bytes, 2)          # 2 = 16-bit width
        samples   = np.frombuffer(pcm_bytes, dtype=np.int16)
        return samples.astype(np.float32) / 32768.0

    # --- Pure-numpy G.711 μ-law decoder ---
    BIAS = 33
    mulaw = np.frombuffer(mulaw_bytes, dtype=np.uint8)
    mulaw = ~mulaw & 0xFF                                      # invert all bits
    sign     = mulaw & 0x80
    exponent = (mulaw & 0x70) >> 4
    mantissa = mulaw & 0x0F
    sample   = ((mantissa << 3) + BIAS) << exponent
    # Restore sign
    sample   = np.where(sign != 0, -sample, sample).astype(np.int16)
    return sample.astype(np.float32) / 32768.0


class WhisperClient:
    """Local speech-to-text using FasterWhisper (no audio sent to external APIs)."""

    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_name   = settings.WHISPER_MODEL
        self.device       = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE

    def load_model(self):
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name} on {self.device}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded successfully.")

    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        """
        Transcribe raw μ-law audio bytes (as streamed by Twilio).

        The bytes are first decoded to a float32 numpy array so that
        FasterWhisper can process them directly without temp-file I/O.
        """
        self.load_model()

        # Convert mulaw bytes → float32 numpy array
        audio_array = _mulaw_to_float32(audio_data)

        loop = asyncio.get_event_loop()

        def _transcribe_sync():
            segments, _ = self.model.transcribe(
                audio_array,
                language=language,
                beam_size=1,
                vad_filter=True,
            )
            return " ".join(seg.text for seg in segments)

        return await loop.run_in_executor(None, _transcribe_sync)

    async def transcribe_audio_file(self, file_path: str, language: str = "en") -> str:
        """Transcribe from a file path (used in batch/testing scenarios)."""
        self.load_model()

        loop = asyncio.get_event_loop()

        def _transcribe_sync():
            segments, _ = self.model.transcribe(
                file_path,
                language=language,
                beam_size=1,
                vad_filter=True,
            )
            return " ".join(seg.text for seg in segments)

        return await loop.run_in_executor(None, _transcribe_sync)


whisper_client = WhisperClient()