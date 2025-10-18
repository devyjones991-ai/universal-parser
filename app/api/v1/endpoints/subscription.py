"""API эндпоинты для подписок и биллинга"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.schemas.subscription import (
    SubscriptionResponse, SubscriptionCreate, SubscriptionUpdate,
    SubscriptionPlanResponse, BillingSummary, PaymentResponse,
    CashbackResponse, ReferralResponse, PaymentIntentCreate,
    PaymentIntentResponse
)
from app.models.subscription import SubscriptionTier

router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(get_db)):
    """Получить все тарифные планы"""
    service = SubscriptionService(db)
    plans = service.get_subscription_plans()
    return plans


@router.get("/plans/{tier}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(tier: SubscriptionTier, db: Session = Depends(get_db)):
    """Получить тарифный план по уровню"""
    service = SubscriptionService(db)
    plan = service.get_subscription_plan(tier)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )
    return plan


@router.get("/user/{user_id}", response_model=SubscriptionResponse)
async def get_user_subscription(user_id: str, db: Session = Depends(get_db)):
    """Получить подписку пользователя"""
    service = SubscriptionService(db)
    subscription = service.get_user_subscription(user_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User subscription not found"
        )
    return subscription


@router.post("/", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Создать подписку"""
    service = SubscriptionService(db)
    subscription = service.create_subscription(subscription_data)
    return subscription


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Обновить подписку"""
    service = SubscriptionService(db)
    subscription = service.update_subscription(subscription_id, update_data)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return subscription


@router.delete("/{subscription_id}")
async def cancel_subscription(subscription_id: str, db: Session = Depends(get_db)):
    """Отменить подписку"""
    service = SubscriptionService(db)
    success = service.cancel_subscription(subscription_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return {"message": "Subscription cancelled successfully"}


@router.post("/{subscription_id}/upgrade")
async def upgrade_subscription(
    subscription_id: str,
    new_tier: SubscriptionTier,
    db: Session = Depends(get_db)
):
    """Обновить подписку до нового уровня"""
    service = SubscriptionService(db)
    subscription = service.upgrade_subscription(subscription_id, new_tier)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return {"message": "Subscription upgraded successfully"}


@router.post("/{subscription_id}/extend")
async def extend_subscription(
    subscription_id: str,
    days: int,
    db: Session = Depends(get_db)
):
    """Продлить подписку"""
    service = SubscriptionService(db)
    success = service.extend_subscription(subscription_id, days)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    return {"message": f"Subscription extended by {days} days"}


@router.get("/user/{user_id}/billing", response_model=BillingSummary)
async def get_billing_summary(user_id: str, db: Session = Depends(get_db)):
    """Получить сводку по биллингу пользователя"""
    service = SubscriptionService(db)
    summary = service.get_billing_summary(user_id)
    return summary


@router.get("/user/{user_id}/limits")
async def get_subscription_limits(user_id: str, db: Session = Depends(get_db)):
    """Получить ограничения подписки пользователя"""
    service = SubscriptionService(db)
    limits = service.check_subscription_limits(user_id, "all")
    return limits


@router.get("/user/{user_id}/feature/{feature}")
async def check_feature_access(user_id: str, feature: str, db: Session = Depends(get_db)):
    """Проверить доступ к функции"""
    service = SubscriptionService(db)
    has_access = service.can_use_feature(user_id, feature)
    return {"feature": feature, "has_access": has_access}
