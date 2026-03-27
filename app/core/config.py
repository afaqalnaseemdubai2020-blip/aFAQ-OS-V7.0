import sys
import json
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AFAQ-OS"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: SecretStr = Field(min_length=32)
    TIMEZONE: str = "Asia/Dubai"

    DATABASE_URL: str = Field(min_length=1)
    DATABASE_ECHO: bool = False

    SHOPIFY_STORE_DOMAIN: str = ""
    SHOPIFY_ACCESS_TOKEN: str = ""
    SHOPIFY_API_VERSION: str = "2024-01"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    FEATURE_FLAGS: str = "{}"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    GRACE_WINDOW_MINUTES: int = 15
    INACTIVITY_THRESHOLD_MINUTES: int = 15
    CHECK_IN_PING_INTERVAL_MINUTES: int = 10

    @property
    def feature_flags_dict(self) -> Dict[str, bool]:
        return json.loads(self.FEATURE_FLAGS)


settings = Settings()


# Critical validations
if len(settings.SECRET_KEY.get_secret_value()) < 32:
    print("CRITICAL: SECRET_KEY must be at least 32 characters long.")
    sys.exit(1)

if not settings.DATABASE_URL:
    print("CRITICAL: DATABASE_URL cannot be empty.")
    sys.exit(1)
