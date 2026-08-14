from functools import lru_cache

from supabase import Client, create_client

from recon_ai_core.settings import get_settings


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not settings.supabase_secret_key:
        raise RuntimeError("SUPABASE_SECRET_KEY is not configured")
    return create_client(settings.supabase_url, settings.supabase_secret_key)
