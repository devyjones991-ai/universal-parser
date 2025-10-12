import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from db import (
    get_user_alerts, get_user_tracked_items, update_tracked_item_price,
    trigger_alert, get_price_history, TrackedItem, Alert
)
from parser import UniversalParser
from config import settings
import logging

logger = logging.getLogger(__name__)

class AlertChecker:
    """Класс для проверки условий алертов"""
    
    @staticmethod
    def check_price_drop_alert(alert: Alert, current_price: float, previous_price: float) -> bool:
        """Проверка алерта на падение цены"""
        if not previous_price or not current_price:
            return False
        
        conditions = alert.conditions
        drop_percent = ((previous_price - current_price) / previous_price) * 100
        
        if "min_drop_percent" in conditions:
            return drop_percent >= conditions["min_drop_percent"]
        
        return False
    
    @staticmethod
    def check_price_rise_alert(alert: Alert, current_price: float, previous_price: float) -> bool:
        """Проверка алерта на рост цены"""
        if not previous_price or not current_price:
            return False
        
        conditions = alert.conditions
        rise_percent = ((current_price - previous_price) / previous_price) * 100
        
        if "min_rise_percent" in conditions:
            return rise_percent >= conditions["min_rise_percent"]
        
        return False
    
    @staticmethod
    def check_stock_change_alert(alert: Alert, current_stock: int, previous_stock: int) -> bool:
        """Проверка алерта на изменение остатков"""
        if previous_stock is None or current_stock is None:
            return False
        
        conditions = alert.conditions
        
        # Проверка на появление товара в наличии
        if conditions.get("stock_appeared") and previous_stock == 0 and current_stock > 0:
            return True
        
        # Проверка на исчезновение товара
        if conditions.get("stock_disappeared") and previous_stock > 0 and current_stock == 0:
            return True
        
        # Проверка на критически низкий остаток
        if "low_stock_threshold" in conditions:
            return current_stock <= conditions["low_stock_threshold"]
        
        return False
    
    @staticmethod
    def check_review_change_alert(alert: Alert, current_rating: float, previous_rating: float) -> bool:
        """Проверка алерта на изменение рейтинга"""
        if not previous_rating or not current_rating:
            return False
        
        conditions = alert.conditions
        rating_change = abs(current_rating - previous_rating)
        
        if "min_rating_change" in conditions:
            return rating_change >= conditions["min_rating_change"]
        
        return False

class MonitoringService:
    """Сервис мониторинга товаров и алертов"""
    
    def __init__(self):
        self.parser = UniversalParser()
        self.alert_checker = AlertChecker()
    
    async def check_user_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Проверить все алерты пользователя"""
        alerts = get_user_alerts(user_id)
        triggered_alerts = []
        
        for alert in alerts:
            try:
                if await self._check_alert(alert):
                    triggered_alerts.append({
                        "alert_id": alert.id,
                        "alert_type": alert.alert_type,
                        "conditions": alert.conditions,
                        "triggered_at": datetime.utcnow()
                    })
                    trigger_alert(alert.id)
            except Exception as e:
                logger.error(f"Ошибка при проверке алерта {alert.id}: {e}")
        
        return triggered_alerts
    
    async def _check_alert(self, alert: Alert) -> bool:
        """Проверить конкретный алерт"""
        # Получаем отслеживаемые товары пользователя
        tracked_items = get_user_tracked_items(alert.user_id)
        
        for item in tracked_items:
            try:
                # Получаем актуальные данные товара
                current_data = await self._get_item_current_data(item)
                if not current_data:
                    continue
                
                # Получаем предыдущие данные из истории
                price_history = get_price_history(alert.user_id, item.id, days=1)
                previous_data = price_history[0] if price_history else None
                
                # Проверяем условия алерта
                if alert.alert_type == "price_drop":
                    if self.alert_checker.check_price_drop_alert(
                        alert, current_data.get("price"), 
                        previous_data.price if previous_data else None
                    ):
                        return True
                
                elif alert.alert_type == "price_rise":
                    if self.alert_checker.check_price_rise_alert(
                        alert, current_data.get("price"), 
                        previous_data.price if previous_data else None
                    ):
                        return True
                
                elif alert.alert_type == "stock_change":
                    if self.alert_checker.check_stock_change_alert(
                        alert, current_data.get("stock"), 
                        previous_data.stock if previous_data else None
                    ):
                        return True
                
                elif alert.alert_type == "review_change":
                    if self.alert_checker.check_review_change_alert(
                        alert, current_data.get("rating"), 
                        previous_data.rating if previous_data else None
                    ):
                        return True
                
            except Exception as e:
                logger.error(f"Ошибка при проверке товара {item.id}: {e}")
                continue
        
        return False
    
    async def _get_item_current_data(self, item: TrackedItem) -> Optional[Dict[str, Any]]:
        """Получить актуальные данные товара"""
        try:
            if item.marketplace == "wb":
                return await self._parse_wildberries_item(item)
            elif item.marketplace == "ozon":
                return await self._parse_ozon_item(item)
            elif item.marketplace == "yandex":
                return await self._parse_yandex_item(item)
            else:
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных товара {item.id}: {e}")
            return None
    
    async def _parse_wildberries_item(self, item: TrackedItem) -> Optional[Dict[str, Any]]:
        """Парсинг товара с Wildberries"""
        try:
            # Используем API Wildberries для получения данных
            async with self.parser as parser:
                results = await parser.parse_by_profile("wildberries_search", search_term=item.name)
                
                # Ищем товар по ID
                for result in results:
                    if str(result.get("id")) == item.item_id:
                        return {
                            "price": result.get("price", 0) / 100,  # Цена в копейках
                            "stock": result.get("stock", 0),
                            "rating": result.get("rating", 0)
                        }
        except Exception as e:
            logger.error(f"Ошибка парсинга WB товара {item.id}: {e}")
        
        return None
    
    async def _parse_ozon_item(self, item: TrackedItem) -> Optional[Dict[str, Any]]:
        """Парсинг товара с Ozon"""
        # TODO: Реализовать парсинг Ozon
        return None
    
    async def _parse_yandex_item(self, item: TrackedItem) -> Optional[Dict[str, Any]]:
        """Парсинг товара с Яндекс.Маркета"""
        # TODO: Реализовать парсинг Яндекс.Маркета
        return None
    
    async def update_all_tracked_items(self, user_id: int) -> Dict[str, Any]:
        """Обновить все отслеживаемые товары пользователя"""
        tracked_items = get_user_tracked_items(user_id)
        updated_count = 0
        errors_count = 0
        
        for item in tracked_items:
            try:
                current_data = await self._get_item_current_data(item)
                if current_data:
                    update_tracked_item_price(
                        item.id,
                        current_data.get("price"),
                        current_data.get("stock"),
                        current_data.get("rating")
                    )
                    updated_count += 1
                else:
                    errors_count += 1
            except Exception as e:
                logger.error(f"Ошибка обновления товара {item.id}: {e}")
                errors_count += 1
        
        return {
            "updated_count": updated_count,
            "errors_count": errors_count,
            "total_items": len(tracked_items)
        }

class AlertNotificationService:
    """Сервис уведомлений об алертах"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def send_alert_notification(self, user_id: int, alert_data: Dict[str, Any]):
        """Отправить уведомление об алерте"""
        try:
            alert_type = alert_data["alert_type"]
            conditions = alert_data["conditions"]
            
            message = self._format_alert_message(alert_type, conditions)
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
    
    def _format_alert_message(self, alert_type: str, conditions: Dict[str, Any]) -> str:
        """Форматировать сообщение об алерте"""
        if alert_type == "price_drop":
            return f"📉 <b>Цена упала!</b>\n\n" \
                   f"Товар подешевел на {conditions.get('min_drop_percent', 0)}%"
        
        elif alert_type == "price_rise":
            return f"📈 <b>Цена выросла!</b>\n\n" \
                   f"Товар подорожал на {conditions.get('min_rise_percent', 0)}%"
        
        elif alert_type == "stock_change":
            if conditions.get("stock_appeared"):
                return f"✅ <b>Товар появился в наличии!</b>"
            elif conditions.get("stock_disappeared"):
                return f"❌ <b>Товар закончился!</b>"
            else:
                return f"⚠️ <b>Критически низкий остаток!</b>"
        
        elif alert_type == "review_change":
            return f"⭐ <b>Изменился рейтинг!</b>\n\n" \
                   f"Изменение на {conditions.get('min_rating_change', 0)} баллов"
        
        return "🔔 <b>Сработал алерт!</b>"

# Глобальные экземпляры сервисов
monitoring_service = MonitoringService()
alert_notification_service = None  # Будет инициализирован в tg_commands.py

async def run_monitoring_cycle():
    """Запустить цикл мониторинга для всех пользователей"""
    # TODO: Получить всех активных пользователей
    # Пока что это заглушка
    logger.info("Запуск цикла мониторинга...")
    
    # Здесь будет логика получения всех пользователей и проверки их алертов
    pass
