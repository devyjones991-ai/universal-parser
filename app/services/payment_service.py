"""Сервис управления платежами"""

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.subscription import Payment, PaymentStatus, Cashback, Referral
from app.schemas.subscription import (
    PaymentCreate, PaymentUpdate, CashbackCreate, ReferralCreate
)

class PaymentService:
    """Сервис управления платежами"""

    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Создать платеж"""
        payment = Payment(
            user_id=payment_data.user_id,
            subscription_id=payment_data.subscription_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_method=payment_data.payment_method,
            description=payment_data.description
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update_payment_status(self, payment_id: str, status: PaymentStatus, external_id: Optional[str] = None) -> bool  # noqa  # noqa: E501 E501
        """Обновить статус платежа"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            return False

        payment.status = status
        if external_id:
            payment.external_id = external_id
        payment.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получить платеж по ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()

    def get_user_payments(self, user_id: str, limit: int = 50) -> list[Payment]  # noqa  # noqa: E501 E501
        """Получить платежи пользователя"""
        return self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).limit(limit).all()

    def process_payment_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Обработать webhook от платежной системы"""
        # Здесь будет логика обработки webhook от Stripe/PayPal
        # Пока что заглушка
        return True

    def create_cashback(self, cashback_data: CashbackCreate) -> Cashback:
        """Создать кэшбек"""
        cashback = Cashback(
            user_id=cashback_data.user_id,
            amount=cashback_data.amount,
            percentage=cashback_data.percentage,
            source=cashback_data.source,
            description=cashback_data.description
        )
        self.db.add(cashback)
        self.db.commit()
        self.db.refresh(cashback)
        return cashback

    def approve_cashback(self, cashback_id: str) -> bool:
        """Одобрить кэшбек"""
        cashback = self.db.query(Cashback).filter(Cashback.id == cashback_id).first()
        if not cashback:
            return False

        cashback.status = "approved"
        self.db.commit()
        return True

    def pay_cashback(self, cashback_id: str) -> bool:
        """Выплатить кэшбек"""
        cashback = self.db.query(Cashback).filter(Cashback.id == cashback_id).first()
        if not cashback:
            return False

        cashback.status = "paid"
        cashback.paid_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_user_cashbacks(self, user_id: str) -> list[Cashback]:
        """Получить кэшбеки пользователя"""
        return self.db.query(Cashback).filter(
            Cashback.user_id == user_id
        ).order_by(Cashback.created_at.desc()).all()

    def create_referral(self, referral_data: ReferralCreate) -> Referral:
        """Создать реферал"""
        referral = Referral(
            referrer_id=referral_data.referrer_id,
            referred_id=referral_data.referred_id,
            reward_amount=referral_data.reward_amount
        )
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def complete_referral(self, referral_id: str) -> bool:
        """Завершить реферал"""
        referral = self.db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            return False

        referral.status = "completed"
        referral.completed_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Получить статистику рефералов"""
        total_referrals = self.db.query(Referral).filter(Referral.referrer_id == user_id).count()
        completed_referrals = self.db.query(Referral).filter(
            and_(
                Referral.referrer_id == user_id,
                Referral.status == "completed"
            )
        ).count()

        total_rewards = self.db.query(Referral).filter(
            and_(
                Referral.referrer_id == user_id,
                Referral.status == "completed"
            )
        ).with_entities(Referral.reward_amount).all()
        total_rewards_sum = sum(ref.reward_amount for ref in total_rewards) if total_rewards else 0.0

        return {
            "total_referrals": total_referrals,
            "completed_referrals": completed_referrals,
            "total_rewards": total_rewards_sum
        }

    def calculate_cashback(self, amount: float, subscription_tier: str) -> float  # noqa  # noqa: E501 E501
        """Рассчитать кэшбек"""
        cashback_rates = {
            "free": 0.0,
            "pro": 0.02,  # 2%
            "premium": 0.05  # 5%
        }

        rate = cashback_rates.get(subscription_tier, 0.0)
        return amount * rate

    def process_subscription_payment(self, user_id: str, subscription_tier: str, amount: float) -> Dict[str, Any]  # noqa  # noqa: E501 E501
        """Обработать платеж за подписку"""
        # Создаем платеж
        payment = self.create_payment(PaymentCreate(
            user_id=user_id,
            amount=amount,
            payment_method="stripe",
            description=f"Subscription payment for {subscription_tier} tier"
        ))

        # Рассчитываем кэшбек
        cashback_amount = self.calculate_cashback(amount, subscription_tier)
        if cashback_amount > 0:
            self.create_cashback(CashbackCreate(
                user_id=user_id,
                amount=cashback_amount,
                percentage=cashback_amount / amount * 100,
                source="subscription",
                description=f"Cashback for {subscription_tier} subscription"
            ))

        return {
            "payment_id": str(payment.id),
            "amount": amount,
            "cashback_amount": cashback_amount
        }
