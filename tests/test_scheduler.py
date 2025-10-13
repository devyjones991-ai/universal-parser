"""
Тесты для планировщика
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from scheduler import MonitoringScheduler, start_monitoring, stop_monitoring


@pytest.fixture
def monitoring_scheduler():
    """Создание экземпляра MonitoringScheduler"""
    return MonitoringScheduler()


class TestMonitoringScheduler:
    """Тесты класса MonitoringScheduler"""
    
    def test_init(self, monitoring_scheduler):
        """Тест инициализации планировщика"""
        assert monitoring_scheduler.scheduler is not None
        assert monitoring_scheduler.is_running is False
    
    def test_start(self, monitoring_scheduler):
        """Тест запуска планировщика"""
        with patch.object(monitoring_scheduler.scheduler, 'start') as mock_start, \
             patch.object(monitoring_scheduler, '_setup_jobs') as mock_setup:
            
            monitoring_scheduler.start()
            
            mock_setup.assert_called_once()
            mock_start.assert_called_once()
            assert monitoring_scheduler.is_running is True
    
    def test_start_already_running(self, monitoring_scheduler):
        """Тест запуска уже работающего планировщика"""
        monitoring_scheduler.is_running = True
        
        with patch.object(monitoring_scheduler.scheduler, 'start') as mock_start:
            monitoring_scheduler.start()
            
            mock_start.assert_not_called()
    
    def test_stop(self, monitoring_scheduler):
        """Тест остановки планировщика"""
        monitoring_scheduler.is_running = True
        
        with patch.object(monitoring_scheduler.scheduler, 'shutdown') as mock_shutdown:
            monitoring_scheduler.stop()
            
            mock_shutdown.assert_called_once()
            assert monitoring_scheduler.is_running is False
    
    def test_stop_not_running(self, monitoring_scheduler):
        """Тест остановки не работающего планировщика"""
        with patch.object(monitoring_scheduler.scheduler, 'shutdown') as mock_shutdown:
            monitoring_scheduler.stop()
            
            mock_shutdown.assert_not_called()
    
    def test_setup_jobs(self, monitoring_scheduler):
        """Тест настройки задач планировщика"""
        with patch.object(monitoring_scheduler.scheduler, 'add_job') as mock_add_job:
            monitoring_scheduler._setup_jobs()
            
            # Проверяем, что все задачи добавлены
            assert mock_add_job.call_count == 4
            
            # Проверяем типы задач
            calls = [call[1] for call in mock_add_job.call_args_list]
            job_ids = [call['id'] for call in calls]
            
            assert "update_prices" in job_ids
            assert "check_alerts" in job_ids
            assert "daily_analytics" in job_ids
            assert "cleanup_data" in job_ids
    
    @pytest.mark.asyncio
    async def test_update_all_prices(self, monitoring_scheduler):
        """Тест обновления всех цен"""
        with patch('scheduler.logger') as mock_logger:
            await monitoring_scheduler._update_all_prices()
            
            mock_logger.info.assert_called()
            # Проверяем, что логируются начало и конец операции
            assert any("Начинаем обновление цен" in call[0][0] for call in mock_logger.info.call_args_list)
            assert any("Обновление цен завершено" in call[0][0] for call in mock_logger.info.call_args_list)
    
    @pytest.mark.asyncio
    async def test_check_all_alerts(self, monitoring_scheduler):
        """Тест проверки всех алертов"""
        with patch('scheduler.logger') as mock_logger:
            await monitoring_scheduler._check_all_alerts()
            
            mock_logger.info.assert_called()
            # Проверяем, что логируются начало и конец операции
            assert any("Начинаем проверку алертов" in call[0][0] for call in mock_logger.info.call_args_list)
            assert any("Проверка алертов завершена" in call[0][0] for call in mock_logger.info.call_args_list)
    
    @pytest.mark.asyncio
    async def test_daily_analytics(self, monitoring_scheduler):
        """Тест ежедневной аналитики"""
        with patch('scheduler.logger') as mock_logger:
            await monitoring_scheduler._daily_analytics()
            
            mock_logger.info.assert_called()
            # Проверяем, что логируются начало и конец операции
            assert any("Генерируем ежедневную аналитику" in call[0][0] for call in mock_logger.info.call_args_list)
            assert any("Ежедневная аналитика завершена" in call[0][0] for call in mock_logger.info.call_args_list)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, monitoring_scheduler):
        """Тест очистки старых данных"""
        with patch('scheduler.logger') as mock_logger:
            await monitoring_scheduler._cleanup_old_data()
            
            mock_logger.info.assert_called()
            # Проверяем, что логируются начало и конец операции
            assert any("Начинаем очистку старых данных" in call[0][0] for call in mock_logger.info.call_args_list)
            assert any("Очистка старых данных завершена" in call[0][0] for call in mock_logger.info.call_args_list)
    
    @pytest.mark.asyncio
    async def test_update_user_prices(self, monitoring_scheduler):
        """Тест обновления цен пользователя"""
        with patch('scheduler.monitoring_service') as mock_service, \
             patch('scheduler.logger') as mock_logger:
            
            mock_service.update_all_tracked_items = AsyncMock(return_value={
                "updated_count": 5,
                "errors_count": 1,
                "total_items": 6
            })
            
            result = await monitoring_scheduler.update_user_prices(123)
            
            assert result["updated_count"] == 5
            assert result["errors_count"] == 1
            assert result["total_items"] == 6
            
            mock_service.update_all_tracked_items.assert_called_once_with(123)
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_user_prices_error(self, monitoring_scheduler):
        """Тест обновления цен пользователя с ошибкой"""
        with patch('scheduler.monitoring_service') as mock_service, \
             patch('scheduler.logger') as mock_logger:
            
            mock_service.update_all_tracked_items = AsyncMock(side_effect=Exception("Database error"))
            
            result = await monitoring_scheduler.update_user_prices(123)
            
            assert result is None
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_user_alerts(self, monitoring_scheduler):
        """Тест проверки алертов пользователя"""
        with patch('scheduler.monitoring_service') as mock_service, \
             patch('scheduler.alert_notification_service') as mock_notification, \
             patch('scheduler.logger') as mock_logger:
            
            mock_service.check_user_alerts = AsyncMock(return_value=[
                {"alert_id": 1, "alert_type": "price_drop", "triggered_at": datetime.utcnow()}
            ])
            mock_notification.send_alert_notification = AsyncMock()
            
            result = await monitoring_scheduler.check_user_alerts(123)
            
            assert len(result) == 1
            assert result[0]["alert_id"] == 1
            
            mock_service.check_user_alerts.assert_called_once_with(123)
            mock_notification.send_alert_notification.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_user_alerts_error(self, monitoring_scheduler):
        """Тест проверки алертов пользователя с ошибкой"""
        with patch('scheduler.monitoring_service') as mock_service, \
             patch('scheduler.logger') as mock_logger:
            
            mock_service.check_user_alerts = AsyncMock(side_effect=Exception("API error"))
            
            result = await monitoring_scheduler.check_user_alerts(123)
            
            assert result == []
            mock_logger.error.assert_called()


class TestSchedulerIntegration:
    """Интеграционные тесты планировщика"""
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self):
        """Тест функции start_monitoring"""
        with patch('scheduler.monitoring_scheduler') as mock_scheduler, \
             patch('scheduler.logger') as mock_logger:
            
            await start_monitoring()
            
            mock_scheduler.start.assert_called_once()
            mock_logger.info.assert_called()
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self):
        """Тест функции stop_monitoring"""
        with patch('scheduler.monitoring_scheduler') as mock_scheduler, \
             patch('scheduler.logger') as mock_logger:
            
            await stop_monitoring()
            
            mock_scheduler.stop.assert_called_once()
            mock_logger.info.assert_called()


class TestSchedulerErrorHandling:
    """Тесты обработки ошибок планировщика"""
    
    @pytest.mark.asyncio
    async def test_update_all_prices_error(self, monitoring_scheduler):
        """Тест обработки ошибки при обновлении цен"""
        with patch('scheduler.logger') as mock_logger:
            # Симулируем ошибку в логгере
            mock_logger.info.side_effect = Exception("Logging error")
            
            # Функция должна завершиться без исключения
            await monitoring_scheduler._update_all_prices()
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_all_alerts_error(self, monitoring_scheduler):
        """Тест обработки ошибки при проверке алертов"""
        with patch('scheduler.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            
            await monitoring_scheduler._check_all_alerts()
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_daily_analytics_error(self, monitoring_scheduler):
        """Тест обработки ошибки при ежедневной аналитике"""
        with patch('scheduler.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            
            await monitoring_scheduler._daily_analytics()
            
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data_error(self, monitoring_scheduler):
        """Тест обработки ошибки при очистке данных"""
        with patch('scheduler.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            
            await monitoring_scheduler._cleanup_old_data()
            
            mock_logger.error.assert_called()
