"""Конфигурационный слой приложения."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseModel):
    """Настройки логирования."""

    level: str = "INFO"
    use_json: bool = False


class QueueSettings(BaseModel):
    """Настройки очереди задач."""

    backend: str = "inmemory"
    default_queue: str = "default"
    concurrency: int = 1
    enabled: bool = True


class SchedulerSettings(BaseModel):
    """Настройки планировщика фоновых заданий."""

    enabled: bool = False
    timezone: str = "UTC"
    interval_seconds: int = 300


class APIClientSettings(BaseModel):
    """Настройки для внешних API."""

    base_url: Optional[str] = None
    timeout: int = 15
    retries: int = 3
    api_key: Optional[str] = None


class StorageSettings(BaseModel):
    """Настройки хранилища и миграций."""

    database_url: str = "sqlite:///universal_parser.db"
    alembic_config: str = "alembic.ini"


class Settings(BaseSettings):
    """Глобальные настройки приложения."""

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    telegram_bot_token: str = ""
    telegram_chat_id: int = 0
    admin_chat_ids: List[int] = Field(default_factory=list)

    default_timeout: int = 15
    max_concurrent_requests: int = 10
    use_proxy: bool = False
    proxy_url: Optional[str] = None

    export_format: str = "json"
    max_results_per_message: int = 50

    profiles_path: str = "profiles/parsing_profiles.json"

    logging: LoggingSettings = LoggingSettings()
    queue: QueueSettings = QueueSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    external_api: APIClientSettings = APIClientSettings()
    storage: StorageSettings = StorageSettings()

    def resolve_path(self, path: str) -> Path:
        """Возвращает абсолютный путь относительно корня проекта."""
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return Path(__file__).resolve().parent.parent.joinpath(candidate)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает singleton настроек."""
    return Settings()


settings = get_settings()

__all__ = [
    "APIClientSettings",
    "LoggingSettings",
    "QueueSettings",
    "SchedulerSettings",
    "Settings",
    "StorageSettings",
    "get_settings",
    "settings",
]
