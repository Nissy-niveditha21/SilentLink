import secrets
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "GENERATE-ME"
    DATABASE_URL: str = "sqlite:///data/silentlink.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    SESSION_COOKIE_NAME: str = "silentlink_session"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

_EPHEMERAL_SENTINEL = object()

if settings.SECRET_KEY == "GENERATE-ME" or not settings.SECRET_KEY:
    warning_msg = (
        "\033[93m[WARN]\033[0m SECRET_KEY not provided in .env; "
        "using per-boot ephemeral key. Sessions will break on restart."
    )
    print(warning_msg, file=sys.stderr)
    settings.SECRET_KEY = secrets.token_urlsafe(32)
    settings._secret_key_runtime = _EPHEMERAL_SENTINEL
