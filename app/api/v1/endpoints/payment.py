"""API эндпоинты для платежей и кэшбека"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.payment_service import PaymentService
from app.schemas.subscription import (
    PaymentResponse, PaymentCreate, PaymentUpdate,
    CashbackResponse, CashbackCreate, ReferralResponse,
    ReferralCreate, PaymentIntentCreate, PaymentIntentResponse
)

router = APIRouter()


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """Создать платеж"""
    service = PaymentService(db)
    payment = service.create_payment(payment_data)
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Получить платеж по ID"""
    service = PaymentService(db)
    payment = service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment


@router.get("/user/{user_id}", response_model=List[PaymentResponse])
async def get_user_payments(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получить платежи пользователя"""
    service = PaymentService(db)
    payments = service.get_user_payments(user_id, limit)
    return payments


@router.put("/{payment_id}/status")
async def update_payment_status(
    payment_id: str,
    status: str,
    external_id: str = None,
    db: Session = Depends(get_db)
):
    """Обновить статус платежа"""
    service = PaymentService(db)
    success = service.update_payment_status(payment_id, status, external_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return {"message": "Payment status updated successfully"}


@router.post("/webhook")
async def process_payment_webhook(
    webhook_data: dict,
    db: Session = Depends(get_db)
):
    """Обработать webhook от платежной системы"""
    service = PaymentService(db)
    success = service.process_payment_webhook(webhook_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process webhook"
        )
    return {"message": "Webhook processed successfully"}


@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    intent_data: PaymentIntentCreate,
    db: Session = Depends(get_db)
):
    """Создать намерение платежа"""
    # Здесь будет интеграция с Stripe/PayPal
    # Пока что возвращаем заглушку
    return PaymentIntentResponse(
        client_secret="pi_mock_client_secret",
        payment_intent_id="pi_mock_payment_intent_id",
        amount=intent_data.amount,
        currency=intent_data.currency
    )


@router.post("/cashback", response_model=CashbackResponse)
async def create_cashback(
    cashback_data: CashbackCreate,
    db: Session = Depends(get_db)
):
    """Создать кэшбек"""
    service = PaymentService(db)
    cashback = service.create_cashback(cashback_data)
    return cashback


@router.get("/cashback/user/{user_id}", response_model=List[CashbackResponse])
async def get_user_cashbacks(user_id: str, db: Session = Depends(get_db)):
    """Получить кэшбеки пользователя"""
    service = PaymentService(db)
    cashbacks = service.get_user_cashbacks(user_id)
    return cashbacks


@router.put("/cashback/{cashback_id}/approve")
async def approve_cashback(cashback_id: str, db: Session = Depends(get_db)):
    """Одобрить кэшбек"""
    service = PaymentService(db)
    success = service.approve_cashback(cashback_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cashback not found"
        )
    return {"message": "Cashback approved successfully"}


@router.put("/cashback/{cashback_id}/pay")
async def pay_cashback(cashback_id: str, db: Session = Depends(get_db)):
    """Выплатить кэшбек"""
    service = PaymentService(db)
    success = service.pay_cashback(cashback_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cashback not found"
        )
    return {"message": "Cashback paid successfully"}


@router.post("/referral", response_model=ReferralResponse)
async def create_referral(
    referral_data: ReferralCreate,
    db: Session = Depends(get_db)
):
    """Создать реферал"""
    service = PaymentService(db)
    referral = service.create_referral(referral_data)
    return referral


@router.get("/referral/user/{user_id}", response_model=List[ReferralResponse])
async def get_user_referrals(user_id: str, db: Session = Depends(get_db)):
    """Получить рефералы пользователя"""
    service = PaymentService(db)
    referrals = service.get_user_referrals(user_id)
    return referrals


@router.put("/referral/{referral_id}/complete")
async def complete_referral(referral_id: str, db: Session = Depends(get_db)):
    """Завершить реферал"""
    service = PaymentService(db)
    success = service.complete_referral(referral_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    return {"message": "Referral completed successfully"}


@router.get("/referral/user/{user_id}/stats")
async def get_referral_stats(user_id: str, db: Session = Depends(get_db)):
    """Получить статистику рефералов"""
    service = PaymentService(db)
    stats = service.get_referral_stats(user_id)
    return stats


@router.post("/subscription")
async def process_subscription_payment(
    user_id: str,
    subscription_tier: str,
    amount: float,
    db: Session = Depends(get_db)
):
    """Обработать платеж за подписку"""
    service = PaymentService(db)
    result = service.process_subscription_payment(user_id, subscription_tier, amount)
    return result
