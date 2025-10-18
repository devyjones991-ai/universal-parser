# Universal Parser v0.2.0 - FastAPI Edition

🚀 **Мощная платформа для отслеживания товаров, цен и аналитики на маркетплейсах**

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/your-username/universal-parser)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 🎯 Что нового в v0.2.0

### ✨ **FastAPI Architecture**
- **Современный REST API** с автоматической документацией
- **Pydantic валидация** для всех запросов и ответов
- **Асинхронная обработка** для высокой производительности
- **OpenAPI/Swagger** документация из коробки

### 🏗️ **Улучшенная архитектура**
- **Модульная структура** с разделением на слои
- **Dependency Injection** для тестируемости
- **Сервисный слой** для бизнес-логики
- **Схемы Pydantic** для типизации

### 🚀 **Производительность**
- **SQLAlchemy 2.0** с современным синтаксисом
- **Асинхронные операции** с базой данных
- **Подготовка к Redis** кэшированию
- **Docker** контейнеризация

## 🛠 Быстрый старт

### 1. Клонирование и установка

```bash
git clone <repository-url>
cd universal-parser
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env`:
```env
# Основные настройки
APP_NAME=Universal Parser
APP_VERSION=0.2.0
DEBUG=false

# API настройки
API_V1_PREFIX=/api/v1
SECRET_KEY=your-secret-key-here

# База данных
DATABASE_URL=sqlite:///./universal_parser.db
# Для PostgreSQL: postgresql://user:password@localhost/universal_parser

# Redis (опционально)
REDIS_URL=redis://localhost:6379

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id
ADMIN_CHAT_IDS=[123456789, 987654321]

# Парсинг
DEFAULT_TIMEOUT=15
MAX_CONCURRENT_REQUESTS=10
USE_PROXY=false
```

### 3. Инициализация базы данных

```bash
python -c "from app.core.database import init_db; init_db()"
```

### 4. Запуск приложения

#### Обычный запуск:
```bash
python main_fastapi.py
```

#### С uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### С Docker:
```bash
docker-compose -f docker-compose.fastapi.yml up --build
```

## 📚 API Документация

После запуска приложения доступна интерактивная документация:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔗 Основные API эндпоинты

### Товары (Items)
- `GET /api/v1/items/` - Список отслеживаемых товаров
- `POST /api/v1/items/` - Добавить новый товар
- `GET /api/v1/items/{item_id}` - Получить товар по ID
- `PUT /api/v1/items/{item_id}` - Обновить товар
- `DELETE /api/v1/items/{item_id}` - Удалить товар
- `GET /api/v1/items/{item_id}/history` - История цен товара
- `POST /api/v1/items/{item_id}/refresh` - Обновить данные товара

### Система
- `GET /` - Информация об API
- `GET /health` - Проверка здоровья системы

## 🏗️ Архитектура

```
app/
├── main.py                 # FastAPI приложение
├── core/                   # Основные компоненты
│   ├── config.py          # Конфигурация
│   └── database.py        # База данных
├── models/                 # SQLAlchemy модели
│   ├── user.py            # Пользователи
│   ├── item.py            # Товары
│   └── alert.py           # Алерты
├── schemas/                # Pydantic схемы
│   ├── user.py            # Схемы пользователей
│   └── item.py            # Схемы товаров
├── services/               # Бизнес-логика
│   └── item_service.py    # Сервис товаров
└── api/                    # API эндпоинты
    └── v1/
        └── endpoints/
            └── items.py    # Эндпоинты товаров
```

## 🐳 Docker

### Простой запуск:
```bash
docker build -f Dockerfile.fastapi -t universal-parser:latest .
docker run -p 8000:8000 universal-parser:latest
```

### Полный стек с мониторингом:
```bash
docker-compose -f docker-compose.fastapi.yml up -d
```

Сервисы:
- **App**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090

## 🔧 Разработка

### Установка зависимостей для разработки:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Если есть
```

### Запуск тестов:
```bash
pytest
```

### Линтинг:
```bash
black app/
isort app/
flake8 app/
mypy app/
```

## 📈 Мониторинг

### Health Check
```bash
curl http://localhost:8000/health
```

### Метрики (с Prometheus)
```bash
curl http://localhost:8000/metrics
```

## 🚀 Следующие шаги

### Планируемые улучшения:
- [ ] **Redis кэширование** для повышения производительности
- [ ] **PostgreSQL** миграция для продакшена
- [ ] **Celery** для фоновых задач
- [ ] **Аутентификация** с JWT токенами
- [ ] **Веб-дашборд** на Streamlit
- [ ] **AI функции** для анализа трендов
- [ ] **Мобильное приложение**

## 🤝 Поддержка

- 📧 Email: support@universal-parser.com
- 💬 Telegram: @universal_parser_support
- 📖 Документация: [docs.universal-parser.com](https://docs.universal-parser.com)
- 🐛 Issues: [GitHub Issues](https://github.com/universal-parser/universal-parser/issues)

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

**Universal Parser v0.2.0** - ваш надежный помощник в мире e-commerce! 🚀
