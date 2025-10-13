"""
Тесты для системы алертов
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from alert_system import AlertChecker, MonitoringService, AlertNotificationService
from db import User, TrackedItem, Alert, PriceHistory


@pytest.fixture
def alert_checker():
    """Создание экземпляра AlertChecker"""
    return AlertChecker()


@pytest.fixture
def monitoring_service():
    """Создание экземпляра MonitoringService"""
    return MonitoringService()


@pytest.fixture
def mock_bot():
    """Создание мок-объекта бота"""
    return Mock()


@pytest.fixture
def notification_service(mock_bot):
    """Создание экземпляра AlertNotificationService"""
    return AlertNotificationService(mock_bot)


@pytest.fixture
def sample_alert():
    """Создание тестового алерта"""
    alert = Mock()
    alert.id = 1
    alert.alert_type = "price_drop"
    alert.conditions = {"min_drop_percent": 10}
    alert.user_id = 123
    return alert


@pytest.fixture
def sample_tracked_item():
    """Создание тестового товара"""
    item = Mock()
    item.id = 1
    item.user_id = 123
    item.item_id = "12345"
    item.marketplace = "wb"
    item.name = "Test Product"
    item.current_price = 1000.0
    item.current_stock = 10
    item.current_rating = 4.5
    return item


class TestAlertChecker:
    """Тесты класса AlertChecker"""
    
    def test_check_price_drop_alert_true(self, alert_checker, sample_alert):
        """Тест срабатывания алерта на падение цены"""
        result = alert_checker.check_price_drop_alert(
            sample_alert, 
            current_price=800.0, 
            previous_price=1000.0
        )
        assert result is True
    
    def test_check_price_drop_alert_false(self, alert_checker, sample_alert):
        """Тест несрабатывания алерта на падение цены"""
        result = alert_checker.check_price_drop_alert(
            sample_alert, 
            current_price=950.0, 
            previous_price=1000.0
        )
        assert result is False
    
    def test_check_price_drop_alert_no_previous_price(self, alert_checker, sample_alert):
        """Тест алерта без предыдущей цены"""
        result = alert_checker.check_price_drop_alert(
            sample_alert, 
            current_price=800.0, 
            previous_price=None
        )
        assert result is False
    
    def test_check_price_rise_alert_true(self, alert_checker):
        """Тест срабатывания алерта на рост цены"""
        alert = Mock()
        alert.conditions = {"min_rise_percent": 10}
        
        result = alert_checker.check_price_rise_alert(
            alert, 
            current_price=1200.0, 
            previous_price=1000.0
        )
        assert result is True
    
    def test_check_stock_change_alert_appeared(self, alert_checker):
        """Тест алерта на появление товара"""
        alert = Mock()
        alert.conditions = {"stock_appeared": True}
        
        result = alert_checker.check_stock_change_alert(
            alert, 
            current_stock=5, 
            previous_stock=0
        )
        assert result is True
    
    def test_check_stock_change_alert_disappeared(self, alert_checker):
        """Тест алерта на исчезновение товара"""
        alert = Mock()
        alert.conditions = {"stock_disappeared": True}
        
        result = alert_checker.check_stock_change_alert(
            alert, 
            current_stock=0, 
            previous_stock=5
        )
        assert result is True
    
    def test_check_stock_change_alert_low_stock(self, alert_checker):
        """Тест алерта на низкий остаток"""
        alert = Mock()
        alert.conditions = {"low_stock_threshold": 5}
        
        result = alert_checker.check_stock_change_alert(
            alert, 
            current_stock=3, 
            previous_stock=10
        )
        assert result is True
    
    def test_check_review_change_alert(self, alert_checker):
        """Тест алерта на изменение рейтинга"""
        alert = Mock()
        alert.conditions = {"min_rating_change": 0.5}
        
        result = alert_checker.check_review_change_alert(
            alert, 
            current_rating=3.0, 
            previous_rating=4.0
        )
        assert result is True


class TestMonitoringService:
    """Тесты класса MonitoringService"""
    
    @pytest.mark.asyncio
    async def test_check_user_alerts_no_alerts(self, monitoring_service):
        """Тест проверки алертов без алертов"""
        with patch('alert_system.get_user_alerts', return_value=[]):
            result = await monitoring_service.check_user_alerts(123)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_check_user_alerts_with_triggered_alert(self, monitoring_service, sample_alert):
        """Тест проверки алертов со сработавшим алертом"""
        with patch('alert_system.get_user_alerts', return_value=[sample_alert]), \
             patch.object(monitoring_service, '_check_alert', return_value=True), \
             patch('alert_system.trigger_alert'):
            
            result = await monitoring_service.check_user_alerts(123)
            
            assert len(result) == 1
            assert result[0]["alert_id"] == sample_alert.id
            assert result[0]["alert_type"] == "price_drop"
    
    @pytest.mark.asyncio
    async def test_update_all_tracked_items(self, monitoring_service, sample_tracked_item):
        """Тест обновления всех отслеживаемых товаров"""
        with patch('alert_system.get_user_tracked_items', return_value=[sample_tracked_item]), \
             patch.object(monitoring_service, '_get_item_current_data', return_value={
                 "price": 900.0, "stock": 8, "rating": 4.2
             }), \
             patch('alert_system.update_tracked_item_price'):
            
            result = await monitoring_service.update_all_tracked_items(123)
            
            assert result["updated_count"] == 1
            assert result["errors_count"] == 0
            assert result["total_items"] == 1
    
    @pytest.mark.asyncio
    async def test_get_item_current_data_wb(self, monitoring_service, sample_tracked_item):
        """Тест получения данных товара с Wildberries"""
        sample_tracked_item.marketplace = "wb"
        
        with patch.object(monitoring_service, '_parse_wildberries_item', return_value={
            "price": 1000.0, "stock": 10, "rating": 4.5
        }):
            result = await monitoring_service._get_item_current_data(sample_tracked_item)
            
            assert result["price"] == 1000.0
            assert result["stock"] == 10
            assert result["rating"] == 4.5
    
    @pytest.mark.asyncio
    async def test_parse_wildberries_item(self, monitoring_service, sample_tracked_item):
        """Тест парсинга товара с Wildberries"""
        with patch.object(monitoring_service.parser, 'parse_by_profile', return_value=[
            {"id": "12345", "price": 100000, "rating": 4.5, "stock": 10}
        ]):
            result = await monitoring_service._parse_wildberries_item(sample_tracked_item)
            
            assert result["price"] == 1000.0  # Цена в копейках
            assert result["stock"] == 10
            assert result["rating"] == 4.5


class TestAlertNotificationService:
    """Тесты класса AlertNotificationService"""
    
    @pytest.mark.asyncio
    async def test_send_alert_notification(self, notification_service):
        """Тест отправки уведомления об алерте"""
        alert_data = {
            "alert_type": "price_drop",
            "conditions": {"min_drop_percent": 10}
        }
        
        await notification_service.send_alert_notification(123, alert_data)
        
        # Проверяем, что бот был вызван
        notification_service.bot.send_message.assert_called_once()
        call_args = notification_service.bot.send_message.call_args
        assert call_args[1]["chat_id"] == 123
        assert "Цена упала!" in call_args[1]["text"]
    
    def test_format_alert_message_price_drop(self, notification_service):
        """Тест форматирования сообщения о падении цены"""
        message = notification_service._format_alert_message(
            "price_drop", 
            {"min_drop_percent": 15}
        )
        
        assert "Цена упала!" in message
        assert "15%" in message
    
    def test_format_alert_message_price_rise(self, notification_service):
        """Тест форматирования сообщения о росте цены"""
        message = notification_service._format_alert_message(
            "price_rise", 
            {"min_rise_percent": 20}
        )
        
        assert "Цена выросла!" in message
        assert "20%" in message
    
    def test_format_alert_message_stock_appeared(self, notification_service):
        """Тест форматирования сообщения о появлении товара"""
        message = notification_service._format_alert_message(
            "stock_change", 
            {"stock_appeared": True}
        )
        
        assert "Товар появился в наличии!" in message
    
    def test_format_alert_message_stock_disappeared(self, notification_service):
        """Тест форматирования сообщения об исчезновении товара"""
        message = notification_service._format_alert_message(
            "stock_change", 
            {"stock_disappeared": True}
        )
        
        assert "Товар закончился!" in message
    
    def test_format_alert_message_review_change(self, notification_service):
        """Тест форматирования сообщения об изменении рейтинга"""
        message = notification_service._format_alert_message(
            "review_change", 
            {"min_rating_change": 0.5}
        )
        
        assert "Изменился рейтинг!" in message
        assert "0.5" in message
