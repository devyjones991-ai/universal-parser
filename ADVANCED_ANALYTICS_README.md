# 📊 Расширенная аналитика и отчеты - Universal Parser

## Обзор

Модуль расширенной аналитики предоставляет мощные инструменты для глубокого анализа данных, создания пользовательских отчетов и автоматизации их генерации.

## Основные функции

### 📈 Расширенная аналитика
- **Обзорные метрики** - ключевые показатели системы
- **Анализ цен** - детальный анализ цен и трендов
- **Аналитика пользователей** - поведение и активность пользователей
- **Социальная аналитика** - вовлеченность и взаимодействие
- **Предиктивная аналитика** - прогнозы и предсказания

### 📊 Интерактивные дашборды
- **Временные фильтры** - анализ за различные периоды
- **Мульти-маркетплейс сравнение** - сравнение по платформам
- **Категорийный анализ** - глубокий анализ по категориям
- **Реальные метрики** - данные в реальном времени
- **Экспорт данных** - в различных форматах

### 📅 Планировщик отчетов
- **Автоматическая генерация** - по расписанию
- **Email уведомления** - отправка на почту
- **Шаблоны отчетов** - готовые конфигурации
- **Гибкие фильтры** - настройка параметров
- **Множественные форматы** - PDF, Excel, CSV, JSON

## API Эндпоинты

### Расширенная аналитика
```http
GET /api/v1/advanced-analytics/overview
GET /api/v1/advanced-analytics/price-analysis
GET /api/v1/advanced-analytics/user-analytics
GET /api/v1/advanced-analytics/social-analytics
GET /api/v1/advanced-analytics/predictive-analytics
GET /api/v1/advanced-analytics/real-time-metrics
GET /api/v1/advanced-analytics/dashboard-data
GET /api/v1/advanced-analytics/marketplace-comparison
```

### Экспорт данных
```http
GET /api/v1/advanced-analytics/export/{report_type}?format={format}
```

### Планировщик отчетов
```http
POST /api/v1/report-scheduler/schedules
GET /api/v1/report-scheduler/schedules
PUT /api/v1/report-scheduler/schedules/{report_type}
DELETE /api/v1/report-scheduler/schedules/{report_type}
POST /api/v1/report-scheduler/schedules/{report_type}/toggle
POST /api/v1/report-scheduler/schedules/{report_type}/run-now
GET /api/v1/report-scheduler/status
POST /api/v1/report-scheduler/start
POST /api/v1/report-scheduler/stop
GET /api/v1/report-scheduler/templates
GET /api/v1/report-scheduler/history
```

## Типы отчетов

### 📊 Анализ цен
- **Тренды цен** - изменение цен во времени
- **Распределение цен** - статистика и процентили
- **Сравнение маркетплейсов** - цены по платформам
- **Категорийный анализ** - цены по категориям
- **Волатильность** - стабильность цен

### 👥 Аналитика пользователей
- **Активность** - ежедневная и еженедельная
- **Конверсия** - регистрация и удержание
- **География** - распределение по странам
- **Подписки** - анализ тарифных планов
- **Топ пользователи** - самые активные

### 📱 Социальная аналитика
- **Вовлеченность** - лайки, комментарии, просмотры
- **Популярный контент** - топ посты
- **Типы контента** - анализ форматов
- **Временная активность** - по часам и дням
- **Социальные метрики** - общая статистика

### 🔮 Предиктивная аналитика
- **Прогноз цен** - на неделю и месяц
- **Прогноз пользователей** - рост аудитории
- **Прогноз доходов** - финансовые предсказания
- **Уровень доверия** - точность прогнозов
- **Тренды** - направление изменений

## Фильтры и параметры

### Временные фильтры
```python
{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "period": "30d"  # 1d, 7d, 30d, 90d
}
```

### Фильтры данных
```python
{
    "marketplace": "wildberries",
    "category": "electronics",
    "user_id": "user_123",
    "group_id": "group_456",
    "price_min": 100.0,
    "price_max": 1000.0,
    "brand": "Apple",
    "rating_min": 4.0,
    "rating_max": 5.0
}
```

## Форматы экспорта

### 📄 PDF
- **Структурированные отчеты** с графиками
- **Профессиональное оформление**
- **Векторная графика** для масштабирования
- **Печатная версия** оптимизирована

### 📊 Excel
- **Множественные листы** для разных данных
- **Интерактивные таблицы** с фильтрами
- **Графики и диаграммы** встроенные
- **Формулы и вычисления** автоматические

### 📋 CSV
- **Сырые данные** для анализа
- **Совместимость** с любыми системами
- **Быстрая загрузка** больших объемов
- **Простота обработки** программно

### 📱 JSON
- **Структурированные данные** для API
- **Метаданные** и контекст
- **Вложенные объекты** для сложных данных
- **Читаемость** для разработчиков

## Планировщик отчетов

### Расписания
- **Ежедневно** - каждый день в указанное время
- **Еженедельно** - по понедельникам
- **Ежемесячно** - первого числа каждого месяца
- **Произвольное** - настраиваемое расписание

### Шаблоны отчетов
```json
{
    "id": "price_analysis",
    "name": "Анализ цен",
    "description": "Еженедельный отчет по анализу цен и трендов",
    "category": "pricing",
    "default_schedule": "weekly",
    "default_time": "09:00",
    "parameters": ["start_date", "end_date", "marketplace", "category"]
}
```

### Email уведомления
- **SMTP интеграция** - отправка через почтовые серверы
- **HTML форматирование** - красивые письма
- **Вложения** - отчеты в файлах
- **Персонализация** - индивидуальные сообщения

## Использование

### Python API
```python
from app.services.advanced_analytics_service import AdvancedAnalyticsService, AnalyticsFilter

# Создание сервиса
service = AdvancedAnalyticsService(db)

# Настройка фильтров
filter_params = AnalyticsFilter(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    marketplace="wildberries",
    category="electronics"
)

# Получение аналитики
overview = service.get_overview_metrics(filter_params)
price_analytics = service.get_price_analytics(filter_params)
user_analytics = service.get_user_analytics(filter_params)

# Экспорт данных
report_data = service.export_data(
    ReportType.PRICE_ANALYSIS,
    filter_params,
    ExportFormat.PDF
)
```

### HTTP запросы
```bash
# Получение обзорной аналитики
curl -X GET "http://localhost:8000/api/v1/advanced-analytics/overview?start_date=2024-01-01&end_date=2024-01-31"

# Анализ цен
curl -X GET "http://localhost:8000/api/v1/advanced-analytics/price-analysis?marketplace=wildberries&category=electronics"

# Экспорт отчета
curl -X GET "http://localhost:8000/api/v1/advanced-analytics/export/price_analysis?format=pdf&start_date=2024-01-01"

# Создание расписания
curl -X POST "http://localhost:8000/api/v1/report-scheduler/schedules?user_id=user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "price_analysis",
    "schedule_type": "weekly",
    "time": "09:00",
    "email": "user@example.com",
    "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
    "export_format": "pdf"
  }'
```

## Дашборд

### Основные вкладки
- **📈 Обзор** - ключевые метрики и тренды
- **💰 Цены** - детальный анализ цен
- **👥 Пользователи** - аналитика пользователей
- **📱 Социальные** - социальная активность
- **🔮 Прогнозы** - предиктивная аналитика

### Интерактивные элементы
- **Фильтры** - настройка параметров анализа
- **Графики** - интерактивные диаграммы
- **Таблицы** - детальные данные
- **Экспорт** - скачивание отчетов
- **Обновление** - актуализация данных

### Планировщик отчетов
- **📊 Мои расписания** - управление отчетами
- **➕ Создать расписание** - настройка новых отчетов
- **📋 Шаблоны** - готовые конфигурации
- **📈 Статистика** - аналитика планировщика

## Конфигурация

### Настройки аналитики
```python
ANALYTICS = {
    "cache_ttl": 3600,  # TTL кэша в секундах
    "max_data_points": 10000,  # Максимум точек данных
    "forecast_days": 30,  # Дней для прогноза
    "confidence_threshold": 0.7,  # Порог доверия
    "export_max_size": 100 * 1024 * 1024  # 100MB
}
```

### Настройки планировщика
```python
SCHEDULER = {
    "check_interval": 60,  # Интервал проверки (сек)
    "max_concurrent": 5,  # Максимум одновременных задач
    "retry_attempts": 3,  # Попытки повтора
    "retry_delay": 300,  # Задержка между попытками (сек)
    "cleanup_days": 30  # Дни хранения истории
}
```

### SMTP настройки
```python
SMTP = {
    "server": "smtp.gmail.com",
    "port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "use_tls": True
}
```

## Производительность

### Оптимизации
- **Кэширование** - Redis для быстрого доступа
- **Пагинация** - обработка больших данных
- **Индексы** - оптимизация запросов к БД
- **Асинхронность** - неблокирующие операции
- **Сжатие** - уменьшение размера данных

### Мониторинг
- **Метрики производительности** - время ответа, пропускная способность
- **Использование ресурсов** - CPU, память, диск
- **Ошибки** - логирование и алерты
- **Качество данных** - валидация и проверки

## Безопасность

### Контроль доступа
- **Аутентификация** - проверка пользователей
- **Авторизация** - права доступа к данным
- **Шифрование** - защита чувствительных данных
- **Аудит** - логирование действий

### Защита данных
- **Анонимизация** - удаление персональных данных
- **Маскирование** - скрытие чувствительной информации
- **Ограничения** - лимиты на экспорт
- **Валидация** - проверка входных данных

## Развертывание

### Требования
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- SMTP сервер

### Установка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка базы данных
alembic upgrade head

# Запуск планировщика
python -m app.services.report_scheduler_service
```

### Docker
```bash
# Запуск с планировщиком
docker-compose up -d

# Проверка статуса
docker-compose ps
```

## Мониторинг и логирование

### Логи
```python
import logging

logger = logging.getLogger("analytics")
logger.info(f"Generated report for user {user_id}")
logger.error(f"Failed to export data: {error}")
```

### Метрики
- Количество сгенерированных отчетов
- Время выполнения запросов
- Использование кэша
- Ошибки экспорта

## Поддержка

Для вопросов и предложений по расширенной аналитике создайте issue в репозитории или обратитесь к документации API.

## Лицензия

MIT License - см. файл LICENSE для деталей.
