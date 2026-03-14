import os
from typing import Any

from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY")
    return create_client(url, key)


def placeholder_table(name: str) -> list[dict[str, Any]]:
    # During early hackathon setup, we work from in-memory seed data.
    return []
