"""Сервис биллинга: тарифы, подписки и лимиты."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from billing.providers import get_provider
from db import SessionLocal
from profiles.models import (
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
    Tariff,
)


class SubscriptionRequiredError(Exception):
    """Нет активной подписки."""


class LimitExceededError(Exception):
    """Превышен лимит использования."""


@dataclass
class UsageInfo:
    metric: str
    used: int
    limit: int


class BillingService:
    """Высокоуровневый сервис управления тарифами и лимитами."""

    DEFAULT_PERIOD_DAYS = 30

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    @contextmanager
    def session(self) -> Iterable[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def ensure_default_tariffs(self) -> None:
        """Создаёт дефолтные тарифы, если их нет."""

        with self.session() as session:
            count = session.scalar(select(func.count()).select_from(Tariff))
            if count and count > 0:
                return

            tariffs = [
                Tariff(
                    code="free",
                    name="Бесплатный",
                    description="Базовые возможности с ограничением на мониторинг",
                    monthly_price=0,
                    tracked_products_limit=5,
                    alerts_limit=5,
                ),
                Tariff(
                    code="pro",
                    name="Pro",
                    description="Расширенный мониторинг",
                    monthly_price=2990,
                    tracked_products_limit=50,
                    alerts_limit=50,
                ),
            ]
            session.add_all(tariffs)

    def list_tariffs(self) -> List[Tariff]:
        with self.session() as session:
            tariffs = list(session.scalars(select(Tariff).where(Tariff.is_active.is_(True))))
            for tariff in tariffs:
                session.expunge(tariff)
            return tariffs

    def get_tariff(self, code: str) -> Tariff:
        with self.session() as session:
            tariff = session.scalar(select(Tariff).where(Tariff.code == code))
            if not tariff:
                raise NoResultFound(f"Тариф '{code}' не найден")
            session.expunge(tariff)
            return tariff

    def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        with self.session() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                select(Subscription)
                .where(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    (Subscription.active_until.is_(None) | (Subscription.active_until >= now)),
                )
                .order_by(Subscription.updated_at.desc())
            )
            subscription = session.scalar(stmt)
            if subscription:
                subscription.tariff  # загрузка тарифа до отделения
                subscription.tariff.tracked_products_limit
                subscription.tariff.alerts_limit
                session.expunge(subscription)
            return subscription

    def create_subscription(
        self, user_id: int, tariff_code: str, provider_name: str = "manual", payload: Optional[Dict] = None
    ) -> Subscription:
        with self.session() as session:
            tariff = session.scalar(select(Tariff).where(Tariff.code == tariff_code))
            if not tariff:
                raise NoResultFound(f"Тариф '{tariff_code}' не найден")

            subscription = Subscription(user_id=user_id, tariff=tariff)
            session.add(subscription)
            session.flush()

            payment = Payment(
                subscription=subscription,
                amount=tariff.monthly_price,
                provider=provider_name,
            )
            provider = get_provider(provider_name)
            provider.create_payment(subscription, payment, payload)
            session.add(payment)
            session.flush()

            session.refresh(subscription)
            subscription.tariff  # ensure relationship loaded
            subscription.tariff.tracked_products_limit
            subscription.tariff.alerts_limit
            session.expunge(subscription)
            return subscription

    def activate_subscription(
        self, subscription_id: int, duration_days: int = DEFAULT_PERIOD_DAYS
    ) -> Subscription:
        with self.session() as session:
            subscription = session.get(Subscription, subscription_id)
            if not subscription:
                raise NoResultFound("Подписка не найдена")

            now = datetime.now(timezone.utc)
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.started_at = now
            subscription.active_until = now + timedelta(days=duration_days)
            subscription.usage = {}

            for payment in subscription.payments:
                if payment.status == PaymentStatus.PENDING:
                    provider = get_provider(payment.provider)
                    provider.confirm_payment(subscription, payment)

            session.flush()
            session.refresh(subscription)
            subscription.tariff
            subscription.tariff.tracked_products_limit
            subscription.tariff.alerts_limit
            session.expunge(subscription)
            return subscription

    def change_tariff(self, user_id: int, new_tariff_code: str) -> Subscription:
        with self.session() as session:
            subscription = session.scalar(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                )
            )
            if not subscription:
                raise SubscriptionRequiredError("Нет активной подписки")

            tariff = session.scalar(select(Tariff).where(Tariff.code == new_tariff_code))
            if not tariff:
                raise NoResultFound(f"Тариф '{new_tariff_code}' не найден")

            subscription.tariff = tariff
            subscription.usage = {}
            subscription.updated_at = datetime.now(timezone.utc)

            session.flush()
            session.refresh(subscription)
            subscription.tariff
            subscription.tariff.tracked_products_limit
            subscription.tariff.alerts_limit
            session.expunge(subscription)
            return subscription

    def get_latest_payment(self, subscription_id: int) -> Optional[Payment]:
        with self.session() as session:
            payment = session.scalar(
                select(Payment)
                .where(Payment.subscription_id == subscription_id)
                .order_by(Payment.created_at.desc())
            )
            if payment:
                session.expunge(payment)
            return payment

    def _require_active_subscription(self, user_id: int, session: Session) -> Subscription:
        now = datetime.now(timezone.utc)
        subscription = session.scalar(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                (Subscription.active_until.is_(None) | (Subscription.active_until >= now)),
            )
            .order_by(Subscription.updated_at.desc())
        )
        if not subscription:
            raise SubscriptionRequiredError("Необходимо активировать подписку")
        return subscription

    def ensure_limit(self, user_id: int, metric: str, amount: int = 1) -> None:
        with self.session() as session:
            subscription = self._require_active_subscription(user_id, session)
            limit = subscription.tariff.get_limit(metric)
            if limit == 0:
                return
            used = subscription.get_usage(metric)
            if used + amount > limit:
                raise LimitExceededError(
                    f"Лимит по '{metric}' исчерпан: {used}/{limit}"
                )

    def increment_usage(self, user_id: int, metric: str, amount: int = 1) -> UsageInfo:
        with self.session() as session:
            subscription = self._require_active_subscription(user_id, session)
            limit = subscription.tariff.get_limit(metric)
            used = subscription.get_usage(metric)
            new_value = used + amount
            if limit and new_value > limit:
                raise LimitExceededError(
                    f"Лимит по '{metric}' исчерпан: {used}/{limit}"
                )
            subscription.set_usage(metric, new_value)
            session.flush()
            return UsageInfo(metric=metric, used=new_value, limit=limit)

    def get_usage_report(self, user_id: int) -> Dict[str, UsageInfo]:
        with self.session() as session:
            subscription = self._require_active_subscription(user_id, session)
            limits = {
                "tracked_products": subscription.tariff.get_limit("tracked_products"),
                "alerts": subscription.tariff.get_limit("alerts"),
            }
            usage = {
                metric: UsageInfo(metric=metric, used=subscription.get_usage(metric), limit=limit)
                for metric, limit in limits.items()
            }
            return usage

