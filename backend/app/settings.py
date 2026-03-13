from functools import lru_cache
from typing import List

from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: List[AnyHttpUrl] = []

    database_url: str = "postgresql+psycopg2://appuser:apppassword@db:5432/appdb"
    redis_url: str = "redis://redis:6379/0"
    openai_api_key: str = ""

    briefing_max_cards: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
