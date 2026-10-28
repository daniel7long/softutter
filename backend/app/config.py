import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.llm_model = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
        self.stt_model = os.getenv("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")
        self.tts_model = os.getenv("OPENAI_TTS_MODEL", "tts-1")
        self.tts_voice = os.getenv("OPENAI_TTS_VOICE", "nova")
        self.azure_key = os.getenv("AZURE_SPEECH_KEY", "").strip()
        self.azure_region = os.getenv("AZURE_SPEECH_REGION", "").strip()
        self.force_mock = os.getenv("SOFTUTTER_MOCK", "0") == "1"
        self.cors_origins = [
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if o.strip()
        ]
        # Set a long random MCP_TOKEN to expose the MCP server at /mcp (off when empty).
        self.mcp_token = os.getenv("MCP_TOKEN", "").strip()
        self.data_dir = BASE_DIR / "data"
        self.cache_dir = self.data_dir / "tts_cache"
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

    @property
    def mock(self) -> bool:
        return self.force_mock or not self.openai_api_key

    @property
    def azure(self) -> bool:
        return bool(self.azure_key and self.azure_region)


settings = Settings()
