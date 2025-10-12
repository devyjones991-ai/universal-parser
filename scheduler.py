import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from db import get_user_by_telegram_id, get_user_tracked_items, update_tracked_item_price
from alert_system import monitoring_service, alert_notification_service
from config import settings

logger = logging.getLogger(__name__)

class MonitoringScheduler:
    """Планировщик для автоматического мониторинга"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Запустить планировщик"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        # Настраиваем задачи
        self._setup_jobs()
        
        # Запускаем планировщик
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Планировщик мониторинга запущен")
    
    def stop(self):
        """Остановить планировщик"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        
        logger.info("Планировщик мониторинга остановлен")
    
    def _setup_jobs(self):
        """Настроить задачи планировщика"""
        
        # Обновление цен каждые 30 минут
        self.scheduler.add_job(
            self._update_all_prices,
            trigger=IntervalTrigger(minutes=30),
            id="update_prices",
            name="Обновление цен товаров",
            max_instances=1
        )
        
        # Проверка алертов каждые 15 минут
        self.scheduler.add_job(
            self._check_all_alerts,
            trigger=IntervalTrigger(minutes=15),
            id="check_alerts",
            name="Проверка алертов",
            max_instances=1
        )
        
        # Ежедневная аналитика в 9:00
        self.scheduler.add_job(
            self._daily_analytics,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_analytics",
            name="Ежедневная аналитика",
            max_instances=1
        )
        
        # Очистка старых данных каждую неделю
        self.scheduler.add_job(
            self._cleanup_old_data,
            trigger=CronTrigger(day_of_week=0, hour=2, minute=0),  # Воскресенье в 2:00
            id="cleanup_data",
            name="Очистка старых данных",
            max_instances=1
        )
    
    async def _update_all_prices(self):
        """Обновить цены всех отслеживаемых товаров"""
        try:
            logger.info("Начинаем обновление цен...")
            
            # Получаем всех пользователей с отслеживаемыми товарами
            # TODO: Реализовать получение всех активных пользователей
            # Пока что это заглушка
            
            logger.info("Обновление цен завершено")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении цен: {e}")
    
    async def _check_all_alerts(self):
        """Проверить все алерты пользователей"""
        try:
            logger.info("Начинаем проверку алертов...")
            
            # Получаем всех пользователей с алертами
            # TODO: Реализовать получение всех пользователей с алертами
            
            logger.info("Проверка алертов завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке алертов: {e}")
    
    async def _daily_analytics(self):
        """Ежедневная аналитика"""
        try:
            logger.info("Генерируем ежедневную аналитику...")
            
            # TODO: Реализовать ежедневную аналитику
            # Отправка сводок пользователям
            
            logger.info("Ежедневная аналитика завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при генерации ежедневной аналитики: {e}")
    
    async def _cleanup_old_data(self):
        """Очистка старых данных"""
        try:
            logger.info("Начинаем очистку старых данных...")
            
            # TODO: Реализовать очистку старых данных
            # Удаление записей старше 6 месяцев
            
            logger.info("Очистка старых данных завершена")
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых данных: {e}")
    
    async def update_user_prices(self, user_id: int):
        """Обновить цены для конкретного пользователя"""
        try:
            result = await monitoring_service.update_all_tracked_items(user_id)
            
            logger.info(
                f"Обновление цен для пользователя {user_id}: "
                f"обновлено {result['updated_count']}, "
                f"ошибок {result['errors_count']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обновления цен для пользователя {user_id}: {e}")
            return None
    
    async def check_user_alerts(self, user_id: int):
        """Проверить алерты для конкретного пользователя"""
        try:
            triggered_alerts = await monitoring_service.check_user_alerts(user_id)
            
            if triggered_alerts:
                # Отправляем уведомления
                for alert_data in triggered_alerts:
                    await alert_notification_service.send_alert_notification(
                        user_id, alert_data
                    )
                
                logger.info(
                    f"Отправлено {len(triggered_alerts)} уведомлений пользователю {user_id}"
                )
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Ошибка проверки алертов для пользователя {user_id}: {e}")
            return []

# Глобальный экземпляр планировщика
monitoring_scheduler = MonitoringScheduler()

async def start_monitoring():
    """Запустить автоматический мониторинг"""
    monitoring_scheduler.start()
    logger.info("Автоматический мониторинг запущен")

async def stop_monitoring():
    """Остановить автоматический мониторинг"""
    monitoring_scheduler.stop()
    logger.info("Автоматический мониторинг остановлен")
