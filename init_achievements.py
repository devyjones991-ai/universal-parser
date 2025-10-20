"""Скрипт для инициализации достижений в базе данных"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.social import Achievement
from datetime import datetime

async def init_achievements():
    """Инициализирует достижения в базе данных"""
    engine = create_async_engine(settings.async_database_url, echo=True)
    AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

    async with AsyncSessionLocal() as session:
        # Определяем достижения
        achievements_data = [
            # Парсинг достижения
            {
                "name": "Первый парсинг",
                "description": "Выполните первый парсинг товара",
                "icon_url": "https://via.placeholder.com/64x64/4CAF50/ffffff?text=1",
                "category": "parsing",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 1,
                "condition_data": {"action": "parse_item"},
                "points_reward": 100,
                "badge_reward": "first_parser",
                "is_hidden": False
            },
            {
                "name": "Парсер-новичок",
                "description": "Выполните 10 парсингов товаров",
                "icon_url": "https://via.placeholder.com/64x64/2196F3/ffffff?text=10",
                "category": "parsing",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 10,
                "condition_data": {"action": "parse_item"},
                "points_reward": 500,
                "badge_reward": "parsing_rookie",
                "is_hidden": False
            },
            {
                "name": "Парсер-эксперт",
                "description": "Выполните 100 парсингов товаров",
                "icon_url": "https://via.placeholder.com/64x64/FF9800/ffffff?text=100",
                "category": "parsing",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 100,
                "condition_data": {"action": "parse_item"},
                "points_reward": 2000,
                "badge_reward": "parsing_expert",
                "is_hidden": False
            },
            {
                "name": "Парсер-мастер",
                "description": "Выполните 1000 парсингов товаров",
                "icon_url": "https://via.placeholder.com/64x64/9C27B0/ffffff?text=1K",
                "category": "parsing",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 1000,
                "condition_data": {"action": "parse_item"},
                "points_reward": 10000,
                "badge_reward": "parsing_master",
                "is_hidden": False
            },
            
            # Социальные достижения
            {
                "name": "Первый пост",
                "description": "Создайте первый социальный пост",
                "icon_url": "https://via.placeholder.com/64x64/4CAF50/ffffff?text=📝",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 1,
                "condition_data": {"action": "create_post"},
                "points_reward": 50,
                "badge_reward": "first_post",
                "is_hidden": False
            },
            {
                "name": "Активный пользователь",
                "description": "Создайте 50 социальных постов",
                "icon_url": "https://via.placeholder.com/64x64/2196F3/ffffff?text=50",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 50,
                "condition_data": {"action": "create_post"},
                "points_reward": 1000,
                "badge_reward": "active_user",
                "is_hidden": False
            },
            {
                "name": "Популярный автор",
                "description": "Получите 100 лайков на посты",
                "icon_url": "https://via.placeholder.com/64x64/FF9800/ffffff?text=❤️",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 100,
                "condition_data": {"action": "receive_like"},
                "points_reward": 1500,
                "badge_reward": "popular_author",
                "is_hidden": False
            },
            {
                "name": "Комментатор",
                "description": "Оставьте 100 комментариев",
                "icon_url": "https://via.placeholder.com/64x64/607D8B/ffffff?text=💬",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 100,
                "condition_data": {"action": "create_comment"},
                "points_reward": 800,
                "badge_reward": "commentator",
                "is_hidden": False
            },
            
            # Торговые достижения
            {
                "name": "Первый трейдер",
                "description": "Отследите первый товар",
                "icon_url": "https://via.placeholder.com/64x64/4CAF50/ffffff?text=📈",
                "category": "trading",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 1,
                "condition_data": {"action": "track_item"},
                "points_reward": 200,
                "badge_reward": "first_trader",
                "is_hidden": False
            },
            {
                "name": "Опытный трейдер",
                "description": "Отследите 25 товаров",
                "icon_url": "https://via.placeholder.com/64x64/2196F3/ffffff?text=25",
                "category": "trading",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 25,
                "condition_data": {"action": "track_item"},
                "points_reward": 1000,
                "badge_reward": "experienced_trader",
                "is_hidden": False
            },
            {
                "name": "Мастер трейдинга",
                "description": "Отследите 100 товаров",
                "icon_url": "https://via.placeholder.com/64x64/FF9800/ffffff?text=100",
                "category": "trading",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 100,
                "condition_data": {"action": "track_item"},
                "points_reward": 5000,
                "badge_reward": "trading_master",
                "is_hidden": False
            },
            
            # Специальные достижения
            {
                "name": "Ранняя пташка",
                "description": "Войдите в систему 7 дней подряд",
                "icon_url": "https://via.placeholder.com/64x64/4CAF50/ffffff?text=7",
                "category": "special",
                "type": "streak",
                "condition_type": "streak",
                "condition_value": 7,
                "condition_data": {"action": "daily_login"},
                "points_reward": 500,
                "badge_reward": "early_bird",
                "is_hidden": False
            },
            {
                "name": "Недельный марафон",
                "description": "Войдите в систему 30 дней подряд",
                "icon_url": "https://via.placeholder.com/64x64/9C27B0/ffffff?text=30",
                "category": "special",
                "type": "streak",
                "condition_type": "streak",
                "condition_value": 30,
                "condition_data": {"action": "daily_login"},
                "points_reward": 2000,
                "badge_reward": "weekly_marathon",
                "is_hidden": False
            },
            {
                "name": "Социальная бабочка",
                "description": "Добавьте 10 друзей",
                "icon_url": "https://via.placeholder.com/64x64/FF9800/ffffff?text=👥",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 10,
                "condition_data": {"action": "add_friend"},
                "points_reward": 1000,
                "badge_reward": "social_butterfly",
                "is_hidden": False
            },
            {
                "name": "Лидер мнений",
                "description": "Получите 500 лайков на посты",
                "icon_url": "https://via.placeholder.com/64x64/9C27B0/ffffff?text=👑",
                "category": "social",
                "type": "milestone",
                "condition_type": "count",
                "condition_value": 500,
                "condition_data": {"action": "receive_like"},
                "points_reward": 5000,
                "badge_reward": "opinion_leader",
                "is_hidden": False
            },
            {
                "name": "Скрытое достижение",
                "description": "Найдите скрытое достижение!",
                "icon_url": "https://via.placeholder.com/64x64/000000/ffffff?text=?",
                "category": "special",
                "type": "hidden",
                "condition_type": "count",
                "condition_value": 1,
                "condition_data": {"action": "find_hidden"},
                "points_reward": 10000,
                "badge_reward": "hidden_achievement",
                "is_hidden": True
            }
        ]

        for achievement_data in achievements_data:
            # Проверяем, существует ли уже такое достижение
            existing = await session.execute(
                session.query(Achievement).filter_by(name=achievement_data["name"])
            )
            if not existing.scalar_one_or_none():
                achievement = Achievement(**achievement_data)
                session.add(achievement)
                print(f"Создано достижение: {achievement.name}")
            else:
                print(f"Достижение '{achievement_data['name']}' уже существует")

        await session.commit()
        print("✅ Все достижения инициализированы!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_achievements())


