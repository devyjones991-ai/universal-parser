from pydantic_settings import BaseSettings
from typing import Optional, List
import json
import os

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: int = 0
    ADMIN_CHAT_IDS: List[int] = []
    
    # Настройки парсинга
    DEFAULT_TIMEOUT: int = 15
    MAX_CONCURRENT_REQUESTS: int = 10
    USE_PROXY: bool = False
    PROXY_URL: Optional[str] = None
    
    # Настройки базы
    DATABASE_URL: str = "sqlite:///universal_parser.db"
    
    # Настройки экспорта
    EXPORT_FORMAT: str = "json"  # json, csv, xlsx
    MAX_RESULTS_PER_MESSAGE: int = 50
    
    class Config:
        env_file = ".env"

def load_parsing_profiles():
    """Загружает профили парсинга из JSON"""
    try:
        with open("profiles/parsing_profiles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

settings = Settings()
parsing_profiles = load_parsing_profiles()
