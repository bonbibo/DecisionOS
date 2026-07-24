from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://decisionos:decisionos@localhost:5432/decisionos"

    app_env: str = "development"
    log_level: str = "INFO"

    whatsapp_verify_token: str = "change-me"
    whatsapp_access_token: str = "change-me"
    whatsapp_phone_number_id: str = "change-me"
    whatsapp_app_secret: str = "change-me"

    gmail_client_id: str = "change-me"
    gmail_client_secret: str = "change-me"
    gmail_refresh_token: str = "change-me"
    gmail_sender_address: str = "negotiator@example.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
