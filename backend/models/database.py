from functools import lru_cache

from supabase import create_client, Client

from config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    return create_client(settings.supabase_url, settings.supabase_key)
