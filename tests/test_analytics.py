import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def analytics_env(tmp_path, monkeypatch):
    db_path = tmp_path / "analytics.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    import db

    importlib.reload(db)
    db.init_db()

    import analytics.service as service

    importlib.reload(service)

    yield db, service


def _seed_history(db, base_time: datetime):
    from db import InventoryHistory, ItemSnapshot, PriceHistory, SessionLocal

    with SessionLocal() as session:
        prices = [100.0, 110.0, 90.0, 120.0]
        stocks = [10, 9, 7, 8]

        for offset, (price, stock) in enumerate(zip(prices, stocks)):
            ts = base_time + timedelta(days=offset)
            snapshot = ItemSnapshot(
                profile_name="demo",
                item_id="item-1",
                name="Demo Item",
                category="Категория",
                price=price,
                currency="RUB",
                stock=stock,
                data_json="{}",
                created_at=ts,
            )
            session.add(snapshot)
            session.flush()

            session.add(
                PriceHistory(
                    snapshot_id=snapshot.id,
                    profile_name="demo",
                    item_id="item-1",
                    price=price,
                    currency="RUB",
                    price_change=None if offset == 0 else price - prices[offset - 1],
                    change_percent=None,
                    created_at=ts,
                )
            )
            session.add(
                InventoryHistory(
                    snapshot_id=snapshot.id,
                    profile_name="demo",
                    item_id="item-1",
                    stock_level=stock,
                    availability="in_stock",
                    created_at=ts,
                )
            )
        session.commit()


def test_build_analytics_report_basic_stats(analytics_env):
    db, service = analytics_env
    base_time = datetime(2024, 1, 1)
    _seed_history(db, base_time)

    report = service.build_analytics_report(
        profile_name="demo",
        item_id="item-1",
        start_date="2024-01-01",
        end_date="2024-01-10",
    )

    assert len(report["price_history"]) == 4
    assert pytest.approx(report["price_stats"]["average"], 0.1) == 105.0
    assert report["price_stats"]["maximum"] == 120.0
    assert report["inventory_stats"]["minimum"] == 7


def test_format_report_text_contains_sections(analytics_env):
    db, service = analytics_env
    base_time = datetime(2024, 2, 1)
    _seed_history(db, base_time)

    report = service.build_analytics_report(
        profile_name="demo",
        item_id="item-1",
        start_date="2024-02-01",
        end_date="2024-02-10",
    )

    text = service.format_report_text(report)

    assert "📈 Аналитика" in text
    assert "💵 Цена" in text
    assert "📦 Склад" in text


def test_export_report_csv(analytics_env):
    db, service = analytics_env
    base_time = datetime(2024, 3, 1)
    _seed_history(db, base_time)

    report = service.build_analytics_report(
        profile_name="demo",
        item_id="item-1",
        start_date="2024-03-01",
        end_date="2024-03-10",
    )

    buffer, filename, mime = service.export_report(report, "csv")

    assert filename.endswith(".csv")
    assert mime == "text/csv"

    df = pd.read_csv(buffer)
    assert len(df) == 4
    assert "price" in df.columns
    assert "stock_level" in df.columns
