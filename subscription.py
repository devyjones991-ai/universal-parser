from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from db import get_user_by_telegram_id, update_user_subscription
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Сервис управления подписками"""
    
    # Тарифные планы
    SUBSCRIPTION_PLANS = {
        "free": {
            "name": "Бесплатный",
            "price": 0,
            "tracked_items_limit": 3,
            "alerts_limit": 5,
            "analytics_days": 7,
            "features": [
                "Отслеживание до 3 товаров",
                "До 5 алертов",
                "Базовая аналитика (7 дней)",
                "Уведомления в Telegram"
            ]
        },
        "premium": {
            "name": "Premium",
            "price": 990,  # рублей в месяц
            "tracked_items_limit": 50,
            "alerts_limit": 100,
            "analytics_days": 90,
            "features": [
                "Отслеживание до 50 товаров",
                "До 100 алертов",
                "Расширенная аналитика (90 дней)",
                "Экспорт в Excel",
                "Графики цен",
                "Приоритетная поддержка"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 2990,  # рублей в месяц
            "tracked_items_limit": -1,  # без ограничений
            "alerts_limit": -1,  # без ограничений
            "analytics_days": 365,
            "features": [
                "Неограниченное отслеживание",
                "Неограниченные алерты",
                "Полная аналитика (365 дней)",
                "API доступ",
                "Персональный менеджер",
                "Кастомные интеграции"
            ]
        }
    }
    
    def __init__(self):
        pass
    
    def get_subscription_info(self, user_id: int) -> Dict[str, Any]:
        """Получить информацию о подписке пользователя"""
        user = get_user_by_telegram_id(user_id)
        if not user:
            return {}
        
        plan = self.SUBSCRIPTION_PLANS.get(user.subscription_tier, self.SUBSCRIPTION_PLANS["free"])
        
        return {
            "user_id": user_id,
            "current_tier": user.subscription_tier,
            "plan_name": plan["name"],
            "price": plan["price"],
            "expires": user.subscription_expires.strftime('%Y-%m-%d') if user.subscription_expires else None,
            "is_active": self._is_subscription_active(user),
            "limits": {
                "tracked_items": plan["tracked_items_limit"],
                "alerts": plan["alerts_limit"],
                "analytics_days": plan["analytics_days"]
            },
            "features": plan["features"]
        }
    
    def _is_subscription_active(self, user) -> bool:
        """Проверить, активна ли подписка"""
        if user.subscription_tier == "free":
            return True
        
        if not user.subscription_expires:
            return False
        
        return user.subscription_expires > datetime.utcnow()
    
    def can_add_tracked_item(self, user_id: int) -> tuple[bool, str]:
        """Проверить, может ли пользователь добавить товар"""
        user = get_user_by_telegram_id(user_id)
        if not user:
            return False, "Пользователь не найден"
        
        plan = self.SUBSCRIPTION_PLANS.get(user.subscription_tier, self.SUBSCRIPTION_PLANS["free"])
        
        # Проверяем лимиты
        if plan["tracked_items_limit"] == -1:  # Без ограничений
            return True, ""
        
        # TODO: Получить текущее количество отслеживаемых товаров
        # current_count = get_user_tracked_items_count(user_id)
        current_count = 0  # Заглушка
        
        if current_count >= plan["tracked_items_limit"]:
            return False, f"Достигнут лимит {plan['tracked_items_limit']} товаров для тарифа {plan['name']}"
        
        return True, ""
    
    def can_add_alert(self, user_id: int) -> tuple[bool, str]:
        """Проверить, может ли пользователь добавить алерт"""
        user = get_user_by_telegram_id(user_id)
        if not user:
            return False, "Пользователь не найден"
        
        plan = self.SUBSCRIPTION_PLANS.get(user.subscription_tier, self.SUBSCRIPTION_PLANS["free"])
        
        # Проверяем лимиты
        if plan["alerts_limit"] == -1:  # Без ограничений
            return True, ""
        
        # TODO: Получить текущее количество алертов
        # current_count = get_user_alerts_count(user_id)
        current_count = 0  # Заглушка
        
        if current_count >= plan["alerts_limit"]:
            return False, f"Достигнут лимит {plan['alerts_limit']} алертов для тарифа {plan['name']}"
        
        return True, ""
    
    def upgrade_subscription(self, user_id: int, new_tier: str, duration_months: int = 1) -> bool:
        """Обновить подписку пользователя"""
        try:
            if new_tier not in self.SUBSCRIPTION_PLANS:
                return False
            
            # Вычисляем дату окончания
            expires = datetime.utcnow() + timedelta(days=30 * duration_months)
            
            # Обновляем в базе данных
            update_user_subscription(user_id, new_tier, expires)
            
            logger.info(f"Подписка пользователя {user_id} обновлена на {new_tier}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления подписки для пользователя {user_id}: {e}")
            return False
    
    def get_available_plans(self) -> Dict[str, Dict[str, Any]]:
        """Получить доступные тарифные планы"""
        return self.SUBSCRIPTION_PLANS
    
    def calculate_upgrade_price(self, current_tier: str, new_tier: str) -> int:
        """Рассчитать стоимость обновления подписки"""
        current_plan = self.SUBSCRIPTION_PLANS.get(current_tier, self.SUBSCRIPTION_PLANS["free"])
        new_plan = self.SUBSCRIPTION_PLANS.get(new_tier, self.SUBSCRIPTION_PLANS["free"])
        
        return max(0, new_plan["price"] - current_plan["price"])
    
    def get_subscription_benefits(self, tier: str) -> Dict[str, Any]:
        """Получить преимущества тарифного плана"""
        plan = self.SUBSCRIPTION_PLANS.get(tier, self.SUBSCRIPTION_PLANS["free"])
        
        return {
            "name": plan["name"],
            "price": plan["price"],
            "features": plan["features"],
            "limits": {
                "tracked_items": plan["tracked_items_limit"],
                "alerts": plan["alerts_limit"],
                "analytics_days": plan["analytics_days"]
            }
        }

class PaymentService:
    """Сервис обработки платежей"""
    
    def __init__(self):
        # TODO: Интеграция с платежными системами
        # ЮKassa, CloudPayments, Stripe и т.д.
        pass
    
    async def create_payment_link(self, user_id: int, amount: int, description: str) -> Optional[str]:
        """Создать ссылку для оплаты"""
        try:
            # TODO: Реализовать создание ссылки для оплаты
            # Пока что возвращаем заглушку
            
            payment_data = {
                "user_id": user_id,
                "amount": amount,
                "description": description,
                "created_at": datetime.utcnow()
            }
            
            # В реальной реализации здесь будет интеграция с платежной системой
            payment_link = f"https://payment.example.com/pay?user={user_id}&amount={amount}"
            
            logger.info(f"Создана ссылка для оплаты: {payment_link}")
            return payment_link
            
        except Exception as e:
            logger.error(f"Ошибка создания ссылки для оплаты: {e}")
            return None
    
    async def verify_payment(self, payment_id: str) -> bool:
        """Проверить статус платежа"""
        try:
            # TODO: Реализовать проверку статуса платежа
            # В реальной реализации здесь будет запрос к API платежной системы
            
            # Заглушка - всегда возвращаем успех
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки платежа {payment_id}: {e}")
            return False
    
    async def process_payment_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Обработать webhook от платежной системы"""
        try:
            # TODO: Реализовать обработку webhook
            # Проверка подписи, обновление статуса подписки и т.д.
            
            logger.info(f"Получен webhook платежа: {webhook_data}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            return False

# Глобальные экземпляры сервисов
subscription_service = SubscriptionService()
payment_service = PaymentService()
