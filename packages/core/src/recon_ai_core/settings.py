from functools import lru_cache

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = find_dotenv(".env", usecwd=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE or ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = ""
    supabase_url: str = ""
    supabase_secret_key: str = ""
    supabase_storage_bucket: str = "reconciliation-documents"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1"
    openai_extraction_model: str = "gpt-4.1"
    redis_url: str = "redis://localhost:6379/0"
    api_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
