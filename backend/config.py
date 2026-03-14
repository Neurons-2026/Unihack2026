from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    anthropic_api_key: str = ""

    # Optional / extra settings used by scripts
    openai_api_key: str = ""
    scrape_sources: str = ""
    briefing_max_cards: int = 5

    cors_origins: Optional[str] = None
    app_env: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # allow extra vars without raising errors


@lru_cache()
def get_settings() -> Settings:
    return Settings()
