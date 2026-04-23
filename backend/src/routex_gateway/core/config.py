from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ROUTEX_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "RouteX Gateway"
    app_env: str = "development"
    host: str = "127.0.0.1"
    port: int = 48200
    admin_port: int | None = None
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./backend/routex.db"
    logs_dir: Path = Field(default_factory=lambda: Path("./var/logs"))
    config_dir: Path = Field(default_factory=lambda: Path("./configs"))
    project_configs_dir: Path = Field(default_factory=lambda: Path("./.routex"))
    allow_anonymous_local_requests: bool = True
    local_api_key_salt: str = "routex-local-dev-salt"
    request_log_retention_days: int = 14
    debug_logging_ttl_minutes: int = 30


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
