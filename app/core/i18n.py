"""Система интернационализации и локализации"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz
from babel import Locale, UnknownLocaleError
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_currency, format_number, format_decimal
import locale

class I18nManager:
    """Менеджер интернационализации"""
    
    def __init__(self, default_locale: str = "en", translations_dir: str = "app/translations"):
        self.default_locale = default_locale
        self.translations_dir = translations_dir
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.supported_locales = [
            "en", "ru", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ar", "he"
        ]
        self.rtl_languages = ["ar", "he", "fa", "ur"]
        self.load_translations()
    
    def load_translations(self):
        """Загрузить переводы из файлов"""
        for locale_code in self.supported_locales:
            try:
                file_path = os.path.join(self.translations_dir, f"{locale_code}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[locale_code] = json.load(f)
                else:
                    # Создаем базовый файл переводов
                    self.translations[locale_code] = self._create_base_translations(locale_code)
                    self._save_translations(locale_code)
            except Exception as e:
                print(f"Error loading translations for {locale_code}: {e}")
                self.translations[locale_code] = self._create_base_translations(locale_code)
    
    def _create_base_translations(self, locale_code: str) -> Dict[str, Any]:
        """Создать базовые переводы для языка"""
        base_translations = {
            "en": {
                "app": {
                    "name": "Universal Parser",
                    "description": "Comprehensive marketplace monitoring platform"
                },
                "common": {
                    "loading": "Loading...",
                    "error": "Error",
                    "success": "Success",
                    "cancel": "Cancel",
                    "save": "Save",
                    "delete": "Delete",
                    "edit": "Edit",
                    "add": "Add",
                    "search": "Search",
                    "filter": "Filter",
                    "export": "Export",
                    "import": "Import",
                    "refresh": "Refresh",
                    "back": "Back",
                    "next": "Next",
                    "previous": "Previous",
                    "close": "Close",
                    "open": "Open",
                    "yes": "Yes",
                    "no": "No"
                },
                "navigation": {
                    "overview": "Overview",
                    "items": "Items Management",
                    "analytics": "Analytics",
                    "advanced_analytics": "Advanced Analytics",
                    "report_scheduler": "Report Scheduler",
                    "ai_insights": "AI Insights",
                    "niche_analysis": "Niche Analysis",
                    "russian_marketplaces": "Russian Marketplaces",
                    "social_features": "Social Features",
                    "monetization": "Monetization",
                    "settings": "Settings",
                    "parsing_tools": "Parsing Tools"
                },
                "dashboard": {
                    "welcome": "Welcome to Universal Parser",
                    "total_items": "Total Items",
                    "total_users": "Total Users",
                    "total_revenue": "Total Revenue",
                    "active_users": "Active Users"
                },
                "marketplaces": {
                    "wildberries": "Wildberries",
                    "ozon": "Ozon",
                    "yandex_market": "Yandex Market",
                    "avito": "Avito",
                    "mvideo": "M.Video",
                    "eldorado": "Eldorado",
                    "aliexpress": "AliExpress",
                    "amazon": "Amazon",
                    "ebay": "eBay",
                    "lamoda": "Lamoda"
                },
                "currencies": {
                    "usd": "US Dollar",
                    "eur": "Euro",
                    "rub": "Russian Ruble",
                    "gbp": "British Pound",
                    "jpy": "Japanese Yen",
                    "cny": "Chinese Yuan",
                    "krw": "South Korean Won",
                    "aed": "UAE Dirham",
                    "ils": "Israeli Shekel"
                },
                "timezones": {
                    "utc": "UTC",
                    "est": "Eastern Time",
                    "pst": "Pacific Time",
                    "cet": "Central European Time",
                    "msk": "Moscow Time",
                    "jst": "Japan Standard Time",
                    "kst": "Korea Standard Time",
                    "cst": "China Standard Time",
                    "gst": "Gulf Standard Time",
                    "ist": "Israel Standard Time"
                }
            }
        }
        
        # Создаем переводы для других языков
        if locale_code == "ru":
            return {
                "app": {
                    "name": "Универсальный Парсер",
                    "description": "Комплексная платформа мониторинга маркетплейсов"
                },
                "common": {
                    "loading": "Загрузка...",
                    "error": "Ошибка",
                    "success": "Успешно",
                    "cancel": "Отмена",
                    "save": "Сохранить",
                    "delete": "Удалить",
                    "edit": "Редактировать",
                    "add": "Добавить",
                    "search": "Поиск",
                    "filter": "Фильтр",
                    "export": "Экспорт",
                    "import": "Импорт",
                    "refresh": "Обновить",
                    "back": "Назад",
                    "next": "Далее",
                    "previous": "Предыдущий",
                    "close": "Закрыть",
                    "open": "Открыть",
                    "yes": "Да",
                    "no": "Нет"
                },
                "navigation": {
                    "overview": "Обзор",
                    "items": "Управление товарами",
                    "analytics": "Аналитика",
                    "advanced_analytics": "Расширенная аналитика",
                    "report_scheduler": "Планировщик отчетов",
                    "ai_insights": "AI инсайты",
                    "niche_analysis": "Анализ ниш",
                    "russian_marketplaces": "Российские маркетплейсы",
                    "social_features": "Социальные функции",
                    "monetization": "Монетизация",
                    "settings": "Настройки",
                    "parsing_tools": "Инструменты парсинга"
                },
                "dashboard": {
                    "welcome": "Добро пожаловать в Универсальный Парсер",
                    "total_items": "Всего товаров",
                    "total_users": "Всего пользователей",
                    "total_revenue": "Общий доход",
                    "active_users": "Активные пользователи"
                },
                "marketplaces": {
                    "wildberries": "Вайлдберриз",
                    "ozon": "Озон",
                    "yandex_market": "Яндекс.Маркет",
                    "avito": "Авито",
                    "mvideo": "М.Видео",
                    "eldorado": "Эльдорадо",
                    "aliexpress": "Алиэкспресс",
                    "amazon": "Амазон",
                    "ebay": "Ибей",
                    "lamoda": "Ламода"
                },
                "currencies": {
                    "usd": "Доллар США",
                    "eur": "Евро",
                    "rub": "Российский рубль",
                    "gbp": "Британский фунт",
                    "jpy": "Японская иена",
                    "cny": "Китайский юань",
                    "krw": "Южнокорейская вона",
                    "aed": "Дирхам ОАЭ",
                    "ils": "Израильский шекель"
                },
                "timezones": {
                    "utc": "UTC",
                    "est": "Восточное время",
                    "pst": "Тихоокеанское время",
                    "cet": "Центральноевропейское время",
                    "msk": "Московское время",
                    "jst": "Японское стандартное время",
                    "kst": "Корейское стандартное время",
                    "cst": "Китайское стандартное время",
                    "gst": "Время Персидского залива",
                    "ist": "Израильское стандартное время"
                }
            }
        }
        
        # Для других языков возвращаем английские переводы как базовые
        return base_translations.get("en", {})
    
    def _save_translations(self, locale_code: str):
        """Сохранить переводы в файл"""
        try:
            os.makedirs(self.translations_dir, exist_ok=True)
            file_path = os.path.join(self.translations_dir, f"{locale_code}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translations[locale_code], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving translations for {locale_code}: {e}")
    
    def get_text(self, key: str, locale: str = None, **kwargs) -> str:
        """Получить переведенный текст"""
        if locale is None:
            locale = self.default_locale
        
        if locale not in self.translations:
            locale = self.default_locale
        
        # Разбиваем ключ на части (например, "common.save")
        keys = key.split('.')
        value = self.translations[locale]
        
        try:
            for k in keys:
                value = value[k]
            
            # Если это строка, форматируем с параметрами
            if isinstance(value, str):
                return value.format(**kwargs) if kwargs else value
            return str(value)
        except (KeyError, TypeError):
            # Если перевод не найден, возвращаем ключ
            return key
    
    def get_locale_info(self, locale_code: str) -> Dict[str, Any]:
        """Получить информацию о локали"""
        try:
            locale_obj = Locale(locale_code)
            return {
                "code": locale_code,
                "name": locale_obj.display_name,
                "language": locale_obj.language,
                "territory": locale_obj.territory,
                "is_rtl": locale_code in self.rtl_languages,
                "currency": self._get_default_currency(locale_code),
                "timezone": self._get_default_timezone(locale_code)
            }
        except UnknownLocaleError:
            return {
                "code": locale_code,
                "name": locale_code,
                "language": locale_code,
                "territory": None,
                "is_rtl": locale_code in self.rtl_languages,
                "currency": "USD",
                "timezone": "UTC"
            }
    
    def _get_default_currency(self, locale_code: str) -> str:
        """Получить валюту по умолчанию для локали"""
        currency_map = {
            "en": "USD",
            "ru": "RUB",
            "es": "EUR",
            "fr": "EUR",
            "de": "EUR",
            "it": "EUR",
            "pt": "EUR",
            "ja": "JPY",
            "ko": "KRW",
            "zh": "CNY",
            "ar": "AED",
            "he": "ILS"
        }
        return currency_map.get(locale_code, "USD")
    
    def _get_default_timezone(self, locale_code: str) -> str:
        """Получить часовой пояс по умолчанию для локали"""
        timezone_map = {
            "en": "America/New_York",
            "ru": "Europe/Moscow",
            "es": "Europe/Madrid",
            "fr": "Europe/Paris",
            "de": "Europe/Berlin",
            "it": "Europe/Rome",
            "pt": "Europe/Lisbon",
            "ja": "Asia/Tokyo",
            "ko": "Asia/Seoul",
            "zh": "Asia/Shanghai",
            "ar": "Asia/Dubai",
            "he": "Asia/Jerusalem"
        }
        return timezone_map.get(locale_code, "UTC")
    
    def format_currency(self, amount: float, currency: str, locale: str = None) -> str:
        """Форматировать валюту"""
        if locale is None:
            locale = self.default_locale
        
        try:
            locale_obj = Locale(locale)
            return format_currency(amount, currency, locale=locale_obj)
        except Exception:
            return f"{amount} {currency}"
    
    def format_number(self, number: float, locale: str = None) -> str:
        """Форматировать число"""
        if locale is None:
            locale = self.default_locale
        
        try:
            locale_obj = Locale(locale)
            return format_number(number, locale=locale_obj)
        except Exception:
            return str(number)
    
    def format_datetime(self, dt: datetime, locale: str = None, timezone: str = None) -> str:
        """Форматировать дату и время"""
        if locale is None:
            locale = self.default_locale
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                dt = dt.astimezone(tz)
            except Exception:
                pass
        
        try:
            locale_obj = Locale(locale)
            return format_datetime(dt, locale=locale_obj)
        except Exception:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def format_date(self, dt: datetime, locale: str = None, timezone: str = None) -> str:
        """Форматировать дату"""
        if locale is None:
            locale = self.default_locale
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                dt = dt.astimezone(tz)
            except Exception:
                pass
        
        try:
            locale_obj = Locale(locale)
            return format_date(dt, locale=locale_obj)
        except Exception:
            return dt.strftime("%Y-%m-%d")
    
    def format_time(self, dt: datetime, locale: str = None, timezone: str = None) -> str:
        """Форматировать время"""
        if locale is None:
            locale = self.default_locale
        
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                dt = dt.astimezone(tz)
            except Exception:
                pass
        
        try:
            locale_obj = Locale(locale)
            return format_time(dt, locale=locale_obj)
        except Exception:
            return dt.strftime("%H:%M:%S")
    
    def get_supported_locales(self) -> List[Dict[str, Any]]:
        """Получить список поддерживаемых локалей"""
        return [self.get_locale_info(locale) for locale in self.supported_locales]
    
    def detect_language(self, text: str) -> str:
        """Определить язык текста (упрощенная версия)"""
        # Простая эвристика для определения языка
        cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff')
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "en"
        
        if cyrillic_chars / total_chars > 0.3:
            return "ru"
        elif arabic_chars / total_chars > 0.3:
            return "ar"
        elif chinese_chars / total_chars > 0.3:
            return "zh"
        elif japanese_chars / total_chars > 0.3:
            return "ja"
        elif korean_chars / total_chars > 0.3:
            return "ko"
        else:
            return "en"
    
    def is_rtl(self, locale: str) -> bool:
        """Проверить, является ли язык RTL"""
        return locale in self.rtl_languages
    
    def add_translation(self, key: str, value: str, locale: str):
        """Добавить перевод"""
        if locale not in self.translations:
            self.translations[locale] = {}
        
        keys = key.split('.')
        current = self.translations[locale]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self._save_translations(locale)
    
    def get_available_translations(self) -> Dict[str, Dict[str, Any]]:
        """Получить все доступные переводы"""
        return self.translations


# Глобальный экземпляр менеджера i18n
i18n_manager = I18nManager()


def get_text(key: str, locale: str = None, **kwargs) -> str:
    """Получить переведенный текст (удобная функция)"""
    return i18n_manager.get_text(key, locale, **kwargs)


def format_currency(amount: float, currency: str, locale: str = None) -> str:
    """Форматировать валюту (удобная функция)"""
    return i18n_manager.format_currency(amount, currency, locale)


def format_datetime(dt: datetime, locale: str = None, timezone: str = None) -> str:
    """Форматировать дату и время (удобная функция)"""
    return i18n_manager.format_datetime(dt, locale, timezone)


def is_rtl(locale: str) -> bool:
    """Проверить RTL (удобная функция)"""
    return i18n_manager.is_rtl(locale)
