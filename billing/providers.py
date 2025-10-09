"""Интеграции платёжных провайдеров."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from profiles.models import Payment, PaymentStatus, Subscription


class PaymentProvider:
    """Базовый интерфейс платёжного провайдера."""

    name = "base"

    def create_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        raise NotImplementedError

    def confirm_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        raise NotImplementedError


class ManualActivationProvider(PaymentProvider):
    """Ручная активация администратором."""

    name = "manual"

    def create_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.external_id = f"manual-{subscription.id}"
        payment.status = PaymentStatus.PENDING
        return payment

    def confirm_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = datetime.now(timezone.utc)
        return payment


class YooKassaProvider(PaymentProvider):
    """Простейшая имитация интеграции с YooKassa."""

    name = "yookassa"

    def create_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.external_id = str(uuid.uuid4())
        payment.status = PaymentStatus.PENDING
        payment.confirmation_url = (
            payload.get("return_url") if payload else "https://pay.yookassa.ru/mock"
        )
        payment.extra = payload or {}
        return payment

    def confirm_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = datetime.now(timezone.utc)
        return payment


class CloudPaymentsProvider(PaymentProvider):
    """Простейшая имитация CloudPayments."""

    name = "cloudpayments"

    def create_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.external_id = str(uuid.uuid4())
        payment.status = PaymentStatus.PENDING
        payment.confirmation_url = (
            payload.get("return_url") if payload else "https://cloudpayments.ru/mock"
        )
        payment.extra = payload or {}
        return payment

    def confirm_payment(
        self, subscription: Subscription, payment: Payment, payload: Optional[Dict] = None
    ) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        payment.confirmed_at = datetime.now(timezone.utc)
        return payment


PROVIDERS: Dict[str, PaymentProvider] = {
    ManualActivationProvider.name: ManualActivationProvider(),
    YooKassaProvider.name: YooKassaProvider(),
    CloudPaymentsProvider.name: CloudPaymentsProvider(),
}


def get_provider(name: str) -> PaymentProvider:
    """Возвращает провайдера по названию."""

    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Неизвестный провайдер '{name}'")
    return provider

