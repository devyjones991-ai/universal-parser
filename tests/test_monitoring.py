import asyncio

import pytest

from profiles.monitoring import MonitoringStorage, UserTrackedItem
from profiles.import_export import (
    export_items,
    export_items_to_clipboard,
    import_items_from_clipboard,
    import_items_from_file,
)
from alerts.checker import process_monitoring_batch


@pytest.fixture
def sample_items() -> list[UserTrackedItem]:
    return [
        UserTrackedItem(
            user_id=1,
            profile="demo",
            query="item-1",
            sku="SKU-1",
            title="Первый",
            sources=["site", "email"],
        ),
        UserTrackedItem(
            user_id=2,
            profile="demo",
            query="item-2",
            sources=["feed"],
        ),
    ]


def test_export_import_roundtrip_excel(sample_items, tmp_path):
    filename, payload = export_items(sample_items, fmt="xlsx")
    assert filename.endswith(".xlsx")

    imported = import_items_from_file(payload, filename, default_user_id=None)
    assert len(imported) == len(sample_items)
    assert imported[0].sku == sample_items[0].sku
    assert imported[1].user_id == sample_items[1].user_id


def test_export_import_clipboard_csv(sample_items):
    csv_text = export_items_to_clipboard(sample_items, fmt="csv")
    imported = import_items_from_clipboard(csv_text, fmt="csv")
    assert {item.query for item in imported} == {item.query for item in sample_items}


def test_storage_add_remove(tmp_path):
    storage = MonitoringStorage(path=tmp_path / "monitor.json")
    item = UserTrackedItem(
        user_id=77,
        profile="demo",
        query="abc",
        title="Тест",
        sources=["rss"],
    )

    assert storage.add_item(item) is True
    assert storage.add_item(item) is False
    listed = storage.list_user_items(77)
    assert len(listed) == 1
    assert listed[0].title == "Тест"

    assert storage.remove_item(77, "demo", "abc") is True
    assert storage.list_user_items(77) == []


class DummyParser:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def parse_by_profile(self, profile_name: str, **kwargs):
        query = kwargs.get("query")
        if query == "bad":
            raise ValueError("ошибка профиля")
        return [{"profile": profile_name, "query": query}]


@pytest.mark.asyncio
async def test_process_monitoring_batch(tmp_path):
    storage = MonitoringStorage(path=tmp_path / "monitor.json")
    storage.replace_user_items(
        1,
        [
            UserTrackedItem(user_id=1, profile="demo", query="good", title="Хороший"),
            UserTrackedItem(user_id=1, profile="demo", query="bad", title="Плохой"),
        ],
    )
    storage.replace_user_items(
        2,
        [UserTrackedItem(user_id=2, profile="demo", query="extra", sources=["api"] )],
    )

    notifications = await process_monitoring_batch(
        storage=storage,
        parser_factory=lambda: DummyParser(),
    )

    assert 1 in notifications and 2 in notifications
    assert "Хороший" in notifications[1]
    assert "❌" in notifications[1]
    assert "источники" in notifications[2]


@pytest.mark.asyncio
async def test_process_monitoring_batch_empty(tmp_path):
    storage = MonitoringStorage(path=tmp_path / "monitor.json")
    notifications = await process_monitoring_batch(
        storage=storage,
        parser_factory=lambda: DummyParser(),
    )
    assert notifications == {}
