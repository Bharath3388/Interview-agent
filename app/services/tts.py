import io
import logging

import numpy as np
import soundfile as sf
from kokoro import KPipeline

from app.config import settings

logger = logging.getLogger(__name__)


class KokoroTTS:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        logger.info("Loading Kokoro TTS pipeline (lang=%s, voice=%s)...",
                     settings.TTS_LANGUAGE, settings.TTS_VOICE)
        self.pipeline = KPipeline(lang_code=settings.TTS_LANGUAGE)
        self.voice = settings.TTS_VOICE
        self._initialized = True
        logger.info("Kokoro TTS ready.")

    async def synthesize(self, text: str, speed: float = 1.0) -> bytes:
        """Generate WAV audio bytes from text."""
        if not text.strip():
            return b""

        audio_segments = []
        for _gs, _ps, audio in self.pipeline(
            text, voice=self.voice, speed=speed, split_pattern=r"\n+"
        ):
            if audio is not None:
                audio_segments.append(audio)

        if not audio_segments:
            return b""

        full_audio = np.concatenate(audio_segments)

        buf = io.BytesIO()
        sf.write(buf, full_audio, 24000, format="WAV")
        buf.seek(0)
        return buf.read()

    async def stream_chunks(self, text: str, speed: float = 1.0):
        """Yield WAV audio chunks for streaming playback."""
        for _gs, _ps, audio in self.pipeline(
            text, voice=self.voice, speed=speed
        ):
            if audio is not None:
                buf = io.BytesIO()
                sf.write(buf, audio, 24000, format="WAV")
                buf.seek(0)
                yield buf.read()
