from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RSA-SHIELD"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./rsa_shield.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = 64 * 1024
    default_ecm_timeout_ms: int = 8000
    default_ecm_curves: int = 40
    default_ecm_b1: int = 50_000
    rate_limit_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
