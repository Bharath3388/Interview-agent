import io
import logging

import edge_tts

from app.config import settings

logger = logging.getLogger(__name__)

# Map old Kokoro voice settings to Edge TTS voices
EDGE_VOICE = settings.TTS_VOICE if settings.TTS_VOICE.startswith("en-") else "en-US-AvaMultilingualNeural"


class KokoroTTS:
    """TTS using Microsoft Edge's free cloud TTS (replaces local Kokoro to avoid OOM on Railway)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.voice = EDGE_VOICE
        self._initialized = True
        logger.info("Edge TTS ready (voice=%s)", self.voice)

    async def synthesize(self, text: str, speed: float = 1.0) -> bytes:
        """Generate WAV audio bytes from text."""
        if not text.strip():
            return b""

        rate = f"{int((speed - 1) * 100):+d}%"
        communicate = edge_tts.Communicate(text, self.voice, rate=rate)

        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        buf.seek(0)
        return buf.read()

    async def stream_chunks(self, text: str, speed: float = 1.0):
        """Yield audio chunks for streaming playback."""
        rate = f"{int((speed - 1) * 100):+d}%"
        communicate = edge_tts.Communicate(text, self.voice, rate=rate)

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
