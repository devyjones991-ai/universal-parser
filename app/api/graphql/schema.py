"""GraphQL схема для Universal Parser"""

import graphene
from graphene import ObjectType, String, Int, Float, Boolean, List, Field, ID, DateTime
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.item import TrackedItem
from app.models.user import User
from app.models.item import PriceHistory
from app.models.social import SocialPost, UserProfile
from app.core.database import get_db


class ItemType(SQLAlchemyObjectType):
    """GraphQL тип для товара"""
    class Meta:
        model = Item
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
    
    # Дополнительные поля
    current_price = Float()
    price_change_percent = Float()
    marketplace_display_name = String()
    category_display_name = String()
    
    def resolve_current_price(self, info):
        """Получить текущую цену товара"""
        # В реальном приложении здесь был бы запрос к БД
        return self.price if hasattr(self, 'price') else 0.0
    
    def resolve_price_change_percent(self, info):
        """Получить изменение цены в процентах"""
        # В реальном приложении здесь был бы расчет изменения цены
        return 0.0
    
    def resolve_marketplace_display_name(self, info):
        """Получить отображаемое название маркетплейса"""
        marketplace_names = {
            "wildberries": "Wildberries",
            "ozon": "Ozon",
            "yandex_market": "Яндекс.Маркет",
            "avito": "Avito",
            "aliexpress": "AliExpress",
            "amazon": "Amazon",
            "ebay": "eBay"
        }
        return marketplace_names.get(self.marketplace, self.marketplace)
    
    def resolve_category_display_name(self, info):
        """Получить отображаемое название категории"""
        return self.category or "Без категории"


class UserType(SQLAlchemyObjectType):
    """GraphQL тип для пользователя"""
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
    
    # Дополнительные поля
    profile = Field(lambda: UserProfileType)
    items_count = Int()
    posts_count = Int()
    
    def resolve_profile(self, info):
        """Получить профиль пользователя"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_items_count(self, info):
        """Получить количество товаров пользователя"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_posts_count(self, info):
        """Получить количество постов пользователя"""
        # В реальном приложении здесь был бы запрос к БД
        return 0


class UserProfileType(SQLAlchemyObjectType):
    """GraphQL тип для профиля пользователя"""
    class Meta:
        model = UserProfile
        interfaces = (graphene.relay.Node,)
        fields = "__all__"


class PriceHistoryType(SQLAlchemyObjectType):
    """GraphQL тип для истории цен"""
    class Meta:
        model = PriceHistory
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
    
    # Дополнительные поля
    item = Field(ItemType)
    price_change = Float()
    formatted_price = String()
    
    def resolve_item(self, info):
        """Получить товар"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_price_change(self, info):
        """Получить изменение цены"""
        # В реальном приложении здесь был бы расчет изменения цены
        return 0.0
    
    def resolve_formatted_price(self, info):
        """Получить отформатированную цену"""
        return f"{self.price:.2f} ₽"


class SocialPostType(SQLAlchemyObjectType):
    """GraphQL тип для социального поста"""
    class Meta:
        model = SocialPost
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
    
    # Дополнительные поля
    author = Field(UserType)
    likes_count = Int()
    comments_count = Int()
    time_ago = String()
    
    def resolve_author(self, info):
        """Получить автора поста"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_likes_count(self, info):
        """Получить количество лайков"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_comments_count(self, info):
        """Получить количество комментариев"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_time_ago(self, info):
        """Получить время назад"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            if delta.days > 0:
                return f"{delta.days} дней назад"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600} часов назад"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60} минут назад"
            else:
                return "Только что"
        return "Неизвестно"


class ItemConnection(graphene.relay.Connection):
    """Соединение для товаров"""
    class Meta:
        node = ItemType


class UserConnection(graphene.relay.Connection):
    """Соединение для пользователей"""
    class Meta:
        node = UserType


class SocialPostConnection(graphene.relay.Connection):
    """Соединение для социальных постов"""
    class Meta:
        node = SocialPostType


class Query(ObjectType):
    """Основной GraphQL запрос"""
    
    # Товары
    items = SQLAlchemyConnectionField(ItemConnection)
    item = Field(ItemType, id=ID(required=True))
    items_by_marketplace = List(ItemType, marketplace=String(required=True))
    items_by_category = List(ItemType, category=String(required=True))
    search_items = List(ItemType, query=String(required=True))
    
    # Пользователи
    users = SQLAlchemyConnectionField(UserConnection)
    user = Field(UserType, id=ID(required=True))
    user_by_username = Field(UserType, username=String(required=True))
    
    # Социальные посты
    social_posts = SQLAlchemyConnectionField(SocialPostConnection)
    social_post = Field(SocialPostType, id=ID(required=True))
    user_posts = List(SocialPostType, user_id=ID(required=True))
    
    # История цен
    price_history = List(PriceHistoryType, item_id=ID(required=True))
    price_trends = List(PriceHistoryType, 
                       marketplace=String(), 
                       category=String(),
                       days=Int(default_value=30))
    
    # Аналитика
    analytics_overview = Field(lambda: AnalyticsOverviewType)
    marketplace_stats = List(lambda: MarketplaceStatsType)
    category_stats = List(lambda: CategoryStatsType)
    
    def resolve_item(self, info, id):
        """Получить товар по ID"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_items_by_marketplace(self, info, marketplace):
        """Получить товары по маркетплейсу"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_items_by_category(self, info, category):
        """Получить товары по категории"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_search_items(self, info, query):
        """Поиск товаров"""
        # В реальном приложении здесь был бы поиск по БД
        return []
    
    def resolve_user(self, info, id):
        """Получить пользователя по ID"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_user_by_username(self, info, username):
        """Получить пользователя по имени"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_social_post(self, info, id):
        """Получить социальный пост по ID"""
        # В реальном приложении здесь был бы запрос к БД
        return None
    
    def resolve_user_posts(self, info, user_id):
        """Получить посты пользователя"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_price_history(self, info, item_id):
        """Получить историю цен товара"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_price_trends(self, info, marketplace=None, category=None, days=30):
        """Получить тренды цен"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_analytics_overview(self, info):
        """Получить обзор аналитики"""
        return AnalyticsOverviewType()
    
    def resolve_marketplace_stats(self, info):
        """Получить статистику по маркетплейсам"""
        # В реальном приложении здесь был бы запрос к БД
        return []
    
    def resolve_category_stats(self, info):
        """Получить статистику по категориям"""
        # В реальном приложении здесь был бы запрос к БД
        return []


class AnalyticsOverviewType(ObjectType):
    """Тип для обзора аналитики"""
    total_items = Int()
    total_users = Int()
    total_posts = Int()
    total_revenue = Float()
    active_users = Int()
    price_changes_today = Int()
    new_items_today = Int()
    top_marketplace = String()
    top_category = String()
    
    def resolve_total_items(self, info):
        """Получить общее количество товаров"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_total_users(self, info):
        """Получить общее количество пользователей"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_total_posts(self, info):
        """Получить общее количество постов"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_total_revenue(self, info):
        """Получить общий доход"""
        # В реальном приложении здесь был бы запрос к БД
        return 0.0
    
    def resolve_active_users(self, info):
        """Получить количество активных пользователей"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_price_changes_today(self, info):
        """Получить количество изменений цен сегодня"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_new_items_today(self, info):
        """Получить количество новых товаров сегодня"""
        # В реальном приложении здесь был бы запрос к БД
        return 0
    
    def resolve_top_marketplace(self, info):
        """Получить топ маркетплейс"""
        # В реальном приложении здесь был бы запрос к БД
        return "Wildberries"
    
    def resolve_top_category(self, info):
        """Получить топ категорию"""
        # В реальном приложении здесь был бы запрос к БД
        return "Электроника"


class MarketplaceStatsType(ObjectType):
    """Тип для статистики маркетплейса"""
    marketplace = String()
    items_count = Int()
    average_price = Float()
    price_changes = Int()
    new_items = Int()
    top_category = String()
    
    def resolve_marketplace(self, info):
        """Получить название маркетплейса"""
        return "Wildberries"
    
    def resolve_items_count(self, info):
        """Получить количество товаров"""
        return 0
    
    def resolve_average_price(self, info):
        """Получить среднюю цену"""
        return 0.0
    
    def resolve_price_changes(self, info):
        """Получить количество изменений цен"""
        return 0
    
    def resolve_new_items(self, info):
        """Получить количество новых товаров"""
        return 0
    
    def resolve_top_category(self, info):
        """Получить топ категорию"""
        return "Электроника"


class CategoryStatsType(ObjectType):
    """Тип для статистики категории"""
    category = String()
    items_count = Int()
    average_price = Float()
    price_changes = Int()
    new_items = Int()
    top_marketplace = String()
    
    def resolve_category(self, info):
        """Получить название категории"""
        return "Электроника"
    
    def resolve_items_count(self, info):
        """Получить количество товаров"""
        return 0
    
    def resolve_average_price(self, info):
        """Получить среднюю цену"""
        return 0.0
    
    def resolve_price_changes(self, info):
        """Получить количество изменений цен"""
        return 0
    
    def resolve_new_items(self, info):
        """Получить количество новых товаров"""
        return 0
    
    def resolve_top_marketplace(self, info):
        """Получить топ маркетплейс"""
        return "Wildberries"


class CreateItemInput(graphene.InputObjectType):
    """Входные данные для создания товара"""
    name = String(required=True)
    marketplace = String(required=True)
    category = String()
    price = Float()
    url = String()
    description = String()
    image_url = String()


class UpdateItemInput(graphene.InputObjectType):
    """Входные данные для обновления товара"""
    name = String()
    category = String()
    price = Float()
    description = String()
    image_url = String()


class CreateSocialPostInput(graphene.InputObjectType):
    """Входные данные для создания социального поста"""
    content = String(required=True)
    author_id = ID(required=True)
    item_id = ID()
    media_urls = List(String)


class Mutation(ObjectType):
    """GraphQL мутации"""
    
    # Товары
    create_item = Field(ItemType, input=CreateItemInput(required=True))
    update_item = Field(ItemType, id=ID(required=True), input=UpdateItemInput(required=True))
    delete_item = Field(Boolean, id=ID(required=True))
    
    # Социальные посты
    create_social_post = Field(SocialPostType, input=CreateSocialPostInput(required=True))
    like_post = Field(Boolean, id=ID(required=True))
    unlike_post = Field(Boolean, id=ID(required=True))
    
    def resolve_create_item(self, info, input):
        """Создать товар"""
        # В реальном приложении здесь была бы логика создания товара
        return None
    
    def resolve_update_item(self, info, id, input):
        """Обновить товар"""
        # В реальном приложении здесь была бы логика обновления товара
        return None
    
    def resolve_delete_item(self, info, id):
        """Удалить товар"""
        # В реальном приложении здесь была бы логика удаления товара
        return True
    
    def resolve_create_social_post(self, info, input):
        """Создать социальный пост"""
        # В реальном приложении здесь была бы логика создания поста
        return None
    
    def resolve_like_post(self, info, id):
        """Лайкнуть пост"""
        # В реальном приложении здесь была бы логика лайка
        return True
    
    def resolve_unlike_post(self, info, id):
        """Убрать лайк с поста"""
        # В реальном приложении здесь была бы логика убирания лайка
        return True


class Subscription(ObjectType):
    """GraphQL подписки"""
    
    # Подписки на изменения
    item_updated = Field(ItemType, item_id=ID(required=True))
    price_changed = Field(PriceHistoryType, item_id=ID(required=True))
    new_social_post = Field(SocialPostType, user_id=ID())
    
    def resolve_item_updated(self, info, item_id):
        """Подписка на обновления товара"""
        # В реальном приложении здесь была бы подписка на WebSocket
        return None
    
    def resolve_price_changed(self, info, item_id):
        """Подписка на изменения цены"""
        # В реальном приложении здесь была бы подписка на WebSocket
        return None
    
    def resolve_new_social_post(self, info, user_id=None):
        """Подписка на новые социальные посты"""
        # В реальном приложении здесь была бы подписка на WebSocket
        return None


# Создаем схему
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    types=[ItemType, UserType, UserProfileType, PriceHistoryType, SocialPostType]
)


