from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "FitBuddy – AI Fitness Plan Generator"
    environment: str = "development"
    debug: bool = True

    database_url: str = f"sqlite:///{(BASE_DIR / 'data' / 'fitbuddy.db').as_posix()}"

    gemini_api_key: str | None = None
    workout_model: str = "gemini-3.8-flash"
    nutrition_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = Field(default=45.0, gt=0)
    mock_ai: bool = False

    admin_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
