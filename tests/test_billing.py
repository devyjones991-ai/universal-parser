import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from billing.service import BillingService, LimitExceededError, SubscriptionRequiredError
from db import Base


@pytest.fixture()
def billing_env():
    engine = create_engine("sqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    service = BillingService(session_factory=TestingSession)
    service.ensure_default_tariffs()
    return service


def test_limit_is_enforced(billing_env):
    service = billing_env
    subscription = service.create_subscription(user_id=1, tariff_code="free")
    service.activate_subscription(subscription.id)

    for _ in range(5):
        service.increment_usage(1, "tracked_products")

    with pytest.raises(LimitExceededError):
        service.increment_usage(1, "tracked_products")


def test_tariff_transition_resets_usage(billing_env):
    service = billing_env
    subscription = service.create_subscription(user_id=2, tariff_code="free")
    service.activate_subscription(subscription.id)
    service.increment_usage(2, "tracked_products", amount=3)

    updated = service.change_tariff(2, "pro")
    report = service.get_usage_report(2)

    assert report["tracked_products"].used == 0
    assert report["tracked_products"].limit == updated.tariff.tracked_products_limit


def test_subscription_required_error(billing_env):
    service = billing_env
    with pytest.raises(SubscriptionRequiredError):
        service.ensure_limit(5, "tracked_products")
