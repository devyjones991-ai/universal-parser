"""
Конфигурация приложения с использованием Pydantic Settings
"""
from typing import List, Optional
from pydantic import BaseSettings, validator
import json
import os


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    app_name: str = "Universal Parser"
    app_version: str = "0.2.0"
    debug: bool = False
    
    # API настройки
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # База данных
    database_url: str = "sqlite:///./universal_parser.db"
    redis_url: str = "redis://localhost:6379"
    
    # Telegram Bot
    telegram_bot_token: str = ""
    telegram_chat_id: int = 0
    admin_chat_ids: List[int] = []
    
    # Парсинг
    default_timeout: int = 15
    max_concurrent_requests: int = 10
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    
    # Экспорт
    export_format: str = "json"
    max_results_per_message: int = 50
    
    # Мониторинг
    update_interval_minutes: int = 30
    alert_check_interval_minutes: int = 15
    
    # Подписки
    free_items_limit: int = 3
    free_alerts_limit: int = 5
    premium_price: int = 990
    enterprise_price: int = 2990
    
    # Внешние API
    openai_api_key: Optional[str] = None
    yandex_api_key: Optional[str] = None
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    @validator('admin_chat_ids', pre=True)
    def parse_admin_chat_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()


def load_parsing_profiles():
    """Загружает профили парсинга из JSON"""
    try:
        with open("profiles/parsing_profiles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Глобальные профили парсинга
parsing_profiles = load_parsing_profiles()
