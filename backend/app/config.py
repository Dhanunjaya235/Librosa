import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Interview Assessment PoC"
    debug: bool = False
    upload_dir: str = str(Path(tempfile.gettempdir()) / "interview_uploads")
    max_file_size_mb: int = 500
    allowed_extensions: set[str] = {".mp3", ".wav", ".mp4", ".mov"}
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    target_sample_rate: int = 16000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
