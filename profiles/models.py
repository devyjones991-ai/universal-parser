"""Модели биллинга и тарифов."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionStatus(enum.Enum):
    """Статусы подписки."""

    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(enum.Enum):
    """Статусы платежей."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tariff(Base):
    """Тариф с лимитами и стоимостью."""

    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    monthly_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tracked_products_limit: Mapped[int] = mapped_column(Integer, default=0)
    alerts_limit: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="tariff"
    )

    def get_limit(self, metric: str) -> int:
        """Возвращает лимит по названию метрики."""

        mapping = {
            "tracked_products": self.tracked_products_limit,
            "alerts": self.alerts_limit,
        }
        return mapping.get(metric, 0)


class Subscription(Base):
    """Подписка пользователя на тариф."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    active_until: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False)
    usage: Mapped[Dict[str, int]] = mapped_column(JSON, default=dict)

    tariff: Mapped[Tariff] = relationship("Tariff", back_populates="subscriptions")
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="subscription", cascade="all, delete-orphan"
    )

    def get_usage(self, metric: str) -> int:
        """Возвращает текущее значение использования по метрике."""

        return int(self.usage.get(metric, 0))

    def set_usage(self, metric: str, value: int) -> None:
        """Сохраняет использование по метрике."""

        updated = dict(self.usage or {})
        updated[metric] = value
        self.usage = updated


class Payment(Base):
    """Информация о платеже по подписке."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="RUB")
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    confirmation_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    extra: Mapped[Dict[str, str]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)

    subscription: Mapped[Subscription] = relationship(
        "Subscription", back_populates="payments"
    )

