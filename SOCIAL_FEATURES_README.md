# 👥 Социальные функции и геймификация - Universal Parser

## Обзор

Модуль социальных функций и геймификации добавляет интерактивные возможности для пользователей, включая профили, группы, достижения, социальные посты, чат и систему рейтингов.

## Основные функции

### 👤 Профили пользователей
- **Расширенные профили** с аватарами, биографией и настройками приватности
- **Система уровней** с очками опыта и репутацией
- **Статистика активности** (посты, комментарии, лайки, друзья)
- **Настройки приватности** для контроля видимости информации

### 👥 Социальные связи
- **Система друзей** с запросами и подтверждениями
- **Подписки** на других пользователей
- **Группы и сообщества** по интересам
- **Роли в группах** (участник, модератор, администратор)

### 📱 Социальные посты
- **Создание постов** с текстом, изображениями и видео
- **Связывание с товарами** из отслеживаемых маркетплейсов
- **Комментарии и ответы** на посты
- **Система лайков** с различными типами реакций
- **Социальная лента** с персональными рекомендациями

### 🏆 Геймификация
- **Система достижений** с различными категориями
- **Очки опыта** и повышение уровней
- **Лидерборды** по различным категориям
- **Бейджи и награды** за активность
- **Скрытые достижения** для дополнительной мотивации

### 💬 Коммуникация
- **Личные сообщения** между пользователями
- **Уведомления** о социальной активности
- **Чат в группах** для обсуждений
- **Медиа-сообщения** с изображениями и файлами

## API Эндпоинты

### Профили пользователей
```http
POST /api/v1/social/profiles
GET /api/v1/social/profiles/{user_id}
PUT /api/v1/social/profiles/{user_id}
GET /api/v1/social/profiles/{user_id}/stats
```

### Группы
```http
POST /api/v1/social/groups
GET /api/v1/social/groups/{group_id}
POST /api/v1/social/groups/{group_id}/join
DELETE /api/v1/social/groups/{group_id}/leave
```

### Социальные посты
```http
POST /api/v1/social/posts
GET /api/v1/social/feed
GET /api/v1/social/posts/{post_id}
PUT /api/v1/social/posts/{post_id}
DELETE /api/v1/social/posts/{post_id}
```

### Комментарии
```http
POST /api/v1/social/comments
GET /api/v1/social/posts/{post_id}/comments
```

### Лайки
```http
POST /api/v1/social/likes
```

### Лидерборды
```http
POST /api/v1/social/leaderboards
GET /api/v1/social/leaderboards/{leaderboard_id}
POST /api/v1/social/leaderboards/{leaderboard_id}/update
```

### Уведомления
```http
GET /api/v1/social/notifications
PUT /api/v1/social/notifications/{notification_id}/read
```

### Геймификация
```http
GET /api/v1/social/gamification/points
GET /api/v1/social/achievements
GET /api/v1/social/users/{user_id}/achievements
```

## Модели данных

### UserProfile
```python
class UserProfile:
    id: UUID
    user_id: UUID
    display_name: str
    bio: str
    avatar_url: str
    level: int
    experience_points: int
    total_points: int
    reputation: int
    # ... настройки приватности
```

### Group
```python
class Group:
    id: UUID
    name: str
    description: str
    owner_id: UUID
    is_public: bool
    member_count: int
    # ... настройки группы
```

### SocialPost
```python
class SocialPost:
    id: UUID
    author_id: UUID
    content: str
    post_type: str
    item_id: UUID  # Связь с товаром
    marketplace: str
    like_count: int
    comment_count: int
    # ... статистика
```

### Achievement
```python
class Achievement:
    id: UUID
    name: str
    description: str
    category: str  # parsing, social, trading, special
    type: str      # milestone, streak, hidden
    condition_type: str
    condition_value: int
    points_reward: int
    badge_reward: str
    is_hidden: bool
```

## Система достижений

### Категории достижений
- **Парсинг** - за активность в парсинге товаров
- **Социальные** - за социальную активность
- **Торговля** - за отслеживание товаров
- **Специальные** - за особые действия

### Типы достижений
- **Milestone** - достижение определенного количества действий
- **Streak** - выполнение действий подряд
- **Hidden** - скрытые достижения для исследования

### Примеры достижений
- 🎯 **Первый парсинг** - выполните первый парсинг товара (100 очков)
- 📝 **Первый пост** - создайте первый социальный пост (50 очков)
- 👥 **Социальная бабочка** - добавьте 10 друзей (1000 очков)
- 👑 **Лидер мнений** - получите 500 лайков (5000 очков)
- 🔒 **Скрытое достижение** - найдите скрытое достижение (10000 очков)

## Система уровней

### Формула расчета
- **Необходимый опыт для уровня N:** N × 1000 очков
- **Повышение уровня:** автоматически при достижении необходимого опыта
- **Очки опыта:** начисляются за выполнение действий

### Бонусы уровней
- **Доступ к премиум функциям**
- **Увеличенные лимиты**
- **Эксклюзивные достижения**
- **Приоритетная поддержка**

## Лидерборды

### Категории лидербордов
- **Парсинг товаров** - по количеству парсингов
- **Социальная активность** - по постам и комментариям
- **Торговля** - по отслеживаемым товарам
- **Общий рейтинг** - по общим очкам

### Периоды
- **Ежедневный** - обновляется каждый день
- **Еженедельный** - обновляется каждую неделю
- **Ежемесячный** - обновляется каждый месяц
- **За все время** - постоянный рейтинг

## Дашборд

### Функции дашборда
- **Просмотр профиля** с полной статистикой
- **Социальная лента** с постами друзей
- **Достижения** с прогрессом выполнения
- **Лидерборды** с рейтингами пользователей
- **Уведомления** о социальной активности

### Графики и аналитика
- **График активности** по дням
- **Распределение достижений** по категориям
- **Прогресс уровня** с визуализацией
- **Статистика социальной активности**

## Использование

### Python
```python
from app.services.social_service import SocialService

# Создание сервиса
service = SocialService(db)

# Создание профиля
profile = service.create_user_profile(UserProfileCreate(
    user_id="user_123",
    display_name="Иван Иванов",
    bio="Люблю парсить товары!"
))

# Создание поста
post = service.create_post(SocialPostCreate(
    content="Нашел отличную скидку на iPhone!",
    post_type="text",
    item_id="item_456"
), "user_123")

# Проверка достижений
achievements = service.check_achievements(
    "user_123", 
    "social", 
    {"posts_count": 1}
)
```

### HTTP запросы
```bash
# Создание профиля
curl -X POST "http://localhost:8000/api/v1/social/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "display_name": "Иван Иванов",
    "bio": "Люблю парсить товары!"
  }'

# Получение социальной ленты
curl -X GET "http://localhost:8000/api/v1/social/feed?user_id=user_123"

# Создание поста
curl -X POST "http://localhost:8000/api/v1/social/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Нашел отличную скидку!",
    "post_type": "text"
  }'
```

## Конфигурация

### Настройки геймификации
```python
GAMIFICATION = {
    "level_multiplier": 1000,  # Множитель для расчета уровня
    "achievement_check_interval": 300,  # Интервал проверки достижений (сек)
    "leaderboard_update_interval": 3600,  # Интервал обновления лидербордов (сек)
    "max_notifications": 100,  # Максимум уведомлений на пользователя
    "points_decay": False  # Уменьшение очков со временем
}
```

### Настройки социальных функций
```python
SOCIAL = {
    "max_posts_per_day": 50,
    "max_comments_per_post": 1000,
    "max_friends": 5000,
    "max_groups_per_user": 100,
    "max_group_members": 10000,
    "post_media_limit": 10,
    "message_media_limit": 5
}
```

## Безопасность

- **Валидация контента** для предотвращения спама
- **Модерация постов** с автоматическими фильтрами
- **Ограничения частоты** для предотвращения злоупотреблений
- **Приватность данных** с настройками видимости
- **Блокировка пользователей** при нарушении правил

## Производительность

- **Кэширование** социальных данных
- **Пагинация** для больших списков
- **Индексы** для быстрого поиска
- **Асинхронная обработка** уведомлений
- **Оптимизация запросов** к базе данных

## Мониторинг

### Метрики
- Количество активных пользователей
- Популярность постов и групп
- Выполнение достижений
- Активность в лидербордах

### Логирование
```python
import logging

logger = logging.getLogger("social")
logger.info(f"User {user_id} created post {post_id}")
logger.info(f"User {user_id} unlocked achievement {achievement_id}")
```

## Развертывание

### Миграции базы данных
```bash
# Применить миграции
alembic upgrade head

# Инициализировать достижения
python init_achievements.py
```

### Docker
```bash
# Запуск с социальными функциями
docker-compose up -d
```

## Поддержка

Для вопросов и предложений по социальным функциям создайте issue в репозитории или обратитесь к документации API.

## Лицензия

MIT License - см. файл LICENSE для деталей.


