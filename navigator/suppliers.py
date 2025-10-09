"""Утилиты для поиска поставщиков в открытых каталогах.

Модуль реализует гибкую систему источников с поддержкой HTTP API и
HTML-страниц, а также многоуровневое кэширование запросов для снижения
нагрузки на внешние сервисы.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

__all__ = [
    "CatalogSource",
    "SupplierSearchResult",
    "OPEN_CATALOGS",
    "search_suppliers",
    "clear_supplier_cache",
]

_CACHE_TTL_SECONDS = 60 * 30  # 30 минут по умолчанию
_SUPPLIER_CACHE: Dict[str, Tuple[float, "SupplierSearchResult"]] = {}
_CACHE_LOCK = asyncio.Lock()


def _now() -> float:
    return time.monotonic()


@dataclass(slots=True)
class CatalogSource:
    """Описание источника данных для поиска поставщиков."""

    name: str
    method: str  # "api" или "html"
    url: str
    query_param: str = "q"
    data_path: Optional[Iterable[str]] = None
    item_selector: Optional[str] = None
    fields: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def cache_key(self, query: str, page: int, limit: int) -> str:
        return f"{self.name}:{query}:{page}:{limit}:{self.method}"


@dataclass(slots=True)
class SupplierSearchResult:
    """Результат запроса поиска поставщиков."""

    query: str
    source: CatalogSource
    results: List[Dict[str, Any]]
    page: int
    limit: int
    fetched_at: float
    cached: bool = False

    @property
    def total(self) -> int:
        return len(self.results)


OPEN_CATALOGS: Dict[str, CatalogSource] = {
    "demo_api": CatalogSource(
        name="demo_api",
        method="api",
        url="https://example.com/api/suppliers",
        query_param="search",
        data_path=("data", "items"),
        fields={"name": "name", "category": "category", "location": "city"},
    ),
    "demo_html": CatalogSource(
        name="demo_html",
        method="html",
        url="https://example.com/catalog?q={query}",
        item_selector="div.card",
        fields={"name": ".card-title", "category": ".card-category", "location": ".card-city"},
    ),
}


async def _fetch_api_catalog(
    client: httpx.AsyncClient,
    source: CatalogSource,
    query: str,
    page: int,
    limit: int,
) -> List[Dict[str, Any]]:
    params = dict(source.extra_params)
    params[source.query_param] = query
    params.update({"page": page, "limit": limit})
    response = await client.get(source.url, params=params)
    response.raise_for_status()
    data: Any = response.json()

    if source.data_path:
        for key in source.data_path:
            if isinstance(data, dict):
                data = data.get(key, [])
            else:
                raise ValueError("Некорректный путь к данным в источнике")

    if not isinstance(data, list):
        raise ValueError("Ответ API должен быть списком элементов")

    mapped: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        mapped.append({field: item.get(source_field) for field, source_field in source.fields.items()})
    return mapped


def _parse_html_catalog(html: str, source: CatalogSource) -> List[Dict[str, Any]]:
    if not source.item_selector:
        raise ValueError("Для HTML-источника необходимо определить item_selector")

    soup = BeautifulSoup(html, "lxml")
    items = soup.select(source.item_selector)
    results: List[Dict[str, Any]] = []

    for item in items:
        record: Dict[str, Any] = {}
        for field, selector in source.fields.items():
            element = item.select_one(selector)
            if element is None:
                continue
            if field in source.attributes:
                record[field] = element.get(source.attributes[field])
            else:
                record[field] = element.get_text(strip=True)
        if record:
            results.append(record)
    return results


async def _fetch_html_catalog(
    client: httpx.AsyncClient,
    source: CatalogSource,
    query: str,
    page: int,
    limit: int,
) -> List[Dict[str, Any]]:
    url = source.url.format(query=query, page=page, limit=limit)
    params = dict(source.extra_params)
    if "{" not in source.url:
        params[source.query_param] = query
    response = await client.get(url, params=params)
    response.raise_for_status()
    html = response.text
    data = _parse_html_catalog(html, source)
    if limit:
        return data[:limit]
    return data


async def _load_from_source(
    source: CatalogSource,
    query: str,
    page: int,
    limit: int,
    client: Optional[httpx.AsyncClient] = None,
) -> List[Dict[str, Any]]:
    own_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
        own_client = True
    try:
        if source.method == "api":
            return await _fetch_api_catalog(client, source, query, page, limit)
        if source.method == "html":
            return await _fetch_html_catalog(client, source, query, page, limit)
        raise ValueError(f"Неизвестный метод источника: {source.method}")
    finally:
        if own_client:
            await client.aclose()


async def search_suppliers(
    query: str,
    source_name: str,
    *,
    page: int = 1,
    limit: int = 10,
    refresh: bool = False,
    catalogs: Optional[Dict[str, CatalogSource]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> SupplierSearchResult:
    """Выполняет поиск поставщиков с кэшированием результата."""

    if not query.strip():
        raise ValueError("Поисковый запрос не может быть пустым")

    sources = catalogs or OPEN_CATALOGS
    if source_name not in sources:
        raise KeyError(f"Источник '{source_name}' не найден")

    source = sources[source_name]
    cache_key = source.cache_key(query=query.strip(), page=page, limit=limit)

    async with _CACHE_LOCK:
        if not refresh and cache_key in _SUPPLIER_CACHE:
            timestamp, cached_result = _SUPPLIER_CACHE[cache_key]
            if _now() - timestamp < _CACHE_TTL_SECONDS:
                cached_result.cached = True
                return cached_result
            _SUPPLIER_CACHE.pop(cache_key, None)

    results = await _load_from_source(source, query.strip(), page, limit, client)
    search_result = SupplierSearchResult(
        query=query.strip(),
        source=source,
        results=results,
        page=page,
        limit=limit,
        fetched_at=_now(),
        cached=False,
    )

    async with _CACHE_LOCK:
        _SUPPLIER_CACHE[cache_key] = (search_result.fetched_at, search_result)
    return search_result


async def clear_supplier_cache() -> None:
    """Полностью очищает кэш результатов поиска поставщиков."""

    async with _CACHE_LOCK:
        _SUPPLIER_CACHE.clear()
