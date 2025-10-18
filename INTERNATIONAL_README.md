# 🌍 Интернационализация и локализация - Universal Parser

## Обзор

Модуль интернационализации предоставляет полную поддержку многоязычности, мультивалютности и работы с часовыми поясами для глобальной аудитории.

## Основные функции

### 🌐 Интернационализация (i18n)
- **Поддержка 12+ языков** - английский, русский, испанский, французский, немецкий, итальянский, португальский, японский, корейский, китайский, арабский, иврит
- **RTL поддержка** - для арабского и иврита
- **Автоматическое определение языка** - по тексту
- **Локализованные форматы** - даты, времени, чисел, валют
- **Динамические переводы** - через API

### 💱 Мультивалютная поддержка
- **40+ валют** - включая фиатные и криптовалюты
- **Реальные курсы** - через API обмена валют
- **Автоматическая конвертация** - между любыми валютами
- **Локализованное форматирование** - согласно стандартам стран
- **Исторические данные** - курсы за период

### 🕐 Часовые пояса
- **50+ часовых поясов** - все основные регионы мира
- **Автоматическое определение** - по стране/локали
- **Конвертация времени** - между любыми поясами
- **Рабочие часы** - с учетом локального времени
- **Летнее время** - автоматическое определение

## Поддерживаемые языки

### Латинские языки
- **English (en)** - Английский
- **Español (es)** - Испанский
- **Français (fr)** - Французский
- **Deutsch (de)** - Немецкий
- **Italiano (it)** - Итальянский
- **Português (pt)** - Португальский

### Азиатские языки
- **日本語 (ja)** - Японский
- **한국어 (ko)** - Корейский
- **中文 (zh)** - Китайский

### RTL языки
- **العربية (ar)** - Арабский
- **עברית (he)** - Иврит

### Славянские языки
- **Русский (ru)** - Русский

## API Эндпоинты

### Локали и переводы
```http
GET /api/v1/international/locales
GET /api/v1/international/locales/{locale_code}
GET /api/v1/international/translations?locale={locale}&namespace={namespace}
POST /api/v1/international/translations
GET /api/v1/international/text/{key}?locale={locale}
```

### Валюты и конвертация
```http
GET /api/v1/international/currencies
GET /api/v1/international/currencies/{currency_code}
POST /api/v1/international/currencies/convert
GET /api/v1/international/currencies/rates?from_currency={from}&to_currencies={to}
```

### Часовые пояса
```http
GET /api/v1/international/timezones
GET /api/v1/international/timezones/{timezone_name}
POST /api/v1/international/timezones/convert
GET /api/v1/international/timezones/current/{timezone_name}
GET /api/v1/international/timezones/groups
GET /api/v1/international/timezones/working-hours/{timezone_name}
```

### Форматирование
```http
GET /api/v1/international/format/currency?amount={amount}&currency={currency}&locale={locale}
GET /api/v1/international/format/datetime?datetime_str={datetime}&locale={locale}&timezone={tz}
GET /api/v1/international/detect-language?text={text}
```

## Использование

### Python API
```python
from app.core.i18n import get_text, format_currency, format_datetime, is_rtl
from app.services.currency_service import currency_service
from app.services.timezone_service import timezone_service

# Получение переведенного текста
text = get_text("common.save", locale="ru")  # "Сохранить"

# Форматирование валюты
formatted = format_currency(1234.56, "RUB", "ru")  # "1 234,56 ₽"

# Форматирование даты
formatted_date = format_datetime(datetime.now(), "ru", "Europe/Moscow")

# Проверка RTL
is_rtl_lang = is_rtl("ar")  # True

# Конвертация валют
converted = await currency_service.convert_currency(
    Decimal("100"), "USD", "RUB"
)

# Конвертация времени
converted_time = timezone_service.convert_datetime(
    datetime.now(), "UTC", "Europe/Moscow"
)
```

### HTTP запросы
```bash
# Получение переведенного текста
curl "http://localhost:8000/api/v1/international/text/common.save?locale=ru"

# Конвертация валюты
curl -X POST "http://localhost:8000/api/v1/international/currencies/convert" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "from_currency": "USD", "to_currency": "RUB"}'

# Конвертация времени
curl -X POST "http://localhost:8000/api/v1/international/timezones/convert" \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2024-01-01T12:00:00", "from_timezone": "UTC", "to_timezone": "Europe/Moscow"}'

# Определение языка
curl "http://localhost:8000/api/v1/international/detect-language?text=Привет мир"
```

## Конфигурация

### Настройки i18n
```python
I18N = {
    "default_locale": "en",
    "supported_locales": ["en", "ru", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ar", "he"],
    "rtl_languages": ["ar", "he", "fa", "ur"],
    "translations_dir": "app/translations",
    "fallback_locale": "en"
}
```

### Настройки валют
```python
CURRENCY = {
    "default_currency": "USD",
    "supported_currencies": ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "KRW", "AED", "ILS"],
    "crypto_currencies": ["BTC", "ETH", "LTC", "XRP", "BCH"],
    "exchange_api": "exchangerate-api.com",
    "cache_duration": 3600,  # 1 час
    "update_interval": 300   # 5 минут
}
```

### Настройки часовых поясов
```python
TIMEZONE = {
    "default_timezone": "UTC",
    "popular_timezones": [
        "UTC", "America/New_York", "Europe/London", "Europe/Moscow",
        "Asia/Tokyo", "Asia/Shanghai", "Australia/Sydney"
    ],
    "country_mapping": {
        "US": "America/New_York",
        "RU": "Europe/Moscow",
        "GB": "Europe/London",
        "JP": "Asia/Tokyo"
    }
}
```

## Структура файлов переводов

### Формат JSON
```json
{
  "app": {
    "name": "Universal Parser",
    "description": "Comprehensive marketplace monitoring platform"
  },
  "common": {
    "loading": "Loading...",
    "error": "Error",
    "success": "Success"
  },
  "navigation": {
    "overview": "Overview",
    "analytics": "Analytics"
  },
  "currencies": {
    "usd": "US Dollar",
    "eur": "Euro"
  }
}
```

### Поддержка параметров
```json
{
  "welcome": "Welcome, {username}! You have {count} items.",
  "price_change": "Price changed by {percent}% to {price} {currency}"
}
```

## Дашборд

### Основные вкладки
- **🌐 Локали** - управление языками и переводами
- **💱 Валюты** - конвертация и курсы валют
- **🕐 Часовые пояса** - конвертация времени
- **📝 Переводы** - редактирование переводов
- **🔧 Настройки** - конфигурация локализации

### Интерактивные функции
- **Выбор языка** - переключение интерфейса
- **Конвертер валют** - реальное время
- **Конвертер времени** - между поясами
- **Определение языка** - автоматическое
- **Форматирование** - дат, валют, чисел

## Поддерживаемые валюты

### Фиатные валюты
- **USD** - Доллар США 💵
- **EUR** - Евро 💶
- **RUB** - Российский рубль 💴
- **GBP** - Британский фунт 💷
- **JPY** - Японская иена 💴
- **CNY** - Китайский юань 💴
- **KRW** - Южнокорейская вона 💴
- **AED** - Дирхам ОАЭ 💴
- **ILS** - Израильский шекель 💴

### Криптовалюты
- **BTC** - Биткоин ₿
- **ETH** - Эфириум Ξ
- **LTC** - Лайткоин Ł
- **XRP** - Ripple 💎
- **BCH** - Bitcoin Cash ₿

## Поддерживаемые часовые пояса

### Америка
- **America/New_York** - Восточное время (США) 🇺🇸
- **America/Los_Angeles** - Тихоокеанское время (США) 🇺🇸
- **America/Chicago** - Центральное время (США) 🇺🇸
- **America/Sao_Paulo** - Бразильское время 🇧🇷
- **America/Mexico_City** - Центральное время (Мексика) 🇲🇽
- **America/Toronto** - Восточное время (Канада) 🇨🇦

### Европа
- **Europe/London** - Гринвичское время 🇬🇧
- **Europe/Paris** - Центральноевропейское время 🇫🇷
- **Europe/Berlin** - Центральноевропейское время 🇩🇪
- **Europe/Moscow** - Московское время 🇷🇺
- **Europe/Rome** - Центральноевропейское время 🇮🇹
- **Europe/Madrid** - Центральноевропейское время 🇪🇸

### Азия
- **Asia/Tokyo** - Японское стандартное время 🇯🇵
- **Asia/Seoul** - Корейское стандартное время 🇰🇷
- **Asia/Shanghai** - Китайское стандартное время 🇨🇳
- **Asia/Dubai** - Время Персидского залива 🇦🇪
- **Asia/Jerusalem** - Израильское стандартное время 🇮🇱
- **Asia/Kolkata** - Индийское стандартное время 🇮🇳

### Океания
- **Australia/Sydney** - Австралийское восточное время 🇦🇺
- **Pacific/Auckland** - Новозеландское стандартное время 🇳🇿

## RTL поддержка

### Поддерживаемые языки
- **Арабский (ar)** - справа налево
- **Иврит (he)** - справа налево
- **Фарси (fa)** - справа налево
- **Урду (ur)** - справа налево

### Особенности RTL
- **Направление текста** - автоматическое определение
- **Выравнивание** - по правому краю
- **Навигация** - зеркальное отображение
- **Иконки** - адаптированные для RTL

## Производительность

### Оптимизации
- **Кэширование переводов** - Redis для быстрого доступа
- **Ленивая загрузка** - переводы по требованию
- **Сжатие данных** - минификация JSON файлов
- **CDN поддержка** - статические файлы переводов
- **Предзагрузка** - популярные языки

### Мониторинг
- **Использование языков** - статистика по локалям
- **Производительность API** - время ответа
- **Кэш попадания** - эффективность кэширования
- **Ошибки переводов** - отсутствующие ключи

## Безопасность

### Валидация
- **Проверка локалей** - только поддерживаемые
- **Санитизация входных данных** - XSS защита
- **Валидация валют** - проверка кодов
- **Проверка часовых поясов** - существование

### Контроль доступа
- **Права на переводы** - только для админов
- **Аудит изменений** - логирование
- **Резервное копирование** - файлов переводов
- **Версионирование** - контроль изменений

## Развертывание

### Требования
- Python 3.8+
- Babel для локализации
- pytz для часовых поясов
- Redis для кэширования
- API ключи для курсов валют

### Установка
```bash
# Установка зависимостей
pip install babel pytz

# Настройка переводов
python -m app.core.i18n

# Запуск с поддержкой i18n
python -m app.main
```

### Docker
```bash
# Запуск с интернационализацией
docker-compose up -d

# Проверка переводов
docker exec -it universal-parser python -m app.core.i18n
```

## Мониторинг и логирование

### Логи
```python
import logging

logger = logging.getLogger("i18n")
logger.info(f"Translation loaded for locale: {locale}")
logger.error(f"Missing translation key: {key}")
```

### Метрики
- Количество активных локалей
- Популярность языков
- Использование валют
- Конвертации времени

## Поддержка

Для вопросов по интернационализации создайте issue в репозитории или обратитесь к документации API.

## Лицензия

MIT License - см. файл LICENSE для деталей.
