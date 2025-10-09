import asyncio
import sys
from pathlib import Path

import httpx
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from navigator.suppliers import (
    CatalogSource,
    clear_supplier_cache,
    search_suppliers,
)
from navigator.logistics import (
    Carrier,
    add_carrier,
    find_carriers,
    get_carrier_by_id,
    initialise_storage,
    bulk_upsert_carriers,
)
from navigator.guides import get_section, update_section, get_paginated_faq


@pytest.mark.asyncio
async def test_search_suppliers_uses_cache(tmp_path):
    await clear_supplier_cache()
    source = CatalogSource(
        name="test_api",
        method="api",
        url="https://example.com/api",
        query_param="q",
        data_path=("data", "items"),
        fields={"name": "title", "category": "type", "location": "city"},
    )

    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        data = {
            "data": {
                "items": [
                    {"title": "Поставщик", "type": "Оборудование", "city": "Москва"}
                ]
            }
        }
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result1 = await search_suppliers(
            "кабель",
            "test_api",
            catalogs={"test_api": source},
            client=client,
        )
        assert result1.results[0]["name"] == "Поставщик"
        assert calls == 1

        result2 = await search_suppliers(
            "кабель",
            "test_api",
            catalogs={"test_api": source},
            client=client,
        )
        assert result2.cached is True
        assert calls == 1

        result3 = await search_suppliers(
            "кабель",
            "test_api",
            catalogs={"test_api": source},
            client=client,
            refresh=True,
        )
        assert result3.cached is False
        assert calls == 2


@pytest.mark.asyncio
async def test_search_suppliers_html_source():
    await clear_supplier_cache()
    source = CatalogSource(
        name="html",
        method="html",
        url="https://example.com/list?q={query}",
        item_selector="div.item",
        fields={"name": "h3", "category": "span.cat"},
    )

    html = """
    <div class='item'>
        <h3>Компания А</h3>
        <span class='cat'>Металл</span>
    </div>
    <div class='item'>
        <h3>Компания Б</h3>
        <span class='cat'>Пластик</span>
    </div>
    """

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await search_suppliers(
            "металл",
            "html",
            catalogs={"html": source},
            client=client,
        )
        names = [item["name"] for item in result.results]
        assert names == ["Компания А", "Компания Б"]


def test_logistics_storage_operations(tmp_path: Path):
    db_path = tmp_path / "logistics.db"
    initialise_storage(db_path)

    carrier = Carrier(
        id=None,
        name="СеверТранс",
        regions=["Москва", "СПб"],
        vehicle_types=["Тягач"],
        phone="+7 900 123-45-67",
        email="info@example.com",
        rating=4.8,
    )
    carrier_id = add_carrier(carrier, db_path)
    assert carrier_id > 0

    carriers = find_carriers(query="Север", regions=["Москва"], min_rating=4.0, db_path=db_path)
    assert len(carriers) == 1
    assert carriers[0].name == "СеверТранс"

    fetched = get_carrier_by_id(carrier_id, db_path)
    assert fetched is not None
    assert fetched.email == "info@example.com"

    bulk_upsert_carriers(
        [
            Carrier(
                id=None,
                name="СеверТранс",
                regions=["Москва"],
                vehicle_types=["Тягач"],
                phone="+7 900 123-45-67",
                email="log@example.com",
                rating=5.0,
            ),
            Carrier(
                id=None,
                name="ЮгКарго",
                regions=["Ростов"],
                vehicle_types=["Грузовик"],
                rating=3.5,
            ),
        ],
        db_path,
    )

    carriers_updated = find_carriers(limit=10, db_path=db_path)
    assert {c.name for c in carriers_updated} == {"СеверТранс", "ЮгКарго"}
    updated = get_carrier_by_id(carrier_id, db_path)
    assert updated and updated.email == "log@example.com"


def test_guides_update_and_pagination():
    roadmap = get_section("roadmap")
    original_content = list(roadmap.content)

    try:
        updated = update_section("roadmap", ["Новая цель"])
        assert "Новая цель" in updated.content
    finally:
        update_section("roadmap", original_content)

    items, pages = get_paginated_faq(page=1, per_page=1)
    assert len(items) == 2  # вопрос и ответ
    assert pages >= 1
