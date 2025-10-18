# Universal Parser v0.1.0

🚀 **Мощная платформа для отслеживания товаров, цен и аналитики на маркетплейсах**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/your-username/universal-parser)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🎯 Основные возможности

### 📦 Отслеживание товаров
- **Мультиплатформенность**: Wildberries, Ozon, Яндекс.Маркет
- **Автоматическое обновление** цен и остатков
- **История изменений** с детальной аналитикой
- **Массовое добавление** товаров через файлы

### 🔔 Умные алерты
- **Падение/рост цен** с настраиваемыми порогами
- **Изменение остатков** и появление товаров
- **Уведомления в Telegram** с быстрыми действиями
- **Персонализированные условия** для каждого товара

### 📈 Аналитика и отчеты
- **Графики динамики цен** с трендами
- **Сравнительный анализ** товаров
- **Экспорт в Excel** с детальными данными
- **AI-рекомендации** на основе истории

### 💳 Система подписок
- **Бесплатный тариф**: 3 товара, 5 алертов
- **Premium**: 50 товаров, расширенная аналитика
- **Enterprise**: без ограничений, API доступ

## 🛠 Установка и настройка

### 1. Клонирование и установка зависимостей

```bash
git clone <repository-url>
cd universal-parser
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id
ADMIN_CHAT_IDS=[123456789, 987654321]

# База данных
DATABASE_URL=sqlite:///universal_parser.db

# Настройки парсинга
DEFAULT_TIMEOUT=15
MAX_CONCURRENT_REQUESTS=10
USE_PROXY=false
PROXY_URL=

# Настройки экспорта
EXPORT_FORMAT=json
MAX_RESULTS_PER_MESSAGE=50
```

### 3. Инициализация базы данных

```bash
python -c "from db import init_db; init_db()"
```

### 4. Запуск приложения

```bash
python main.py
```

## 🤖 Telegram Bot команды

### Основные команды
- `/start` - запуск и регистрация
- `/monitor` - добавить товар для отслеживания
- `/myitems` - показать ваши товары
- `/alerts` - настроить алерты
- `/stats` - ваша статистика
- `/analytics` - аналитика и отчеты
- `/subscription` - управление подпиской

### Админские команды
- `/profiles` - список профилей парсинга
- `/parse <url>` - парсить произвольный URL
- `/run <profile>` - запустить профиль парсинга
- `/results` - последние результаты
- `/export` - экспорт данных

## 📊 Архитектура системы

### Основные модули

```
universal-parser/
├── main.py                 # Точка входа приложения
├── db.py                   # Модели и функции базы данных
├── parser.py              # Универсальный парсер
├── tg_commands.py         # Telegram Bot команды
├── alert_system.py        # Система алертов и уведомлений
├── analytics.py           # Аналитика и отчеты
├── subscription.py        # Система подписок
├── scheduler.py           # Планировщик задач
├── config.py              # Конфигурация
└── profiles/
    └── parsing_profiles.json  # Профили парсинга
```

### База данных

**Таблицы:**
- `users` - пользователи системы
- `tracked_items` - отслеживаемые товары
- `alerts` - настройки алертов
- `price_history` - история цен
- `parse_results` - результаты парсинга

## 🔧 Настройка профилей парсинга

Создайте профили в `profiles/parsing_profiles.json`:

```json
{
  "wildberries_search": {
    "name": "Wildberries Search",
    "url": "https://search.wb.ru/exactmatch/ru/common/v4/search",
    "method": "api",
    "params": {
      "appType": "1",
      "curr": "rub",
      "dest": "-1257786",
      "query": "{search_term}",
      "resultset": "catalog",
      "sort": "popular",
      "spp": "27"
    },
    "data_path": "data.products",
    "fields": {
      "name": "name",
      "price": "priceU",
      "rating": "reviewRating",
      "id": "id"
    }
  }
}
```

## 🚀 Развертывание в продакшене

### Docker (рекомендуется)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Systemd сервис

```ini
[Unit]
Description=Universal Parser Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/universal-parser
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📈 Мониторинг и логирование

Система включает:
- **Автоматическое логирование** всех операций
- **Мониторинг производительности** парсинга
- **Уведомления об ошибках** администраторам
- **Метрики использования** для аналитики

## 🔒 Безопасность

- **Валидация входных данных** для всех API
- **Ограничение частоты запросов** к маркетплейсам
- **Шифрование чувствительных данных**
- **Аудит действий пользователей**

## 🤝 Поддержка и развитие

### Roadmap
- [ ] Интеграция с дополнительными маркетплейсами
- [ ] AI-анализ трендов и рекомендации
- [ ] API для внешних интеграций
- [ ] Мобильное приложение
- [ ] Расширенная аналитика с ML

### Поддержка
- 📧 Email: support@universal-parser.com
- 💬 Telegram: @universal_parser_support
- 📖 Документация: [docs.universal-parser.com](https://docs.universal-parser.com)

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

**Universal Parser** - ваш надежный помощник в мире e-commerce! 🚀
