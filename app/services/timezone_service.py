"""Сервис для работы с часовыми поясами"""

import pytz
from dataclasses import dataclass

from app.core.i18n import i18n_manager

@dataclass
class TimezoneInfo:
    """Информация о часовом поясе"""
    name: str
    display_name: str
    utc_offset: str
    country: str
    city: str
    is_dst: bool = False

class TimezoneService:
    """Сервис для работы с часовыми поясами"""

    def __init__(self):
        self.default_timezone = "UTC"
        self.popular_timezones = [
            "UTC",
            "America/New_York",      # EST/EDT
            "America/Los_Angeles",   # PST/PDT
            "America/Chicago",       # CST/CDT
            "America/Denver",        # MST/MDT
            "Europe/London",         # GMT/BST
            "Europe/Paris",          # CET/CEST
            "Europe/Berlin",         # CET/CEST
            "Europe/Moscow",         # MSK
            "Asia/Tokyo",            # JST
            "Asia/Seoul",            # KST
            "Asia/Shanghai",         # CST
            "Asia/Dubai",            # GST
            "Asia/Jerusalem",        # IST
            "Australia/Sydney",      # AEST/AEDT
            "Australia/Melbourne",   # AEST/AEDT
            "Pacific/Auckland",      # NZST/NZDT
            "America/Sao_Paulo",     # BRT
            "America/Mexico_City",   # CST/CDT
            "America/Toronto",       # EST/EDT
            "Europe/Rome",           # CET/CEST
            "Europe/Madrid",         # CET/CEST
            "Europe/Amsterdam",      # CET/CEST
            "Europe/Stockholm",      # CET/CEST
            "Europe/Vienna",         # CET/CEST
            "Asia/Kolkata",          # IST
            "Asia/Bangkok",          # ICT
            "Asia/Jakarta",          # WIB
            "Asia/Manila",           # PHT
            "Asia/Ho_Chi_Minh",      # ICT
            "Asia/Kuala_Lumpur",     # MYT
            "Asia/Singapore",        # SGT
            "Asia/Hong_Kong",        # HKT
            "Asia/Taipei",           # CST
            "Asia/Mumbai",           # IST
            "Africa/Cairo",          # EET
            "Africa/Johannesburg",   # SAST
            "America/Argentina/Buenos_Aires",  # ART
            "America/Santiago",      # CLT
            "America/Lima",          # PET
            "America/Caracas",       # VET
            "America/Bogota",        # COT
            "America/Guatemala",     # CST
            "America/Havana",        # CST
            "America/Jamaica",       # EST
            "America/Panama",        # EST
            "America/La_Paz",        # BOT
            "America/Asuncion",      # PYT
            "America/Montevideo",    # UYT
            "America/Recife",        # BRT
            "America/Bahia",         # BRT
            "America/Fortaleza",     # BRT
            "America/Manaus",        # AMT
            "America/Cuiaba",        # AMT
            "America/Campo_Grande",  # AMT
            "America/Porto_Velho",   # AMT
            "America/Rio_Branco",    # ACT
            "America/Boa_Vista",     # AMT
            "America/Maceio",        # BRT
            "America/Natal",         # BRT
            "America/Joao_Pessoa",   # BRT
            "America/Aracaju",       # BRT
            "America/Salvador",      # BRT
            "America/Vitoria",       # BRT
            "America/Belo_Horizonte", # BRT
            "America/Sao_Paulo",     # BRT
            "America/Curitiba",      # BRT
            "America/Florianopolis", # BRT
            "America/Porto_Alegre",  # BRT
            "America/Cuiaba",        # AMT
            "America/Campo_Grande",  # AMT
            "America/Manaus",        # AMT
            "America/Porto_Velho",   # AMT
            "America/Rio_Branco",    # ACT
            "America/Boa_Vista",     # AMT
            "America/Maceio",        # BRT
            "America/Natal",         # BRT
            "America/Joao_Pessoa",   # BRT
            "America/Aracaju",       # BRT
            "America/Salvador",      # BRT
            "America/Vitoria",       # BRT
            "America/Belo_Horizonte", # BRT
            "America/Sao_Paulo",     # BRT
            "America/Curitiba",      # BRT
            "America/Florianopolis", # BRT
            "America/Porto_Alegre"   # BRT
        ]

        # Маппинг стран к часовым поясам
        self.country_timezone_map = {
            "US": "America/New_York",
            "RU": "Europe/Moscow",
            "GB": "Europe/London",
            "DE": "Europe/Berlin",
            "FR": "Europe/Paris",
            "IT": "Europe/Rome",
            "ES": "Europe/Madrid",
            "JP": "Asia/Tokyo",
            "CN": "Asia/Shanghai",
            "KR": "Asia/Seoul",
            "AE": "Asia/Dubai",
            "IL": "Asia/Jerusalem",
            "AU": "Australia/Sydney",
            "NZ": "Pacific/Auckland",
            "BR": "America/Sao_Paulo",
            "MX": "America/Mexico_City",
            "CA": "America/Toronto",
            "IN": "Asia/Kolkata",
            "TH": "Asia/Bangkok",
            "ID": "Asia/Jakarta",
            "PH": "Asia/Manila",
            "VN": "Asia/Ho_Chi_Minh",
            "MY": "Asia/Kuala_Lumpur",
            "SG": "Asia/Singapore",
            "HK": "Asia/Hong_Kong",
            "TW": "Asia/Taipei",
            "EG": "Africa/Cairo",
            "ZA": "Africa/Johannesburg",
            "AR": "America/Argentina/Buenos_Aires",
            "CL": "America/Santiago",
            "PE": "America/Lima",
            "VE": "America/Caracas",
            "CO": "America/Bogota",
            "GT": "America/Guatemala",
            "CU": "America/Havana",
            "JM": "America/Jamaica",
            "PA": "America/Panama",
            "BO": "America/La_Paz",
            "PY": "America/Asuncion",
            "UY": "America/Montevideo"
        }

        # Маппинг локалей к часовым поясам
        self.locale_timezone_map = {
            "en": "America/New_York",
            "ru": "Europe/Moscow",
            "es": "Europe/Madrid",
            "fr": "Europe/Paris",
            "de": "Europe/Berlin",
            "it": "Europe/Rome",
            "pt": "America/Sao_Paulo",
            "ja": "Asia/Tokyo",
            "ko": "Asia/Seoul",
            "zh": "Asia/Shanghai",
            "ar": "Asia/Dubai",
            "he": "Asia/Jerusalem",
            "hi": "Asia/Kolkata",
            "th": "Asia/Bangkok",
            "id": "Asia/Jakarta",
            "fil": "Asia/Manila",
            "vi": "Asia/Ho_Chi_Minh",
            "ms": "Asia/Kuala_Lumpur",
            "sv": "Europe/Stockholm",
            "no": "Europe/Oslo",
            "da": "Europe/Copenhagen",
            "pl": "Europe/Warsaw",
            "cs": "Europe/Prague",
            "hu": "Europe/Budapest",
            "tr": "Europe/Istanbul",
            "af": "Africa/Johannesburg",
            "nl": "Europe/Amsterdam",
            "fi": "Europe/Helsinki",
            "el": "Europe/Athens",
            "pt-BR": "America/Sao_Paulo",
            "en-CA": "America/Toronto",
            "en-AU": "Australia/Sydney",
            "en-GB": "Europe/London",
            "en-IN": "Asia/Kolkata",
            "en-SG": "Asia/Singapore",
            "en-HK": "Asia/Hong_Kong",
            "en-NZ": "Pacific/Auckland",
            "es-MX": "America/Mexico_City",
            "es-AR": "America/Argentina/Buenos_Aires",
            "es-CL": "America/Santiago",
            "es-CO": "America/Bogota",
            "es-PE": "America/Lima",
            "es-VE": "America/Caracas",
            "fr-CA": "America/Toronto",
            "fr-FR": "Europe/Paris",
            "de-CH": "Europe/Zurich",
            "de-AT": "Europe/Vienna",
            "de-DE": "Europe/Berlin",
            "it-IT": "Europe/Rome",
            "it-CH": "Europe/Zurich",
            "pt-PT": "Europe/Lisbon",
            "pt-BR": "America/Sao_Paulo",
            "ja-JP": "Asia/Tokyo",
            "ko-KR": "Asia/Seoul",
            "zh-CN": "Asia/Shanghai",
            "zh-TW": "Asia/Taipei",
            "zh-HK": "Asia/Hong_Kong",
            "ar-AE": "Asia/Dubai",
            "ar-SA": "Asia/Riyadh",
            "ar-EG": "Africa/Cairo",
            "he-IL": "Asia/Jerusalem"
        }

    def get_timezone_info(self, timezone_name: str) -> Optional[TimezoneInfo]:
        """Получить информацию о часовом поясе"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)

            # Получаем смещение UTC
            utc_offset = now.strftime("%z")
            if utc_offset:
                utc_offset = f"UTC{utc_offset[:3]}:{utc_offset[3:]}"
            else:
                utc_offset = "UTC+00:00"

            # Получаем название города
            city = timezone_name.split("/")[-1].replace("_", " ")

            # Определяем страну по часовому поясу
            country = self._get_country_by_timezone(timezone_name)

            return TimezoneInfo(
                name=timezone_name,
                display_name=self._get_display_name(timezone_name),
                utc_offset=utc_offset,
                country=country,
                city=city,
                is_dst=now.dst() != timedelta(0)
            )
        except Exception:
            return None

    def _get_country_by_timezone(self, timezone_name: str) -> str:
        """Получить страну по часовому поясу"""
        timezone_country_map = {
            "America/New_York": "United States",
            "America/Los_Angeles": "United States",
            "America/Chicago": "United States",
            "America/Denver": "United States",
            "Europe/London": "United Kingdom",
            "Europe/Paris": "France",
            "Europe/Berlin": "Germany",
            "Europe/Moscow": "Russia",
            "Asia/Tokyo": "Japan",
            "Asia/Seoul": "South Korea",
            "Asia/Shanghai": "China",
            "Asia/Dubai": "United Arab Emirates",
            "Asia/Jerusalem": "Israel",
            "Australia/Sydney": "Australia",
            "Australia/Melbourne": "Australia",
            "Pacific/Auckland": "New Zealand",
            "America/Sao_Paulo": "Brazil",
            "America/Mexico_City": "Mexico",
            "America/Toronto": "Canada",
            "Europe/Rome": "Italy",
            "Europe/Madrid": "Spain",
            "Europe/Amsterdam": "Netherlands",
            "Europe/Stockholm": "Sweden",
            "Europe/Vienna": "Austria",
            "Asia/Kolkata": "India",
            "Asia/Bangkok": "Thailand",
            "Asia/Jakarta": "Indonesia",
            "Asia/Manila": "Philippines",
            "Asia/Ho_Chi_Minh": "Vietnam",
            "Asia/Kuala_Lumpur": "Malaysia",
            "Asia/Singapore": "Singapore",
            "Asia/Hong_Kong": "Hong Kong",
            "Asia/Taipei": "Taiwan",
            "Africa/Cairo": "Egypt",
            "Africa/Johannesburg": "South Africa"
        }

        return timezone_country_map.get(timezone_name, "Unknown")

    def _get_display_name(self, timezone_name: str) -> str:
        """Получить отображаемое название часового пояса"""
        display_names = {
            "UTC": "Coordinated Universal Time",
            "America/New_York": "Eastern Time (US & Canada)",
            "America/Los_Angeles": "Pacific Time (US & Canada)",
            "America/Chicago": "Central Time (US & Canada)",
            "America/Denver": "Mountain Time (US & Canada)",
            "Europe/London": "Greenwich Mean Time",
            "Europe/Paris": "Central European Time",
            "Europe/Berlin": "Central European Time",
            "Europe/Moscow": "Moscow Standard Time",
            "Asia/Tokyo": "Japan Standard Time",
            "Asia/Seoul": "Korea Standard Time",
            "Asia/Shanghai": "China Standard Time",
            "Asia/Dubai": "Gulf Standard Time",
            "Asia/Jerusalem": "Israel Standard Time",
            "Australia/Sydney": "Australian Eastern Time",
            "Australia/Melbourne": "Australian Eastern Time",
            "Pacific/Auckland": "New Zealand Standard Time",
            "America/Sao_Paulo": "Brasilia Time",
            "America/Mexico_City": "Central Time (Mexico)",
            "America/Toronto": "Eastern Time (Canada)",
            "Europe/Rome": "Central European Time",
            "Europe/Madrid": "Central European Time",
            "Europe/Amsterdam": "Central European Time",
            "Europe/Stockholm": "Central European Time",
            "Europe/Vienna": "Central European Time",
            "Asia/Kolkata": "India Standard Time",
            "Asia/Bangkok": "Indochina Time",
            "Asia/Jakarta": "Western Indonesia Time",
            "Asia/Manila": "Philippine Time",
            "Asia/Ho_Chi_Minh": "Indochina Time",
            "Asia/Kuala_Lumpur": "Malaysia Time",
            "Asia/Singapore": "Singapore Time",
            "Asia/Hong_Kong": "Hong Kong Time",
            "Asia/Taipei": "Taiwan Time",
            "Africa/Cairo": "Eastern European Time",
            "Africa/Johannesburg": "South Africa Standard Time"
        }

        return display_names.get(timezone_name, timezone_name)

    def get_popular_timezones(self) -> List[TimezoneInfo]:
        """Получить список популярных часовых поясов"""
        timezones = []
        for tz_name in self.popular_timezones:
            tz_info = self.get_timezone_info(tz_name)
            if tz_info:
                timezones.append(tz_info)
        return timezones

    def get_timezone_by_country(self, country_code: str) -> Optional[str]:
        """Получить часовой пояс по коду страны"""
        return self.country_timezone_map.get(country_code.upper())

    def get_timezone_by_locale(self, locale: str) -> Optional[str]:
        """Получить часовой пояс по локали"""
        return self.locale_timezone_map.get(locale)

    def convert_datetime(self, dt: datetime, from_tz: str, to_tz: str) -> datetime  # noqa  # noqa: E501 E501
        """Конвертировать дату и время между часовыми поясами"""
        try:
            # Создаем timezone объекты
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)

            # Если дата наивная (без timezone), считаем её в исходном часовом поясе
            if dt.tzinfo is None:
                dt = from_timezone.localize(dt)

            # Конвертируем в целевой часовой пояс
            return dt.astimezone(to_timezone)
        except Exception as e:
            print(f"Error converting datetime from {from_tz} to {to_tz}: {e}")
            return dt

    def get_current_time(self, timezone_name: str) -> datetime:
        """Получить текущее время в указанном часовом поясе"""
        try:
            tz = pytz.timezone(timezone_name)
            return datetime.now(tz)
        except Exception:
            return datetime.now()

    def get_utc_offset(self, timezone_name: str) -> str:
        """Получить смещение UTC для часового пояса"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            utc_offset = now.strftime("%z")
            if utc_offset:
                return f"UTC{utc_offset[:3]}:{utc_offset[3:]}"
            return "UTC+00:00"
        except Exception:
            return "UTC+00:00"

    def is_dst_active(self, timezone_name: str) -> bool:
        """Проверить, действует ли летнее время"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            return now.dst() != timedelta(0)
        except Exception:
            return False

    def get_timezone_abbreviation(self, timezone_name: str) -> str:
        """Получить аббревиатуру часового пояса"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)
            return now.strftime("%Z")
        except Exception:
            return "UTC"

    def get_timezone_emoji(self, timezone_name: str) -> str:
        """Получить эмодзи для часового пояса"""
        timezone_emojis = {
            "UTC": "🌍",
            "America/New_York": "🇺🇸",
            "America/Los_Angeles": "🇺🇸",
            "America/Chicago": "🇺🇸",
            "America/Denver": "🇺🇸",
            "Europe/London": "🇬🇧",
            "Europe/Paris": "🇫🇷",
            "Europe/Berlin": "🇩🇪",
            "Europe/Moscow": "🇷🇺",
            "Asia/Tokyo": "🇯🇵",
            "Asia/Seoul": "🇰🇷",
            "Asia/Shanghai": "🇨🇳",
            "Asia/Dubai": "🇦🇪",
            "Asia/Jerusalem": "🇮🇱",
            "Australia/Sydney": "🇦🇺",
            "Australia/Melbourne": "🇦🇺",
            "Pacific/Auckland": "🇳🇿",
            "America/Sao_Paulo": "🇧🇷",
            "America/Mexico_City": "🇲🇽",
            "America/Toronto": "🇨🇦",
            "Europe/Rome": "🇮🇹",
            "Europe/Madrid": "🇪🇸",
            "Europe/Amsterdam": "🇳🇱",
            "Europe/Stockholm": "🇸🇪",
            "Europe/Vienna": "🇦🇹",
            "Asia/Kolkata": "🇮🇳",
            "Asia/Bangkok": "🇹🇭",
            "Asia/Jakarta": "🇮🇩",
            "Asia/Manila": "🇵🇭",
            "Asia/Ho_Chi_Minh": "🇻🇳",
            "Asia/Kuala_Lumpur": "🇲🇾",
            "Asia/Singapore": "🇸🇬",
            "Asia/Hong_Kong": "🇭🇰",
            "Asia/Taipei": "🇹🇼",
            "Africa/Cairo": "🇪🇬",
            "Africa/Johannesburg": "🇿🇦"
        }

        return timezone_emojis.get(timezone_name, "🌍")

    def get_timezone_groups(self) -> Dict[str, List[TimezoneInfo]]:
        """Получить часовые пояса, сгруппированные по регионам"""
        groups = {
            "Americas": [],
            "Europe": [],
            "Asia": [],
            "Africa": [],
            "Oceania": [],
            "UTC": []
        }

        for tz_name in self.popular_timezones:
            tz_info = self.get_timezone_info(tz_name)
            if tz_info:
                if tz_name == "UTC":
                    groups["UTC"].append(tz_info)
                elif tz_name.startswith("America/"):
                    groups["Americas"].append(tz_info)
                elif tz_name.startswith("Europe/"):
                    groups["Europe"].append(tz_info)
                elif tz_name.startswith("Asia/"):
                    groups["Asia"].append(tz_info)
                elif tz_name.startswith("Africa/"):
                    groups["Africa"].append(tz_info)
                elif tz_name.startswith("Australia/") or tz_name.startswith("Pacific/")  # noqa  # noqa: E501 E501
                    groups["Oceania"].append(tz_info)

        return groups

    def format_datetime_for_timezone(self, dt: datetime, timezone_name: str, 
                                   format_string: str = "%Y-%m-%d %H:%M:%S") -> str  # noqa  # noqa: E501 E501
        """Форматировать дату и время для часового пояса"""
        try:
            tz = pytz.timezone(timezone_name)
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            else:
                dt = dt.astimezone(tz)
            return dt.strftime(format_string)
        except Exception:
            return dt.strftime(format_string)

    def get_timezone_difference(self, tz1: str, tz2: str) -> str:
        """Получить разность между двумя часовыми поясами"""
        try:
            tz1_obj = pytz.timezone(tz1)
            tz2_obj = pytz.timezone(tz2)

            now = datetime.now()
            dt1 = tz1_obj.localize(now)
            dt2 = tz2_obj.localize(now)

            diff = dt2 - dt1
            hours = diff.total_seconds() / 3600

            if hours > 0:
                return f"+{hours:.1f} hours"
            elif hours < 0:
                return f"{hours:.1f} hours"
            else:
                return "Same time"
        except Exception:
            return "Unknown"

    def get_working_hours(self, timezone_name: str, start_hour: int = 9, end_hour: int = 17) -> Dict[str, Any]  # noqa  # noqa: E501 E501
        """Получить рабочие часы для часового пояса"""
        try:
            tz = pytz.timezone(timezone_name)
            now = datetime.now(tz)

            # Рабочие часы сегодня
            work_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            work_end = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)

            # Проверяем, рабочий ли сейчас день
            is_workday = now.weekday() < 5  # Понедельник = 0, Пятница = 4
            is_working_hours = work_start <= now <= work_end

            return {
                "timezone": timezone_name,
                "current_time": now,
                "work_start": work_start,
                "work_end": work_end,
                "is_workday": is_workday,
                "is_working_hours": is_working_hours and is_workday,
                "next_work_start": work_start + timedelta(days=1) if now > work_end else work_start,
                "time_until_work_start": work_start - now if now < work_start else timedelta(0),
                "time_until_work_end": work_end - now if now < work_end else timedelta(0)
            }
        except Exception:
            return {
                "timezone": timezone_name,
                "current_time": datetime.now(),
                "work_start": None,
                "work_end": None,
                "is_workday": False,
                "is_working_hours": False,
                "next_work_start": None,
                "time_until_work_start": timedelta(0),
                "time_until_work_end": timedelta(0)
            }

# Глобальный экземпляр сервиса часовых поясов
timezone_service = TimezoneService()
