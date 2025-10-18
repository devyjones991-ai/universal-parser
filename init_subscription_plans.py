"""Скрипт для инициализации тарифных планов"""

import asyncio
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.subscription import SubscriptionPlan
from app.services.subscription_service import SubscriptionService
import json

def init_subscription_plans():
    """Инициализировать тарифные планы"""
    
    # Получаем сессию базы данных
    db = next(get_db())
    service = SubscriptionService(db)
    
    # Тарифные планы
    plans_data = [
        {
            "name": "Free",
            "tier": "free",
            "price_monthly": 0.0,
            "price_yearly": 0.0,
            "features": [
                "До 5 отслеживаемых товаров",
                "Базовые уведомления",
                "Ограниченная аналитика",
                "Поддержка по email"
            ],
            "limits": {
                "max_items": 5,
                "max_alerts": 3,
                "ai_requests_per_day": 10,
                "export_reports": False,
                "api_calls_per_hour": 100,
                "priority_support": False
            }
        },
        {
            "name": "Pro",
            "tier": "pro",
            "price_monthly": 19.99,
            "price_yearly": 199.99,
            "features": [
                "До 50 отслеживаемых товаров",
                "Умные уведомления",
                "Расширенная аналитика",
                "AI-рекомендации",
                "Экспорт отчетов",
                "API доступ",
                "Приоритетная поддержка",
                "Кэшбек 2%"
            ],
            "limits": {
                "max_items": 50,
                "max_alerts": 25,
                "ai_requests_per_day": 100,
                "export_reports": True,
                "api_calls_per_hour": 1000,
                "priority_support": True
            }
        },
        {
            "name": "Premium",
            "tier": "premium",
            "price_monthly": 49.99,
            "price_yearly": 499.99,
            "features": [
                "Неограниченное количество товаров",
                "Умные уведомления",
                "Полная аналитика",
                "AI-анализ ниш",
                "Динамическое ценообразование",
                "Прогнозирование трендов",
                "API доступ",
                "Приоритетная поддержка",
                "Кэшбек 5%",
                "Персональный менеджер"
            ],
            "limits": {
                "max_items": 1000,
                "max_alerts": 100,
                "ai_requests_per_day": 1000,
                "export_reports": True,
                "api_calls_per_hour": 10000,
                "priority_support": True
            }
        }
    ]
    
    # Создаем планы
    for plan_data in plans_data:
        # Проверяем, существует ли план
        existing_plan = service.get_subscription_plan(plan_data["tier"])
        if existing_plan:
            print(f"План {plan_data['name']} уже существует, пропускаем...")
            continue
        
        # Создаем план
        plan = SubscriptionPlan(
            name=plan_data["name"],
            tier=plan_data["tier"],
            price_monthly=plan_data["price_monthly"],
            price_yearly=plan_data["price_yearly"],
            features=json.dumps(plan_data["features"]),
            limits=json.dumps(plan_data["limits"]),
            is_active=True
        )
        
        db.add(plan)
        print(f"Создан план: {plan_data['name']}")
    
    # Сохраняем изменения
    db.commit()
    print("✅ Тарифные планы успешно инициализированы!")
    
    # Закрываем сессию
    db.close()

if __name__ == "__main__":
    init_subscription_plans()
