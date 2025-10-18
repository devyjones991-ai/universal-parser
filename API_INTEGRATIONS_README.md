# 🔌 API & Integrations - Universal Parser

## Обзор

Модуль API & Integrations предоставляет расширенные возможности интеграции, включая webhook'и, GraphQL API, WebSocket соединения, rate limiting и аналитику использования API.

## Основные функции

### 🔗 Webhook система
- **Управление webhook'ами** - создание, обновление, удаление endpoints
- **Подписка на события** - 15+ типов событий (создание товаров, изменения цен, пользователи)
- **Надежная доставка** - повторные попытки, экспоненциальная задержка
- **Подпись запросов** - HMAC SHA-256 для безопасности
- **Мониторинг доставки** - статусы, логи, статистика

### 📊 GraphQL API
- **Гибкие запросы** - получение только нужных данных
- **Real-time подписки** - WebSocket для live обновлений
- **Интроспекция** - автоматическая документация
- **Playground** - интерактивная среда для тестирования
- **Оптимизация** - N+1 запросы, кэширование

### 🌐 WebSocket соединения
- **Real-time обновления** - мгновенные уведомления
- **Комнаты** - группировка соединений по темам
- **Подписки на события** - выборочная доставка
- **Масштабируемость** - поддержка тысяч соединений
- **Heartbeat** - мониторинг состояния соединений

### ⚡ Rate Limiting
- **Sliding window** - точное ограничение запросов
- **Множественные лимиты** - по пользователям, IP, эндпоинтам
- **Burst protection** - защита от всплесков трафика
- **Гибкая настройка** - разные лимиты для разных API
- **Мониторинг** - статистика использования лимитов

### 📈 API Аналитика
- **Метрики производительности** - время ответа, пропускная способность
- **Использование по пользователям** - активность, популярные эндпоинты
- **Статистика ошибок** - типы, частота, причины
- **Prometheus метрики** - интеграция с мониторингом
- **Real-time дашборд** - визуализация данных

## Webhook система

### Поддерживаемые события
```json
{
  "item.created": "Товар создан",
  "item.updated": "Товар обновлен", 
  "item.deleted": "Товар удален",
  "price.changed": "Цена изменилась",
  "user.registered": "Пользователь зарегистрирован",
  "user.subscribed": "Пользователь подписался",
  "payment.received": "Платеж получен",
  "parsing.started": "Парсинг начат",
  "parsing.completed": "Парсинг завершен",
  "parsing.failed": "Парсинг не удался",
  "analytics.generated": "Аналитика сгенерирована",
  "report.scheduled": "Отчет запланирован",
  "social.post_created": "Социальный пост создан",
  "achievement.unlocked": "Достижение разблокировано"
}
```

### Создание webhook endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/endpoints" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["item.created", "price.changed"],
    "secret": "your-webhook-secret",
    "retry_count": 3,
    "timeout": 30
  }'
```

### Проверка подписи webhook
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret, timestamp):
    message = f"{timestamp}.{payload}"
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

## GraphQL API

### Основные запросы
```graphql
# Получить товары
query GetItems {
  items(first: 10) {
    edges {
      node {
        id
        name
        marketplace
        price
        currentPrice
        priceChangePercent
      }
    }
  }
}

# Поиск товаров
query SearchItems {
  searchItems(query: "iPhone") {
    id
    name
    price
    marketplace
    marketplaceDisplayName
  }
}

# Аналитика
query GetAnalytics {
  analyticsOverview {
    totalItems
    totalUsers
    totalRevenue
    averageResponseTime
    errorRate
  }
}

# Создание товара
mutation CreateItem {
  createItem(input: {
    name: "Test Item"
    marketplace: "wildberries"
    category: "electronics"
    price: 1000.0
  }) {
    id
    name
    price
  }
}

# Подписка на изменения
subscription ItemUpdated {
  itemUpdated(itemId: "item-id") {
    id
    name
    price
    updatedAt
  }
}
```

### GraphQL Playground
- **URL**: `http://localhost:8000/api/v1/graphql`
- **Интроспекция**: `http://localhost:8000/api/v1/graphql/schema`
- **Метрики**: `http://localhost:8000/api/v1/graphql/health`

## WebSocket соединения

### Подключение
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/websocket/ws?user_id=123');

ws.onopen = function() {
    console.log('WebSocket connected');
    
    // Подписаться на события
    ws.send(JSON.stringify({
        type: 'subscribe',
        events: ['item.updated', 'price.changed']
    }));
    
    // Присоединиться к комнате
    ws.send(JSON.stringify({
        type: 'join_room',
        room_id: 'marketplace_updates'
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

### Типы сообщений
```json
{
  "type": "item.updated",
  "data": {
    "id": "item-123",
    "name": "iPhone 15",
    "price": 999.99,
    "old_price": 1099.99
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "user_id": "user-123",
  "room": "marketplace_updates"
}
```

## Rate Limiting

### Настройки лимитов
```python
RATE_LIMITS = {
    "global": {"requests": 1000, "window": 3600},  # 1000/час
    "api": {"requests": 100, "window": 60},        # 100/минуту
    "auth": {"requests": 10, "window": 60},        # 10/минуту
    "parsing": {"requests": 50, "window": 60},     # 50/минуту
    "webhook": {"requests": 1000, "window": 60},   # 1000/минуту
    "user": {"requests": 1000, "window": 3600},    # 1000/час
    "ip": {"requests": 500, "window": 3600}        # 500/час
}
```

### Заголовки ответа
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
Retry-After: 60
```

### Проверка лимитов
```python
from app.core.rate_limiting import check_api_rate_limit

is_allowed, rate_limit_info = await check_api_rate_limit(
    request=request,
    limit_name="api",
    user_id="user-123"
)

if not is_allowed:
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit exceeded"},
        headers=rate_limit_middleware.get_rate_limit_headers(rate_limit_info)
    )
```

## API Аналитика

### Метрики производительности
```bash
# Общая статистика
curl "http://localhost:8000/api/v1/analytics/usage?start_time=2024-01-01T00:00:00Z"

# Статистика эндпоинта
curl "http://localhost:8000/api/v1/analytics/endpoints/items/stats"

# Статистика пользователя
curl "http://localhost:8000/api/v1/analytics/users/user-123/stats"

# Rate limit статистика
curl "http://localhost:8000/api/v1/analytics/rate-limits"

# Prometheus метрики
curl "http://localhost:8000/api/v1/analytics/metrics"
```

### Пример ответа
```json
{
  "total_requests": 15420,
  "unique_users": 1250,
  "unique_ips": 890,
  "average_response_time": 0.245,
  "error_rate": 2.1,
  "top_endpoints": [
    {"endpoint": "GET /api/v1/items", "count": 5420},
    {"endpoint": "POST /api/v1/parsing", "count": 2100}
  ],
  "top_users": [
    {"user_id": "user-123", "count": 450},
    {"user_id": "user-456", "count": 380}
  ],
  "hourly_requests": [
    {"hour": "2024-01-01 10:00", "count": 120},
    {"hour": "2024-01-01 11:00", "count": 150}
  ]
}
```

## Интеграции

### Внешние API
- **Google Analytics** - отслеживание событий
- **Facebook Pixel** - конверсии и ретаргетинг
- **Telegram Bot** - уведомления пользователей
- **Slack** - уведомления команды
- **Discord** - интеграция с сообществами
- **Zapier** - автоматизация workflows
- **IFTTT** - простые интеграции

### Платежные системы
- **Stripe** - обработка платежей
- **PayPal** - альтернативные платежи
- **YooKassa** - российские платежи
- **Tinkoff** - банковские переводы
- **QIWI** - электронные кошельки

### Облачные сервисы
- **AWS S3** - хранение файлов
- **Google Cloud Storage** - резервное копирование
- **Azure Blob** - мультиоблачное хранение
- **CloudFlare** - CDN и защита
- **Redis Cloud** - кэширование

## Мониторинг и логирование

### Метрики
- **Запросы в секунду** - RPS
- **Время ответа** - latency (p50, p95, p99)
- **Процент ошибок** - error rate
- **Доступность** - uptime
- **Пропускная способность** - throughput

### Логи
```python
import logging

logger = logging.getLogger("api")
logger.info(f"API request: {method} {path} - {status_code} - {response_time}ms")
logger.error(f"API error: {error} - {traceback}")
logger.warning(f"Rate limit hit: {user_id} - {limit_name}")
```

### Алерты
- **Высокий процент ошибок** - >5%
- **Медленные запросы** - >1 секунды
- **Превышение лимитов** - >1000/час
- **Недоступность сервиса** - <99%
- **Аномальная активность** - >10x обычного

## Безопасность

### Аутентификация
- **JWT токены** - stateless авторизация
- **OAuth 2.0** - внешние провайдеры
- **API ключи** - для сервисов
- **Webhook подписи** - HMAC SHA-256

### Защита
- **Rate limiting** - защита от DDoS
- **CORS** - настройка доменов
- **HTTPS** - шифрование трафика
- **Валидация** - проверка входных данных
- **Санитизация** - очистка данных

### Аудит
- **Логи доступа** - кто и когда
- **Изменения данных** - что изменилось
- **Попытки взлома** - подозрительная активность
- **Соответствие** - GDPR, PCI DSS

## Производительность

### Оптимизации
- **Кэширование** - Redis для частых запросов
- **Индексы БД** - быстрый поиск
- **Пагинация** - ограничение результатов
- **Сжатие** - gzip для ответов
- **CDN** - статические ресурсы

### Масштабирование
- **Горизонтальное** - больше серверов
- **Вертикальное** - больше ресурсов
- **Балансировка** - распределение нагрузки
- **Кэширование** - уменьшение нагрузки на БД
- **Очереди** - асинхронная обработка

### Мониторинг
- **APM** - Application Performance Monitoring
- **Логи** - централизованное логирование
- **Метрики** - Prometheus + Grafana
- **Трейсинг** - распределенная трассировка
- **Алерты** - уведомления о проблемах

## Развертывание

### Docker
```bash
# Запуск с API интеграциями
docker-compose up -d

# Проверка webhook'ов
docker exec -it universal-parser python -m app.services.webhook_service

# Тест GraphQL
curl "http://localhost:8000/api/v1/graphql/health"
```

### Конфигурация
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - WEBHOOK_SECRET=your-webhook-secret
      - RATE_LIMIT_REDIS_URL=redis://redis:6379
      - GRAPHQL_PLAYGROUND=true
      - WEBSOCKET_HEARTBEAT=30
```

### Мониторинг
```bash
# Проверка состояния
curl "http://localhost:8000/api/v1/analytics/health"

# Метрики Prometheus
curl "http://localhost:8000/api/v1/analytics/metrics"

# Статистика WebSocket
curl "http://localhost:8000/api/v1/websocket/connections"
```

## Поддержка

Для вопросов по API интеграциям создайте issue в репозитории или обратитесь к документации API.

## Лицензия

MIT License - см. файл LICENSE для деталей.
