"""Сервис управления подписками"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionTier
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionPlanCreate,
    BillingSummary
)


class SubscriptionService:
    """Сервис управления подписками"""

    def __init__(self, db: Session):
        self.db = db

    def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Создать подписку"""
        subscription = Subscription(
            user_id=subscription_data.user_id,
            tier=subscription_data.tier,
            status=subscription_data.status,
            auto_renew=subscription_data.auto_renew,
            end_date=subscription_data.end_date
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получить подписку пользователя"""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()

    def update_subscription(self, subscription_id: str, update_data: SubscriptionUpdate) -> Optional[Subscription]:
        """Обновить подписку"""
        subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(subscription, field, value)

        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Отменить подписку"""
        subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            return False

        subscription.status = "cancelled"
        subscription.auto_renew = False
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def upgrade_subscription(self, user_id: str, new_tier: SubscriptionTier) -> Optional[Subscription]:
        """Обновить подписку до нового уровня"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return None

        subscription.tier = new_tier
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def extend_subscription(self, subscription_id: str, days: int) -> bool:
        """Продлить подписку на указанное количество дней"""
        subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            return False

        if subscription.end_date:
            subscription.end_date += timedelta(days=days)
        else:
            subscription.end_date = datetime.utcnow() + timedelta(days=days)

        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_subscription_plans(self) -> List[SubscriptionPlan]:
        """Получить все активные тарифные планы"""
        return self.db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()

    def get_subscription_plan(self, tier: SubscriptionTier) -> Optional[SubscriptionPlan]:
        """Получить тарифный план по уровню"""
        return self.db.query(SubscriptionPlan).filter(
            and_(
                SubscriptionPlan.tier == tier,
                SubscriptionPlan.is_active == True
            )
        ).first()

    def create_subscription_plan(self, plan_data: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Создать тарифный план"""
        import json
        
        plan = SubscriptionPlan(
            name=plan_data.name,
            tier=plan_data.tier,
            price_monthly=plan_data.price_monthly,
            price_yearly=plan_data.price_yearly,
            features=json.dumps(plan_data.features),
            limits=json.dumps(plan_data.limits)
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_billing_summary(self, user_id: str) -> BillingSummary:
        """Получить сводку по биллингу пользователя"""
        from app.models.subscription import Payment, Cashback, Referral
        
        # Текущая подписка
        current_subscription = self.get_user_subscription(user_id)
        
        # Общая сумма платежей
        total_payments = self.db.query(Payment).filter(
            and_(
                Payment.user_id == user_id,
                Payment.status == "completed"
            )
        ).with_entities(Payment.amount).all()
        total_payments_sum = sum(payment.amount for payment in total_payments) if total_payments else 0.0

        # Общий кэшбек
        total_cashback = self.db.query(Cashback).filter(
            and_(
                Cashback.user_id == user_id,
                Cashback.status.in_(["approved", "paid"])
            )
        ).with_entities(Cashback.amount).all()
        total_cashback_sum = sum(cb.amount for cb in total_cashback) if total_cashback else 0.0

        # Доступный кэшбек
        available_cashback = self.db.query(Cashback).filter(
            and_(
                Cashback.user_id == user_id,
                Cashback.status == "approved"
            )
        ).with_entities(Cashback.amount).all()
        available_cashback_sum = sum(cb.amount for cb in available_cashback) if available_cashback else 0.0

        # Реферальные награды
        referral_rewards = self.db.query(Referral).filter(
            and_(
                Referral.referrer_id == user_id,
                Referral.status == "completed"
            )
        ).with_entities(Referral.reward_amount).all()
        referral_rewards_sum = sum(ref.reward_amount for ref in referral_rewards) if referral_rewards else 0.0

        # Дата следующего платежа
        next_payment_date = None
        if current_subscription and current_subscription.auto_renew and current_subscription.end_date:
            next_payment_date = current_subscription.end_date

        return BillingSummary(
            current_subscription=current_subscription,
            total_payments=total_payments_sum,
            total_cashback=total_cashback_sum,
            available_cashback=available_cashback_sum,
            next_payment_date=next_payment_date,
            referral_rewards=referral_rewards_sum
        )

    def check_subscription_limits(self, user_id: str, limit_type: str) -> Dict[str, Any]:
        """Проверить ограничения подписки"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            # Лимиты для бесплатной подписки
            free_limits = {
                "max_items": 5,
                "max_alerts": 3,
                "ai_requests_per_day": 10,
                "export_reports": False,
                "api_calls_per_hour": 100
            }
            return free_limits

        plan = self.get_subscription_plan(subscription.tier)
        if not plan:
            return {}

        limits = plan.get_limits_dict()
        return limits

    def can_use_feature(self, user_id: str, feature: str) -> bool:
        """Проверить, может ли пользователь использовать функцию"""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False

        plan = self.get_subscription_plan(subscription.tier)
        if not plan:
            return False

        features = plan.get_features_list()
        return feature in features


