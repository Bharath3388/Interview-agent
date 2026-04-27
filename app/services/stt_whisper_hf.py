"""Speech-to-text using HuggingFace Transformers Whisper pipeline (openai/whisper-large-v3)."""

import asyncio
import logging
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

logger = logging.getLogger(__name__)

_MODEL_ID = "distil-whisper/distil-large-v3"

# Interview-domain prompt for better accuracy
_INTERVIEW_PROMPT = (
    "This is a job interview. The candidate is answering technical and behavioral questions "
    "about their experience, skills, and projects."
)


def _build_pipeline():
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    logger.info("Loading Whisper model %s on %s ...", _MODEL_ID, device)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        _MODEL_ID,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(_MODEL_ID)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )
    logger.info("Whisper pipeline ready.")
    return pipe


# Singleton — loaded lazily on first use
_pipe = None


def _get_pipeline():
    global _pipe
    if _pipe is None:
        _pipe = _build_pipeline()
    return _pipe


class WhisperHFSTT:
    def _convert_to_wav(self, audio_bytes: bytes) -> bytes | None:
        """Convert WebM/Opus browser audio to 16 kHz mono WAV."""
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            webm_path = f.name
        wav_path = webm_path.replace(".webm", ".wav")
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", webm_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    wav_path,
                ],
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning("ffmpeg failed: %s", result.stderr.decode())
                return None
            if os.path.getsize(wav_path) < 1024:
                logger.warning("Converted WAV too small — likely silence")
                return None
            with open(wav_path, "rb") as wf:
                return wf.read()
        except Exception as e:
            logger.warning("ffmpeg conversion error: %s", e)
            return None
        finally:
            os.unlink(webm_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)

    def _run_pipeline(self, audio_array: np.ndarray) -> str:
        sample = {"array": audio_array, "sampling_rate": 16000}
        result = _get_pipeline()(
            sample,
            return_timestamps=True,  # required for audio > 30s; supports up to ~2 min
            chunk_length_s=30,       # process in 30-second chunks for long-form audio
            generate_kwargs={
                "language": "english",
                "temperature": 0.0,
            },
        )
        return result["text"].strip()

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe WebM/Opus audio bytes to text."""
        logger.info("Received audio: %d bytes", len(audio_bytes))

        if len(audio_bytes) < 512:
            logger.warning("Audio too small — likely silence/empty")
            return ""

        wav_bytes = self._convert_to_wav(audio_bytes)
        if not wav_bytes:
            logger.error("Audio conversion failed — cannot transcribe")
            return ""

        # Read WAV bytes into numpy array
        import io
        audio_array, _ = sf.read(io.BytesIO(wav_bytes), dtype="float32")

        # Run the blocking pipeline in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        try:
            transcript = await loop.run_in_executor(None, self._run_pipeline, audio_array)
            logger.debug("Transcript: %r", transcript)
            return transcript
        except Exception as e:
            logger.error("Whisper HF STT error: %s", e)
            return ""
