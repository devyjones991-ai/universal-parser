"""Сервис для работы с валютами и конвертацией"""

import httpx
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.cache import cache_service
from app.core.i18n import i18n_manager

@dataclass
class CurrencyRate:
    """Курс валюты"""
    from_currency: str
    to_currency: str
    rate: Decimal
    timestamp: datetime
    source: str

@dataclass
class CurrencyInfo:
    """Информация о валюте"""
    code: str
    name: str
    symbol: str
    decimal_places: int
    is_crypto: bool = False

class CurrencyService:
    """Сервис для работы с валютами"""

    def __init__(self):
        self.base_currency = "USD"
        self.supported_currencies = {
            "USD": CurrencyInfo("USD", "US Dollar", "$", 2),
            "EUR": CurrencyInfo("EUR", "Euro", "€", 2),
            "RUB": CurrencyInfo("RUB", "Russian Ruble", "₽", 2),
            "GBP": CurrencyInfo("GBP", "British Pound", "£", 2),
            "JPY": CurrencyInfo("JPY", "Japanese Yen", "¥", 0),
            "CNY": CurrencyInfo("CNY", "Chinese Yuan", "¥", 2),
            "KRW": CurrencyInfo("KRW", "South Korean Won", "₩", 0),
            "AED": CurrencyInfo("AED", "UAE Dirham", "د.إ", 2),
            "ILS": CurrencyInfo("ILS", "Israeli Shekel", "₪", 2),
            "INR": CurrencyInfo("INR", "Indian Rupee", "₹", 2),
            "BRL": CurrencyInfo("BRL", "Brazilian Real", "R$", 2),
            "CAD": CurrencyInfo("CAD", "Canadian Dollar", "C$", 2),
            "AUD": CurrencyInfo("AUD", "Australian Dollar", "A$", 2),
            "CHF": CurrencyInfo("CHF", "Swiss Franc", "CHF", 2),
            "SEK": CurrencyInfo("SEK", "Swedish Krona", "kr", 2),
            "NOK": CurrencyInfo("NOK", "Norwegian Krone", "kr", 2),
            "DKK": CurrencyInfo("DKK", "Danish Krone", "kr", 2),
            "PLN": CurrencyInfo("PLN", "Polish Zloty", "zł", 2),
            "CZK": CurrencyInfo("CZK", "Czech Koruna", "Kč", 2),
            "HUF": CurrencyInfo("HUF", "Hungarian Forint", "Ft", 2),
            "TRY": CurrencyInfo("TRY", "Turkish Lira", "₺", 2),
            "ZAR": CurrencyInfo("ZAR", "South African Rand", "R", 2),
            "MXN": CurrencyInfo("MXN", "Mexican Peso", "$", 2),
            "SGD": CurrencyInfo("SGD", "Singapore Dollar", "S$", 2),
            "HKD": CurrencyInfo("HKD", "Hong Kong Dollar", "HK$", 2),
            "NZD": CurrencyInfo("NZD", "New Zealand Dollar", "NZ$", 2),
            "THB": CurrencyInfo("THB", "Thai Baht", "฿", 2),
            "MYR": CurrencyInfo("MYR", "Malaysian Ringgit", "RM", 2),
            "IDR": CurrencyInfo("IDR", "Indonesian Rupiah", "Rp", 0),
            "PHP": CurrencyInfo("PHP", "Philippine Peso", "₱", 2),
            "VND": CurrencyInfo("VND", "Vietnamese Dong", "₫", 0),
            "BTC": CurrencyInfo("BTC", "Bitcoin", "₿", 8, True),
            "ETH": CurrencyInfo("ETH", "Ethereum", "Ξ", 8, True),
            "LTC": CurrencyInfo("LTC", "Litecoin", "Ł", 8, True),
            "XRP": CurrencyInfo("XRP", "Ripple", "XRP", 6, True),
            "BCH": CurrencyInfo("BCH", "Bitcoin Cash", "BCH", 8, True),
            "ADA": CurrencyInfo("ADA", "Cardano", "ADA", 6, True),
            "DOT": CurrencyInfo("DOT", "Polkadot", "DOT", 10, True),
            "LINK": CurrencyInfo("LINK", "Chainlink", "LINK", 8, True),
            "UNI": CurrencyInfo("UNI", "Uniswap", "UNI", 6, True)
        }

        # API ключи для получения курсов валют
        self.exchange_apis = {
            "exchangerate": "https://api.exchangerate-api.com/v4/latest/{base}",
            "fixer": "https://api.fixer.io/latest?access_key={key}&base={base}",
            "currencylayer": "https://api.currencylayer.com/live?access_key={key}&currencies={currencies}",
            "cryptocompare": "https://min-api.cryptocompare.com/data/price?fsym={from_currency}&tsyms={to_currency}"
        }

        # Кэш курсов валют
        self.rates_cache: Dict[str, CurrencyRate] = {}
        self.cache_duration = timedelta(hours=1)

    def get_supported_currencies(self) -> List[CurrencyInfo]:
        """Получить список поддерживаемых валют"""
        return list(self.supported_currencies.values())

    def get_currency_info(self, currency_code: str) -> Optional[CurrencyInfo]:
        """Получить информацию о валюте"""
        return self.supported_currencies.get(currency_code.upper())

    def is_currency_supported(self, currency_code: str) -> bool:
        """Проверить, поддерживается ли валюта"""
        return currency_code.upper() in self.supported_currencies

    def is_crypto_currency(self, currency_code: str) -> bool:
        """Проверить, является ли валюта криптовалютой"""
        currency_info = self.get_currency_info(currency_code)
        return currency_info.is_crypto if currency_info else False

    @cache_service.get_cache(key_prefix="currency_rates", ttl=3600)
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]  # noqa  # noqa: E501 E501
        """Получить курс обмена валют"""
        if from_currency == to_currency:
            return Decimal("1.0")

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Проверяем кэш
        cache_key = f"{from_currency}_{to_currency}"
        if cache_key in self.rates_cache:
            rate_info = self.rates_cache[cache_key]
            if datetime.now() - rate_info.timestamp < self.cache_duration:
                return rate_info.rate

        # Получаем курс из API
        rate = await self._fetch_exchange_rate(from_currency, to_currency)

        if rate:
            # Сохраняем в кэш
            self.rates_cache[cache_key] = CurrencyRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                timestamp=datetime.now(),
                source="api"
            )

        return rate

    async def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]  # noqa  # noqa: E501 E501
        """Получить курс обмена из API"""

        # Для криптовалют используем специальный API
        if self.is_crypto_currency(from_currency) or self.is_crypto_currency(to_currency)  # noqa  # noqa: E501 E501
            return await self._fetch_crypto_rate(from_currency, to_currency)

        # Для фиатных валют используем обычные API
        return await self._fetch_fiat_rate(from_currency, to_currency)

    async def _fetch_fiat_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]  # noqa  # noqa: E501 E501
        """Получить курс фиатных валют"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Используем бесплатный API exchangerate-api
                url = self.exchange_apis["exchangerate"].format(base=from_currency)
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    rates = data.get("rates", {})

                    if to_currency in rates:
                        return Decimal(str(rates[to_currency])).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

        except Exception as e:
            print(f"Error fetching fiat rate {from_currency} -> {to_currency}: {e}")

        return None

    async def _fetch_crypto_rate(self, from_currency: str, to_currency: str) -> Optional[Decimal]  # noqa  # noqa: E501 E501
        """Получить курс криптовалют"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = self.exchange_apis["cryptocompare"].format(
                    from_currency=from_currency,
                    to_currency=to_currency
                )
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    if to_currency in data:
                        return Decimal(str(data[to_currency])).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

        except Exception as e:
            print(f"Error fetching crypto rate {from_currency} -> {to_currency}  # noqa  # noqa: E501 E501 {e}")

        return None

    async def convert_currency(self, amount: Decimal, from_currency: str, to_currency: str) -> Optional[Decimal]  # noqa  # noqa: E501 E501
        """Конвертировать валюту"""
        if from_currency == to_currency:
            return amount

        rate = await self.get_exchange_rate(from_currency, to_currency)
        if rate is None:
            return None

        converted_amount = amount * rate

        # Округляем до нужного количества знаков после запятой
        currency_info = self.get_currency_info(to_currency)
        if currency_info:
            decimal_places = currency_info.decimal_places
            converted_amount = converted_amount.quantize(
                Decimal("0.1") ** decimal_places,
                rounding=ROUND_HALF_UP
            )

        return converted_amount

    def format_currency(self, amount: Decimal, currency_code: str, locale: str = "en") -> str  # noqa  # noqa: E501 E501
        """Форматировать валюту для отображения"""
        currency_info = self.get_currency_info(currency_code)
        if not currency_info:
            return f"{amount} {currency_code}"

        # Используем i18n менеджер для форматирования
        return i18n_manager.format_currency(
            float(amount),
            currency_code,
            locale
        )

    def get_currency_symbol(self, currency_code: str) -> str:
        """Получить символ валюты"""
        currency_info = self.get_currency_info(currency_code)
        return currency_info.symbol if currency_info else currency_code

    def get_currency_name(self, currency_code: str, locale: str = "en") -> str:
        """Получить название валюты"""
        currency_info = self.get_currency_info(currency_code)
        if not currency_info:
            return currency_code

        # Используем i18n для локализованного названия
        return i18n_manager.get_text(f"currencies.{currency_code.lower()}", locale) or currency_info.name

    async def get_multiple_rates(self, from_currency: str, to_currencies: List[str]) -> Dict[str, Decimal]  # noqa  # noqa: E501 E501
        """Получить курсы для нескольких валют"""
        rates = {}

        # Получаем курсы параллельно
        tasks = []
        for to_currency in to_currencies:
            task = self.get_exchange_rate(from_currency, to_currency)
            tasks.append((to_currency, task))

        for to_currency, task in tasks:
            try:
                rate = await task
                if rate:
                    rates[to_currency] = rate
            except Exception as e:
                print(f"Error getting rate for {to_currency}: {e}")

        return rates

    def get_currency_pairs(self) -> List[Dict[str, str]]:
        """Получить популярные валютные пары"""
        popular_currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "BTC", "ETH"]

        pairs = []
        for from_curr in popular_currencies:
            for to_curr in popular_currencies:
                if from_curr != to_curr:
                    pairs.append({
                        "from": from_curr,
                        "to": to_curr,
                        "pair": f"{from_curr}/{to_curr}"
                    })

        return pairs

    def get_currency_by_country(self, country_code: str) -> Optional[str]:
        """Получить валюту по коду страны"""
        country_currency_map = {
            "US": "USD", "RU": "RUB", "GB": "GBP", "DE": "EUR", "FR": "EUR",
            "IT": "EUR", "ES": "EUR", "JP": "JPY", "CN": "CNY", "KR": "KRW",
            "AE": "AED", "IL": "ILS", "IN": "INR", "BR": "BRL", "CA": "CAD",
            "AU": "AUD", "CH": "CHF", "SE": "SEK", "NO": "NOK", "DK": "DKK",
            "PL": "PLN", "CZ": "CZK", "HU": "HUF", "TR": "TRY", "ZA": "ZAR",
            "MX": "MXN", "SG": "SGD", "HK": "HKD", "NZ": "NZD", "TH": "THB",
            "MY": "MYR", "ID": "IDR", "PH": "PHP", "VN": "VND"
        }

        return country_currency_map.get(country_code.upper())

    def get_currency_by_locale(self, locale: str) -> Optional[str]:
        """Получить валюту по локали"""
        locale_currency_map = {
            "en": "USD", "ru": "RUB", "es": "EUR", "fr": "EUR", "de": "EUR",
            "it": "EUR", "pt": "EUR", "ja": "JPY", "ko": "KRW", "zh": "CNY",
            "ar": "AED", "he": "ILS", "hi": "INR", "pt-BR": "BRL", "en-CA": "CAD",
            "en-AU": "AUD", "de-CH": "CHF", "sv": "SEK", "no": "NOK", "da": "DKK",
            "pl": "PLN", "cs": "CZK", "hu": "HUF", "tr": "TRY", "af": "ZAR",
            "es-MX": "MXN", "en-SG": "SGD", "en-HK": "HKD", "en-NZ": "NZD",
            "th": "THB", "ms": "MYR", "id": "IDR", "fil": "PHP", "vi": "VND"
        }

        return locale_currency_map.get(locale)

    async def get_historical_rates(self, from_currency: str, to_currency: str, 
                                 start_date: datetime, end_date: datetime) -> Dict[str, Decimal]  # noqa  # noqa: E501 E501
        """Получить исторические курсы валют"""
        # Это упрощенная реализация - в реальном проекте нужно использовать
        # специализированные API для исторических данных
        rates = {}

        # Для демонстрации возвращаем случайные данные
        current_date = start_date
        while current_date <= end_date:
            # В реальном проекте здесь был бы запрос к API исторических данных
            rate = await self.get_exchange_rate(from_currency, to_currency)
            if rate:
                rates[current_date.strftime("%Y-%m-%d")] = rate
            current_date += timedelta(days=1)

        return rates

    def calculate_price_change(self, old_price: Decimal, new_price: Decimal) -> Dict[str, Any]  # noqa  # noqa: E501 E501
        """Рассчитать изменение цены"""
        if old_price == 0:
            return {
                "absolute_change": new_price,
                "percentage_change": 0,
                "direction": "up" if new_price > 0 else "down"
            }

        absolute_change = new_price - old_price
        percentage_change = (absolute_change / old_price) * 100

        return {
            "absolute_change": absolute_change,
            "percentage_change": percentage_change,
            "direction": "up" if absolute_change > 0 else "down" if absolute_change < 0 else "same"
        }

    def get_currency_emoji(self, currency_code: str) -> str:
        """Получить эмодзи для валюты"""
        currency_emojis = {
            "USD": "💵", "EUR": "💶", "RUB": "💴", "GBP": "💷", "JPY": "💴",
            "CNY": "💴", "KRW": "💴", "AED": "💴", "ILS": "💴", "INR": "💴",
            "BRL": "💴", "CAD": "💵", "AUD": "💵", "CHF": "💴", "SEK": "💴",
            "NOK": "💴", "DKK": "💴", "PLN": "💴", "CZK": "💴", "HUF": "💴",
            "TRY": "💴", "ZAR": "💴", "MXN": "💴", "SGD": "💴", "HKD": "💴",
            "NZD": "💵", "THB": "💴", "MYR": "💴", "IDR": "💴", "PHP": "💴",
            "VND": "💴", "BTC": "₿", "ETH": "Ξ", "LTC": "Ł", "XRP": "💎",
            "BCH": "₿", "ADA": "💎", "DOT": "💎", "LINK": "💎", "UNI": "💎"
        }

        return currency_emojis.get(currency_code.upper(), "💰")

# Глобальный экземпляр сервиса валют
currency_service = CurrencyService()
