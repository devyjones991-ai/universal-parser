"""
Тесты для системы подписок
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from subscription import SubscriptionService, PaymentService


@pytest.fixture
def subscription_service():
    """Создание экземпляра SubscriptionService"""
    return SubscriptionService()


@pytest.fixture
def payment_service():
    """Создание экземпляра PaymentService"""
    return PaymentService()


@pytest.fixture
def mock_user():
    """Создание мок-пользователя"""
    user = Mock()
    user.id = 123
    user.telegram_id = 123456789
    user.subscription_tier = "free"
    user.subscription_expires = None
    return user


class TestSubscriptionService:
    """Тесты класса SubscriptionService"""
    
    def test_get_subscription_info_free(self, subscription_service, mock_user):
        """Тест получения информации о бесплатной подписке"""
        with patch('subscription.get_user_by_telegram_id', return_value=mock_user):
            info = subscription_service.get_subscription_info(123)
            
            assert info["user_id"] == 123
            assert info["current_tier"] == "free"
            assert info["plan_name"] == "Бесплатный"
            assert info["price"] == 0
            assert info["is_active"] is True
            assert info["limits"]["tracked_items"] == 3
            assert info["limits"]["alerts"] == 5
            assert info["limits"]["analytics_days"] == 7
    
    def test_get_subscription_info_premium(self, subscription_service):
        """Тест получения информации о Premium подписке"""
        user = Mock()
        user.id = 123
        user.telegram_id = 123456789
        user.subscription_tier = "premium"
        user.subscription_expires = datetime.utcnow() + timedelta(days=30)
        
        with patch('subscription.get_user_by_telegram_id', return_value=user):
            info = subscription_service.get_subscription_info(123)
            
            assert info["current_tier"] == "premium"
            assert info["plan_name"] == "Premium"
            assert info["price"] == 990
            assert info["is_active"] is True
            assert info["limits"]["tracked_items"] == 50
            assert info["limits"]["alerts"] == 100
            assert info["limits"]["analytics_days"] == 90
    
    def test_get_subscription_info_expired(self, subscription_service):
        """Тест получения информации об истекшей подписке"""
        user = Mock()
        user.id = 123
        user.telegram_id = 123456789
        user.subscription_tier = "premium"
        user.subscription_expires = datetime.utcnow() - timedelta(days=1)
        
        with patch('subscription.get_user_by_telegram_id', return_value=user):
            info = subscription_service.get_subscription_info(123)
            
            assert info["current_tier"] == "premium"
            assert info["is_active"] is False
    
    def test_can_add_tracked_item_free_within_limit(self, subscription_service):
        """Тест возможности добавления товара в рамках лимита Free"""
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(id=123)), \
             patch('subscription.get_user_tracked_items_count', return_value=2):
            
            can_add, message = subscription_service.can_add_tracked_item(123)
            
            assert can_add is True
            assert message == ""
    
    def test_can_add_tracked_item_free_exceeded_limit(self, subscription_service):
        """Тест невозможности добавления товара при превышении лимита Free"""
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(id=123)), \
             patch('subscription.get_user_tracked_items_count', return_value=3):
            
            can_add, message = subscription_service.can_add_tracked_item(123)
            
            assert can_add is False
            assert "лимит" in message.lower()
            assert "3" in message
    
    def test_can_add_tracked_item_enterprise_unlimited(self, subscription_service):
        """Тест неограниченного добавления товаров в Enterprise"""
        user = Mock()
        user.id = 123
        user.subscription_tier = "enterprise"
        
        with patch('subscription.get_user_by_telegram_id', return_value=user):
            can_add, message = subscription_service.can_add_tracked_item(123)
            
            assert can_add is True
            assert message == ""
    
    def test_can_add_alert_free_within_limit(self, subscription_service):
        """Тест возможности добавления алерта в рамках лимита Free"""
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(id=123)), \
             patch('subscription.get_user_alerts_count', return_value=3):
            
            can_add, message = subscription_service.can_add_alert(123)
            
            assert can_add is True
            assert message == ""
    
    def test_can_add_alert_free_exceeded_limit(self, subscription_service):
        """Тест невозможности добавления алерта при превышении лимита Free"""
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(id=123)), \
             patch('subscription.get_user_alerts_count', return_value=5):
            
            can_add, message = subscription_service.can_add_alert(123)
            
            assert can_add is False
            assert "лимит" in message.lower()
            assert "5" in message
    
    def test_upgrade_subscription(self, subscription_service):
        """Тест обновления подписки"""
        with patch('subscription.update_user_subscription') as mock_update:
            result = subscription_service.upgrade_subscription(123, "premium", 1)
            
            assert result is True
            mock_update.assert_called_once()
            call_args = mock_update.call_args[0]
            assert call_args[0] == 123
            assert call_args[1] == "premium"
            assert isinstance(call_args[2], datetime)
    
    def test_upgrade_subscription_invalid_tier(self, subscription_service):
        """Тест обновления подписки на несуществующий тариф"""
        result = subscription_service.upgrade_subscription(123, "invalid_tier", 1)
        assert result is False
    
    def test_get_available_plans(self, subscription_service):
        """Тест получения доступных тарифных планов"""
        plans = subscription_service.get_available_plans()
        
        assert "free" in plans
        assert "premium" in plans
        assert "enterprise" in plans
        
        assert plans["free"]["name"] == "Бесплатный"
        assert plans["premium"]["name"] == "Premium"
        assert plans["enterprise"]["name"] == "Enterprise"
    
    def test_calculate_upgrade_price(self, subscription_service):
        """Тест расчета стоимости обновления подписки"""
        # Free to Premium
        price = subscription_service.calculate_upgrade_price("free", "premium")
        assert price == 990
        
        # Free to Enterprise
        price = subscription_service.calculate_upgrade_price("free", "enterprise")
        assert price == 2990
        
        # Premium to Enterprise
        price = subscription_service.calculate_upgrade_price("premium", "enterprise")
        assert price == 2000
        
        # Same tier
        price = subscription_service.calculate_upgrade_price("free", "free")
        assert price == 0
    
    def test_get_subscription_benefits(self, subscription_service):
        """Тест получения преимуществ тарифного плана"""
        benefits = subscription_service.get_subscription_benefits("premium")
        
        assert benefits["name"] == "Premium"
        assert benefits["price"] == 990
        assert "features" in benefits
        assert "limits" in benefits
        assert benefits["limits"]["tracked_items"] == 50
        assert benefits["limits"]["alerts"] == 100
        assert benefits["limits"]["analytics_days"] == 90


class TestPaymentService:
    """Тесты класса PaymentService"""
    
    @pytest.mark.asyncio
    async def test_create_payment_link(self, payment_service):
        """Тест создания ссылки для оплаты"""
        link = await payment_service.create_payment_link(
            user_id=123,
            amount=990,
            description="Premium подписка на 1 месяц"
        )
        
        assert link is not None
        assert "payment.example.com" in link
        assert "user=123" in link
        assert "amount=990" in link
    
    @pytest.mark.asyncio
    async def test_create_payment_link_error(self, payment_service):
        """Тест создания ссылки для оплаты с ошибкой"""
        with patch('subscription.datetime') as mock_datetime:
            mock_datetime.utcnow.side_effect = Exception("Database error")
            
            link = await payment_service.create_payment_link(
                user_id=123,
                amount=990,
                description="Test"
            )
            
            assert link is None
    
    @pytest.mark.asyncio
    async def test_verify_payment(self, payment_service):
        """Тест проверки статуса платежа"""
        result = await payment_service.verify_payment("payment_123")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_payment_error(self, payment_service):
        """Тест проверки статуса платежа с ошибкой"""
        with patch('subscription.logger') as mock_logger:
            mock_logger.error.side_effect = Exception("API error")
            
            result = await payment_service.verify_payment("invalid_payment")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_payment_webhook(self, payment_service):
        """Тест обработки webhook от платежной системы"""
        webhook_data = {
            "payment_id": "payment_123",
            "status": "success",
            "amount": 990,
            "user_id": 123
        }
        
        result = await payment_service.process_payment_webhook(webhook_data)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_process_payment_webhook_error(self, payment_service):
        """Тест обработки webhook с ошибкой"""
        webhook_data = {"invalid": "data"}
        
        with patch('subscription.logger') as mock_logger:
            mock_logger.error.side_effect = Exception("Processing error")
            
            result = await payment_service.process_payment_webhook(webhook_data)
            assert result is False


class TestSubscriptionIntegration:
    """Интеграционные тесты системы подписок"""
    
    def test_full_subscription_workflow(self, subscription_service, payment_service):
        """Тест полного рабочего процесса подписки"""
        # 1. Получаем информацию о текущей подписке
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(
            id=123, subscription_tier="free", subscription_expires=None
        )):
            info = subscription_service.get_subscription_info(123)
            assert info["current_tier"] == "free"
        
        # 2. Проверяем возможность добавления товара
        with patch('subscription.get_user_by_telegram_id', return_value=Mock(id=123)), \
             patch('subscription.get_user_tracked_items_count', return_value=2):
            
            can_add, _ = subscription_service.can_add_tracked_item(123)
            assert can_add is True
        
        # 3. Обновляем подписку
        with patch('subscription.update_user_subscription'):
            result = subscription_service.upgrade_subscription(123, "premium", 1)
            assert result is True
        
        # 4. Создаем ссылку для оплаты
        import asyncio
        link = asyncio.run(payment_service.create_payment_link(123, 990, "Premium"))
        assert link is not None
