"""Упрощенная система интернационализации без внешних зависимостей"""

from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

class I18nService:
    """Сервис интернационализации"""
    
    def __init__(self):
        self.current_locale = "en"
        self.translations = {}
        self.translations_dir = Path("app/translations")
        self._load_translations()
    
    def _load_translations(self):
        """Загрузить переводы из файлов"""
        try:
            if self.translations_dir.exists():
                for file_path in self.translations_dir.glob("*.json"):
                    locale = file_path.stem
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[locale] = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")
    
    def set_locale(self, locale: str):
        """Установить текущую локаль"""
        self.current_locale = locale
    
    def get_locale(self) -> str:
        """Получить текущую локаль"""
        return self.current_locale
    
    def translate(self, key: str, **kwargs) -> str:
        """Перевести ключ"""
        try:
            translation = self.translations.get(self.current_locale, {})
            keys = key.split('.')
            
            for k in keys:
                if isinstance(translation, dict) and k in translation:
                    translation = translation[k]
                else:
                    return key
            
            if isinstance(translation, str):
                return translation.format(**kwargs) if kwargs else translation
            return key
        except Exception:
            return key
    
    def format_currency(self, amount: float, currency: str = "USD") -> str:
        """Форматировать валюту"""
        try:
            if currency == "USD":
                return f"${amount:.2f}"
            elif currency == "EUR":
                return f"€{amount:.2f}"
            elif currency == "RUB":
                return f"{amount:.2f} ₽"
            else:
                return f"{amount:.2f} {currency}"
        except Exception:
            return str(amount)
    
    def format_datetime(self, dt, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Форматировать дату и время"""
        try:
            return dt.strftime(format_str)
        except Exception:
            return str(dt)
    
    def get_supported_locales(self) -> list:
        """Получить список поддерживаемых локалей"""
        return list(self.translations.keys())
    
    def get_translation(self, key: str, locale: str = None) -> str:
        """Получить перевод для конкретной локали"""
        if locale is None:
            locale = self.current_locale
        
        try:
            translation = self.translations.get(locale, {})
            keys = key.split('.')
            
            for k in keys:
                if isinstance(translation, dict) and k in translation:
                    translation = translation[k]
                else:
                    return key
            
            return translation if isinstance(translation, str) else key
        except Exception:
            return key

# Глобальный экземпляр
i18n = I18nService()
