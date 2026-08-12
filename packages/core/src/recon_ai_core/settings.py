from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "reconciliation-documents"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4.1"
    openai_extraction_model: str = "gpt-4.1"
    redis_url: str = "redis://localhost:6379/0"


def get_settings() -> Settings:
    return Settings()
