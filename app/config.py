import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # TTS
    TTS_VOICE: str = os.getenv("TTS_VOICE", "af_heart")
    TTS_LANGUAGE: str = os.getenv("TTS_LANGUAGE", "a")

    # Interview
    MAX_FOLLOW_UPS: int = int(os.getenv("MAX_FOLLOW_UPS", "2"))
    DEFAULT_DURATION: int = int(os.getenv("DEFAULT_DURATION", "15"))

    # Temp directory
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/interview_bot")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{str(BASE_DIR / 'interview_agent.db')}",
    )

    # Auth / JWT — generate a random secret if not provided (safe for dev, must set in prod)
    JWT_SECRET: str = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

    def __init__(self):
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        if not os.getenv("JWT_SECRET"):
            import logging
            logging.getLogger(__name__).warning(
                "JWT_SECRET not set — using random secret. Sessions will not persist across restarts."
            )


settings = Settings()
