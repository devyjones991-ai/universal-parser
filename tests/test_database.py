"""
Тесты для модуля базы данных
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import (
    Base, User, TrackedItem, Alert, PriceHistory,
    get_or_create_user, add_tracked_item, create_alert,
    get_user_tracked_items, get_user_alerts, get_user_stats,
    update_tracked_item_price, get_price_history
)


@pytest.fixture
def test_db():
    """Создание тестовой базы данных в памяти"""
    # Создаем временную базу данных в памяти
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def test_user(test_db):
    """Создание тестового пользователя"""
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestUserManagement:
    """Тесты управления пользователями"""
    
    def test_get_or_create_user_new(self, test_db):
        """Тест создания нового пользователя"""
        user = get_or_create_user(
            telegram_id=987654321,
            username="new_user",
            first_name="New",
            last_name="User"
        )
        
        assert user.telegram_id == 987654321
        assert user.username == "new_user"
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.subscription_tier == "free"
        assert user.is_active is True
    
    def test_get_or_create_user_existing(self, test_user):
        """Тест получения существующего пользователя"""
        user = get_or_create_user(
            telegram_id=test_user.telegram_id,
            username="updated_username",
            first_name="Updated",
            last_name="Name"
        )
        
        assert user.id == test_user.id
        assert user.username == "updated_username"
        assert user.first_name == "Updated"
        assert user.last_name == "Name"


class TestTrackedItems:
    """Тесты отслеживаемых товаров"""
    
    def test_add_tracked_item(self, test_user):
        """Тест добавления товара для отслеживания"""
        item = add_tracked_item(
            user_id=test_user.id,
            item_id="12345",
            marketplace="wb",
            name="Test Product",
            url="https://example.com/product/12345"
        )
        
        assert item.user_id == test_user.id
        assert item.item_id == "12345"
        assert item.marketplace == "wb"
        assert item.name == "Test Product"
        assert item.url == "https://example.com/product/12345"
        assert item.is_active is True
    
    def test_get_user_tracked_items(self, test_user):
        """Тест получения отслеживаемых товаров пользователя"""
        # Добавляем несколько товаров
        add_tracked_item(test_user.id, "1", "wb", "Product 1")
        add_tracked_item(test_user.id, "2", "ozon", "Product 2")
        add_tracked_item(test_user.id, "3", "yandex", "Product 3")
        
        items = get_user_tracked_items(test_user.id)
        
        assert len(items) == 3
        assert all(item.user_id == test_user.id for item in items)
        assert all(item.is_active is True for item in items)
    
    def test_update_tracked_item_price(self, test_user):
        """Тест обновления цены товара"""
        item = add_tracked_item(
            test_user.id, "12345", "wb", "Test Product"
        )
        
        # Обновляем цену
        update_tracked_item_price(
            item.id, 
            price=1000.0, 
            stock=5, 
            rating=4.5
        )
        
        # Проверяем, что цена обновилась
        assert item.current_price == 1000.0
        assert item.current_stock == 5
        assert item.current_rating == 4.5
        
        # Проверяем, что создалась запись в истории
        history = get_price_history(test_user.id, item.id)
        assert len(history) == 1
        assert history[0].price == 1000.0
        assert history[0].stock == 5
        assert history[0].rating == 4.5


class TestAlerts:
    """Тесты системы алертов"""
    
    def test_create_alert(self, test_user):
        """Тест создания алерта"""
        alert = create_alert(
            user_id=test_user.id,
            alert_type="price_drop",
            conditions={"min_drop_percent": 10}
        )
        
        assert alert.user_id == test_user.id
        assert alert.alert_type == "price_drop"
        assert alert.conditions == {"min_drop_percent": 10}
        assert alert.is_active is True
        assert alert.trigger_count == 0
    
    def test_get_user_alerts(self, test_user):
        """Тест получения алертов пользователя"""
        # Создаем несколько алертов
        create_alert(test_user.id, "price_drop", {"min_drop_percent": 10})
        create_alert(test_user.id, "price_rise", {"min_rise_percent": 15})
        create_alert(test_user.id, "stock_change", {"low_stock_threshold": 5})
        
        alerts = get_user_alerts(test_user.id)
        
        assert len(alerts) == 3
        assert all(alert.user_id == test_user.id for alert in alerts)
        assert all(alert.is_active is True for alert in alerts)


class TestUserStats:
    """Тесты статистики пользователя"""
    
    def test_get_user_stats(self, test_user):
        """Тест получения статистики пользователя"""
        # Добавляем товары и алерты
        add_tracked_item(test_user.id, "1", "wb", "Product 1")
        add_tracked_item(test_user.id, "2", "ozon", "Product 2")
        create_alert(test_user.id, "price_drop", {"min_drop_percent": 10})
        
        stats = get_user_stats(test_user.id)
        
        assert stats["user_id"] == test_user.id
        assert stats["subscription_tier"] == "free"
        assert stats["tracked_items_count"] == 2
        assert stats["alerts_count"] == 1
        assert "created_at" in stats
        assert "last_activity" in stats


class TestPriceHistory:
    """Тесты истории цен"""
    
    def test_get_price_history(self, test_user):
        """Тест получения истории цен"""
        item = add_tracked_item(
            test_user.id, "12345", "wb", "Test Product"
        )
        
        # Добавляем несколько записей в историю
        for i in range(5):
            update_tracked_item_price(
                item.id, 
                price=1000.0 - i * 100, 
                stock=10 - i, 
                rating=4.5
            )
        
        history = get_price_history(test_user.id, item.id, days=30)
        
        assert len(history) == 5
        assert all(ph.user_id == test_user.id for ph in history)
        assert all(ph.tracked_item_id == item.id for ph in history)
        
        # Проверяем, что записи отсортированы по времени (новые первые)
        prices = [ph.price for ph in history]
        assert prices == [600.0, 700.0, 800.0, 900.0, 1000.0]
