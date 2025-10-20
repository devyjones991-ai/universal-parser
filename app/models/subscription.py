"""Модели подписок и биллинга"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base

class SubscriptionTier(str, Enum):
    """Уровни подписки"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class PaymentStatus(str, Enum):
    """Статусы платежей"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class Subscription(Base):
    """Модель подписки пользователя"""
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tier = Column(String(20), nullable=False, default=SubscriptionTier.FREE)
    status = Column(String(20), nullable=False, default="active")
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")

    def is_active(self) -> bool:
        """Проверка активности подписки"""
        if self.status != "active":
            return False
        if self.end_date and self.end_date < datetime.utcnow():
            return False
        return True

    def days_remaining(self) -> int:
        """Количество дней до окончания подписки"""
        if not self.end_date:
            return 999999  # Бессрочная подписка
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)

class Payment(Base):
    """Модель платежа"""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), nullable=False, default=PaymentStatus.PENDING)
    payment_method = Column(String(50), nullable=False)  # stripe, paypal, etc.
    external_id = Column(String(255), nullable=True)  # ID в платежной системе
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

class Cashback(Base):
    """Модель кэшбека"""
    __tablename__ = "cashbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)  # Процент кэшбека
    source = Column(String(50), nullable=False)  # subscription, referral, bonus
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, paid
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    # Связи
    user = relationship("User", back_populates="cashbacks")

class Referral(Base):
    """Модель реферальной программы"""
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referred_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reward_amount = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending, completed, paid
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Связи
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_sent")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referrals_received")

class SubscriptionPlan(Base):
    """Модель тарифных планов"""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    tier = Column(String(20), nullable=False)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    features = Column(Text, nullable=True)  # JSON список функций
    limits = Column(Text, nullable=True)  # JSON ограничений
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_features_list(self) -> list:
        """Получить список функций"""
        if not self.features:
            return []
        return json.loads(self.features)

    def get_limits_dict(self) -> dict:
        """Получить словарь ограничений"""
        if not self.limits:
            return {}
        return json.loads(self.limits)
