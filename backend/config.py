from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

# Resolve .env relative to this file, not the process CWD
_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    anthropic_api_key: str = ""
    pexels_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # Optional / extra settings used by scripts
    scrape_sources: str = ""
    briefing_max_cards: int = 5

    supabase_jwt_secret: str = ""

    cors_origins: Optional[str] = None
    app_env: str = "development"

    class Config:
        env_file = str(_ENV_FILE)
        case_sensitive = False
        extra = "ignore"  # allow extra vars without raising errors


@lru_cache()
def get_settings() -> Settings:
    return Settings()
