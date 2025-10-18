# 🇷🇺 Российские маркетплейсы - Universal Parser

## Обзор

Модуль для работы с крупнейшими российскими маркетплейсами, включая Wildberries, Ozon, Яндекс.Маркет, Avito, М.Видео и Эльдорадо.

## Поддерживаемые маркетплейсы

### 🛍️ Wildberries
- **URL:** https://www.wildberries.ru
- **Метод:** API + HTML парсинг
- **Особенности:** 
  - Полная интеграция с API поиска
  - Поддержка фильтров по цене, бренду, рейтингу
  - Категории товаров
  - Информация о продавце и доставке
  - Кэширование результатов

### 🛒 Ozon
- **URL:** https://www.ozon.ru
- **Метод:** API + HTML парсинг
- **Особенности:**
  - Поиск по API
  - Фильтрация товаров
  - Категории и бренды
  - Информация о наличии

### 🔍 Яндекс.Маркет
- **URL:** https://market.yandex.ru
- **Метод:** HTML парсинг
- **Особенности:**
  - Сравнительный сервис
  - Множество продавцов
  - Детальная информация о товарах
  - Рейтинги и отзывы

### 📱 Avito
- **URL:** https://www.avito.ru
- **Метод:** HTML парсинг
- **Особенности:**
  - Площадка объявлений
  - Фильтрация по региону
  - Информация о продавце
  - Состояние товара

### 📺 М.Видео
- **URL:** https://www.mvideo.ru
- **Метод:** API
- **Особенности:**
  - Электроника и бытовая техника
  - API интеграция
  - Информация о гарантии
  - Доставка и самовывоз

### 🏪 Эльдорадо
- **URL:** https://www.eldorado.ru
- **Метод:** API
- **Особенности:**
  - Электроника и бытовая техника
  - API интеграция
  - Информация о гарантии
  - Доставка и самовывоз

## API Эндпоинты

### Получение списка маркетплейсов
```http
GET /api/v1/russian-marketplaces/marketplaces
```

### Поиск товаров
```http
GET /api/v1/russian-marketplaces/{marketplace}/search
```

**Параметры:**
- `query` - поисковый запрос
- `page` - номер страницы (по умолчанию 1)
- `price_min` - минимальная цена
- `price_max` - максимальная цена
- `brand` - бренд
- `rating` - минимальный рейтинг
- `discount` - только со скидкой
- `in_stock` - только в наличии
- `region` - регион (для Avito)
- `category` - категория
- `condition` - состояние (для Avito)

### Получение детальной информации о товаре
```http
GET /api/v1/russian-marketplaces/{marketplace}/product/{product_id}
```

### Получение категорий
```http
GET /api/v1/russian-marketplaces/{marketplace}/categories
```

### Получение фильтров
```http
GET /api/v1/russian-marketplaces/{marketplace}/filters
```

### Парсинг маркетплейса
```http
POST /api/v1/russian-marketplaces/{marketplace}/parse
```

**Тело запроса:**
```json
{
  "query": "iPhone 15",
  "page": 1,
  "filters": {
    "price_min": 50000,
    "price_max": 100000,
    "brand": "Apple"
  }
}
```

### Получение статистики
```http
GET /api/v1/russian-marketplaces/{marketplace}/stats
```

## Использование

### Python
```python
import asyncio
from app.services.russian_marketplace_parsers import RussianMarketplaceService

async def main():
    service = RussianMarketplaceService()
    
    # Поиск товаров на Wildberries
    products = await service.search_products(
        marketplace="wildberries",
        query="iPhone 15",
        page=1,
        filters={"price_min": 50000, "brand": "Apple"}
    )
    
    print(f"Найдено {len(products)} товаров")
    for product in products:
        print(f"{product['title']} - {product['price']} ₽")

asyncio.run(main())
```

### HTTP запрос
```bash
curl -X GET "http://localhost:8000/api/v1/russian-marketplaces/wildberries/search?query=iPhone%2015&price_min=50000&brand=Apple"
```

## Конфигурация

### Настройки парсинга
```python
# В app/core/config.py
RUSSIAN_MARKETPLACES = {
    "cache_ttl": 3600,  # Время кэширования в секундах
    "max_retries": 3,   # Максимум попыток
    "delay_min": 1,     # Минимальная задержка
    "delay_max": 3,     # Максимальная задержка
    "use_proxy": False, # Использовать прокси
    "rotate_headers": True  # Ротация заголовков
}
```

### Заголовки запросов
Каждый маркетплейс использует специфичные заголовки для обхода защиты:
- User-Agent ротация
- Accept-Language: ru-RU
- Referer и Origin для каждого маркетплейса

## Кэширование

Все результаты поиска кэшируются в Redis на 1 час для оптимизации производительности.

**Ключи кэша:**
- `wildberries_search:{query}:{page}:{filters}` - результаты поиска
- `wildberries_product:{id}` - детальная информация о товаре

## Обработка ошибок

- **400 Bad Request** - неподдерживаемый маркетплейс
- **404 Not Found** - товар или категории не найдены
- **500 Internal Server Error** - ошибка парсинга

## Мониторинг

### Метрики
- Количество запросов к каждому маркетплейсу
- Время ответа
- Успешность парсинга
- Использование кэша

### Логирование
```python
import logging

logger = logging.getLogger("russian_marketplaces")
logger.info(f"Searching {marketplace} for '{query}'")
logger.error(f"Failed to parse {marketplace}: {error}")
```

## Дашборд

Веб-интерфейс для работы с российскими маркетплейсами доступен по адресу:
```
http://localhost:8501
```

**Функции дашборда:**
- Поиск товаров с фильтрами
- Просмотр статистики маркетплейсов
- Управление категориями
- Настройки парсинга
- Тест подключения

## Развертывание

### Docker
```bash
docker-compose up -d
```

### Локально
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Запуск дашборда
streamlit run dashboard/main.py --server.port 8501
```

## Безопасность

- Ротация User-Agent
- Случайные задержки между запросами
- Ограничение частоты запросов
- Валидация входных данных
- Защита от SQL-инъекций

## Производительность

- Асинхронные запросы
- Кэширование результатов
- Пакетная обработка
- Оптимизация селекторов
- Сжатие ответов

## Поддержка

Для вопросов и предложений создайте issue в репозитории или обратитесь к документации API.

## Лицензия

MIT License - см. файл LICENSE для деталей.
