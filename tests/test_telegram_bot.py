"""
Тесты для Telegram-бота
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from aiogram.types import Message, User, Chat, CallbackQuery
from aiogram.fsm.context import FSMContext

from tg_commands import (
    get_user_or_create, cmd_start, cmd_monitor, cmd_my_items,
    cmd_alerts, cmd_stats, cmd_analytics, cmd_subscription
)


@pytest.fixture
def mock_message():
    """Создание мок-сообщения"""
    message = Mock(spec=Message)
    message.from_user = Mock(spec=User)
    message.from_user.id = 123456789
    message.from_user.username = "test_user"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.text = "/start"
    message.reply = AsyncMock()
    message.reply_document = AsyncMock()
    message.reply_photo = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query():
    """Создание мок-callback query"""
    callback = Mock(spec=CallbackQuery)
    callback.from_user = Mock(spec=User)
    callback.from_user.id = 123456789
    callback.message = Mock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.reply = AsyncMock()
    callback.message.reply_document = AsyncMock()
    callback.message.reply_photo = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = "test_callback"
    return callback


@pytest.fixture
def mock_state():
    """Создание мок-FSM состояния"""
    state = Mock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.clear = AsyncMock()
    return state


class TestUserManagement:
    """Тесты управления пользователями"""
    
    def test_get_user_or_create(self, mock_message):
        """Тест создания/получения пользователя"""
        with patch('tg_commands.get_or_create_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            
            result = get_user_or_create(mock_message)
            
            assert result == mock_user
            mock_get_user.assert_called_once_with(
                telegram_id=123456789,
                username="test_user",
                first_name="Test",
                last_name="User"
            )


class TestBotCommands:
    """Тесты команд бота"""
    
    @pytest.mark.asyncio
    async def test_cmd_start(self, mock_message):
        """Тест команды /start"""
        with patch('tg_commands.get_or_create_user') as mock_get_user:
            mock_user = Mock()
            mock_user.first_name = "Test"
            mock_get_user.return_value = mock_user
            
            await cmd_start(mock_message)
            
            mock_get_user.assert_called_once()
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "Добро пожаловать" in call_args[0][0]
            assert "Test" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_monitor_free_limit_exceeded(self, mock_message, mock_state):
        """Тест команды /monitor при превышении лимита Free"""
        mock_message.text = "/monitor"
        
        with patch('tg_commands.get_user_or_create') as mock_get_user, \
             patch('tg_commands.get_user_stats') as mock_stats:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_stats.return_value = {
                "subscription_tier": "free",
                "tracked_items_count": 3
            }
            
            await cmd_monitor(mock_message, mock_state)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "лимит" in call_args[0][0].lower()
            assert "3" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_monitor_within_limit(self, mock_message, mock_state):
        """Тест команды /monitor в рамках лимита"""
        mock_message.text = "/monitor"
        
        with patch('tg_commands.get_user_or_create') as mock_get_user, \
             patch('tg_commands.get_user_stats') as mock_stats:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_stats.return_value = {
                "subscription_tier": "free",
                "tracked_items_count": 2
            }
            
            await cmd_monitor(mock_message, mock_state)
            
            mock_state.set_state.assert_called_once()
            mock_message.reply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cmd_my_items_no_items(self, mock_message):
        """Тест команды /myitems без товаров"""
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.get_user_tracked_items') as mock_get_items:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_get_items.return_value = []
            
            await cmd_my_items(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "нет отслеживаемых товаров" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_cmd_my_items_with_items(self, mock_message):
        """Тест команды /myitems с товарами"""
        mock_item = Mock()
        mock_item.name = "Test Product"
        mock_item.current_price = 1000.0
        mock_item.current_stock = 5
        mock_item.marketplace = "wb"
        mock_item.url = "https://example.com"
        
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.get_user_tracked_items') as mock_get_items:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_get_items.return_value = [mock_item]
            
            await cmd_my_items(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "Test Product" in call_args[0][0]
            assert "1000" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_alerts_no_alerts(self, mock_message):
        """Тест команды /alerts без алертов"""
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.get_user_alerts') as mock_get_alerts:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_get_alerts.return_value = []
            
            await cmd_alerts(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "нет настроенных алертов" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_cmd_stats(self, mock_message):
        """Тест команды /stats"""
        mock_user = Mock()
        mock_user.id = 123
        mock_user.first_name = "Test"
        
        with patch('tg_commands.get_user_by_telegram_id', return_value=mock_user), \
             patch('tg_commands.get_user_stats') as mock_stats:
            
            mock_stats.return_value = {
                "subscription_tier": "free",
                "tracked_items_count": 2,
                "alerts_count": 1,
                "created_at": "2024-01-01 00:00:00",
                "last_activity": "2024-01-01 12:00:00"
            }
            
            await cmd_stats(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "статистика" in call_args[0][0].lower()
            assert "Test" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_cmd_analytics_no_data(self, mock_message):
        """Тест команды /analytics без данных"""
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.analytics_service') as mock_analytics:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_analytics.generate_analytics_report.return_value = {}
            
            await cmd_analytics(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "аналитика недоступна" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_cmd_subscription(self, mock_message):
        """Тест команды /subscription"""
        mock_user = Mock()
        mock_user.id = 123
        mock_user.first_name = "Test"
        
        with patch('tg_commands.get_user_by_telegram_id', return_value=mock_user), \
             patch('tg_commands.subscription_service') as mock_subscription:
            
            mock_subscription.get_subscription_info.return_value = {
                "user_id": 123,
                "current_tier": "free",
                "plan_name": "Бесплатный",
                "price": 0,
                "expires": None,
                "is_active": True,
                "limits": {
                    "tracked_items": 3,
                    "alerts": 5,
                    "analytics_days": 7
                },
                "features": ["Отслеживание до 3 товаров"]
            }
            
            await cmd_subscription(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "подписка" in call_args[0][0].lower()
            assert "Бесплатный" in call_args[0][0]


class TestCallbackHandlers:
    """Тесты обработчиков callback-кнопок"""
    
    @pytest.mark.asyncio
    async def test_handle_detailed_analytics(self, mock_callback_query):
        """Тест обработчика подробной аналитики"""
        from tg_commands import handle_detailed_analytics
        
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.analytics_service') as mock_analytics:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_analytics.get_price_trends.return_value = {
                "Product 1": {
                    "current_price": 1000.0,
                    "price_change_percent": -10.0,
                    "min_price": 800.0,
                    "max_price": 1200.0,
                    "trend": "down"
                }
            }
            
            await handle_detailed_analytics(mock_callback_query)
            
            mock_callback_query.message.edit_text.assert_called_once()
            call_args = mock_callback_query.message.edit_text.call_args
            assert "аналитика" in call_args[0][0].lower()
            assert "Product 1" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_export_excel(self, mock_callback_query):
        """Тест обработчика экспорта в Excel"""
        from tg_commands import handle_export_excel
        
        with patch('tg_commands.get_user_by_telegram_id') as mock_get_user, \
             patch('tg_commands.analytics_service') as mock_analytics:
            
            mock_user = Mock()
            mock_user.id = 123
            mock_get_user.return_value = mock_user
            mock_analytics.export_to_excel.return_value = b"fake_excel_data"
            
            await handle_export_excel(mock_callback_query)
            
            mock_callback_query.message.reply_document.assert_called_once()
            call_args = mock_callback_query.message.reply_document.call_args
            assert "analytics" in call_args[1]["filename"]


class TestButtonHandlers:
    """Тесты обработчиков кнопок"""
    
    @pytest.mark.asyncio
    async def test_handle_stats_button(self, mock_message):
        """Тест обработчика кнопки статистики"""
        from tg_commands import handle_stats_button
        
        with patch('tg_commands.cmd_stats') as mock_cmd_stats:
            await handle_stats_button(mock_message)
            mock_cmd_stats.assert_called_once_with(mock_message)
    
    @pytest.mark.asyncio
    async def test_handle_help_button(self, mock_message):
        """Тест обработчика кнопки помощи"""
        from tg_commands import handle_help_button
        
        await handle_help_button(mock_message)
        
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args
        assert "помощь" in call_args[0][0].lower()
        assert "команды" in call_args[0][0].lower()


class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    @pytest.mark.asyncio
    async def test_cmd_my_items_user_not_found(self, mock_message):
        """Тест команды /myitems когда пользователь не найден"""
        with patch('tg_commands.get_user_by_telegram_id', return_value=None):
            await cmd_my_items(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "пользователь не найден" in call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_cmd_analytics_user_not_found(self, mock_message):
        """Тест команды /analytics когда пользователь не найден"""
        with patch('tg_commands.get_user_by_telegram_id', return_value=None):
            await cmd_analytics(mock_message)
            
            mock_message.reply.assert_called_once()
            call_args = mock_message.reply.call_args
            assert "пользователь не найден" in call_args[0][0].lower()
