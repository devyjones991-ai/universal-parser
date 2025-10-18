from typing import Optional, List
import json
import os

class Settings:
    def __init__(self):
        # Загружаем из переменных окружения
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
        self.ADMIN_CHAT_IDS = json.loads(os.getenv("ADMIN_CHAT_IDS", "[]"))
        
        # Настройки парсинга
        self.DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "15"))
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
        self.PROXY_URL = os.getenv("PROXY_URL", None)
        
        # Настройки базы
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///universal_parser.db")
        
        # Настройки экспорта
        self.EXPORT_FORMAT = os.getenv("EXPORT_FORMAT", "json")
        self.MAX_RESULTS_PER_MESSAGE = int(os.getenv("MAX_RESULTS_PER_MESSAGE", "50"))

def load_parsing_profiles():
    """Загружает профили парсинга из JSON"""
    try:
        with open("profiles/parsing_profiles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

settings = Settings()
parsing_profiles = load_parsing_profiles()
