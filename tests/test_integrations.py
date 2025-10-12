from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db
from alerts.checker import AlertChecker
from integrations.directories import DirectorySyncService
from integrations.news import NewsIntegration


@pytest.fixture(autouse=True)
def setup_database(tmp_path):
    test_db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{test_db_path}", future=True)
    Session = sessionmaker(bind=engine)

    db.engine = engine
    db.SessionLocal = Session
    db.init_db()

    yield

    db.Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_news_integration_fetches_and_caches():
    call_counter = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        call_counter["count"] += 1
        payload = {
            "items": [
                {
                    "title": "Test news",
                    "url": "https://example.com/news",
                    "summary": "Details",
                    "published_at": "2024-01-01T10:00:00",
                    "source": "API",
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    integration = NewsIntegration(
        sources=[
            {
                "name": "TestAPI",
                "type": "api",
                "url": "https://example.com/news",
                "params": {},
                "data_path": "items",
                "field_map": {
                    "title": "title",
                    "url": "url",
                    "summary": "summary",
                    "published_at": "published_at",
                    "source": "source",
                },
            }
        ],
        client_factory=lambda: httpx.AsyncClient(transport=transport),
        cache_ttl_minutes=120,
    )

    first = await integration.fetch_news("retail", "moscow", limit=5)
    second = await integration.fetch_news("retail", "moscow", limit=5)

    assert call_counter["count"] == 1
    assert len(first) == 1
    assert first == second
    assert first[0]["title"] == "Test news"
    assert first[0]["niche"] == "retail"
    assert first[0]["region"] == "moscow"


@pytest.mark.asyncio
async def test_directory_sync_service_caches_entries():
    call_counter = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        call_counter["count"] += 1
        payload = {
            "entries": [
                {
                    "name": "Supplier A",
                    "contacts": {"email": "a@example.com"},
                    "details": {"rating": 5},
                    "updated_at": "2024-02-01T12:00:00",
                }
            ]
        }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    service = DirectorySyncService(
        sources=[
            {
                "name": "DirectoryAPI",
                "type": "api",
                "url": "https://example.com/directories",
                "params": {},
                "data_path": "entries",
                "field_map": {
                    "name": "name",
                    "contact_info": "contacts",
                    "metadata": "details",
                    "updated_at": "updated_at",
                },
            }
        ],
        client_factory=lambda: httpx.AsyncClient(transport=transport),
        cache_ttl_hours=24,
    )

    first = await service.sync("supplier", "retail", "moscow")
    second = await service.sync("supplier", "retail", "moscow")

    assert call_counter["count"] == 1
    assert len(first) == 1
    assert first == second
    assert first[0]["name"] == "Supplier A"
    assert first[0]["metadata"]["rating"] == 5


@pytest.mark.asyncio
async def test_alert_checker_builds_digest():
    news_counter = {"count": 0}
    directory_counter = {"count": 0}

    async def news_handler(request: httpx.Request) -> httpx.Response:
        news_counter["count"] += 1
        payload = {
            "items": [
                {
                    "title": "Important update",
                    "url": "https://example.com/important",
                    "summary": "Summary",
                    "published_at": "2024-03-10T08:00:00",
                }
            ]
        }
        return httpx.Response(200, json=payload)

    async def directory_handler(request: httpx.Request) -> httpx.Response:
        directory_counter["count"] += 1
        payload = {
            "entries": [
                {
                    "name": "Courier B",
                    "contacts": {"phone": "+70000000000"},
                    "details": {"vehicles": 10},
                    "updated_at": "2024-03-09T09:00:00",
                }
            ]
        }
        return httpx.Response(200, json=payload)

    news_transport = httpx.MockTransport(news_handler)
    directory_transport = httpx.MockTransport(directory_handler)

    news_integration = NewsIntegration(
        sources=[
            {
                "name": "DigestNews",
                "type": "api",
                "url": "https://example.com/digest/news",
                "params": {},
                "data_path": "items",
                "field_map": {
                    "title": "title",
                    "url": "url",
                    "summary": "summary",
                    "published_at": "published_at",
                },
            }
        ],
        client_factory=lambda: httpx.AsyncClient(transport=news_transport),
        cache_ttl_minutes=120,
    )

    directory_service = DirectorySyncService(
        sources=[
            {
                "name": "DigestDirectory",
                "type": "api",
                "url": "https://example.com/digest/directories",
                "params": {},
                "data_path": "entries",
                "field_map": {
                    "name": "name",
                    "contact_info": "contacts",
                    "metadata": "details",
                    "updated_at": "updated_at",
                },
            }
        ],
        client_factory=lambda: httpx.AsyncClient(transport=directory_transport),
        cache_ttl_hours=24,
    )

    checker = AlertChecker(
        news_integration=news_integration,
        directory_service=directory_service,
    )

    digest = await checker.build_digest("retail", "moscow", directory_types=("delivery",))

    assert news_counter["count"] == 1
    assert directory_counter["count"] == 1
    assert digest["news"][0]["title"] == "Important update"
    assert digest["directories"]["delivery"]["count"] == 1
