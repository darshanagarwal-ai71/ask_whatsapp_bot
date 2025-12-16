from functools import lru_cache
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    agent_id: str = Field(..., alias="AGENT_ID")
    ask_api_key: str = Field(..., alias="ASK_API_KEY")
    whatsapp_token: str = Field(..., alias="WHATSAPP_TOKEN")
    whatsapp_phone_id: str = Field(..., alias="WHATSAPP_PHONE_ID")
    verify_token: str = Field(..., alias="VERIFY_TOKEN")
    webhook_url: str = Field(..., alias="WEBHOOK_URL")
    database_url: str = Field(..., alias="DATABASE_URL")
    whatsapp_app_id: str = Field(..., alias="WHATSAPP_APP_ID")
    whatsapp_app_secret: str = Field(..., alias="WHATSAPP_APP_SECRET")
    session_timeout: int = Field(default=60, alias="SESSION_TIMEOUT")
    ask_api_base: str = Field(
        default="https://api.ask.dev.ai71services.ai",
        alias="ASK_API_BASE",
    )

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    env = {k: v for k, v in os.environ.items() if k.startswith("ASK_") or k in {
        "AGENT_ID",
        "WHATSAPP_TOKEN",
        "WHATSAPP_PHONE_ID",
        "VERIFY_TOKEN",
        "WEBHOOK_URL",
        "DATABASE_URL",
        "WHATSAPP_APP_ID",
        "WHATSAPP_APP_SECRET",
        "SESSION_TIMEOUT",
    }}
    return Settings(**env)

