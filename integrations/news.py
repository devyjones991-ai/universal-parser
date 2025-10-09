"""Модуль интеграции с внешними источниками новостей."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional

import httpx
from bs4 import BeautifulSoup

from db import cache_news_items, get_cached_news

DEFAULT_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "MockNewsAPI",
        "type": "api",
        "url": "https://example.com/api/news",
        "params": {"niche": "{niche}", "region": "{region}"},
        "data_path": "items",
        "field_map": {
            "title": "title",
            "url": "url",
            "summary": "summary",
            "published_at": "published_at",
            "source": "source",
        },
    },
    {
        "name": "MockNewsHTML",
        "type": "html",
        "url": "https://example.com/{region}/{niche}/news",
        "selectors": {
            "items": ".news-item",
            "title": ".title",
            "url": ".title a",
            "summary": ".summary",
            "date": ".date",
        },
        "attribute_fields": {"url": "href"},
    },
]


class NewsIntegration:
    """Загрузка и нормализация внешних новостей."""

    def __init__(
        self,
        sources: Optional[Iterable[Dict[str, Any]]] = None,
        cache_ttl_minutes: int = 60,
        client_factory: Optional[Callable[[], httpx.AsyncClient]] = None,
    ) -> None:
        self.sources = list(sources or DEFAULT_SOURCES)
        self.cache_ttl_minutes = cache_ttl_minutes
        self._client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=10.0))

    async def fetch_news(self, niche: str, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает список нормализованных новостей с учётом кэша."""
        cached = get_cached_news(niche=niche, region=region, ttl_minutes=self.cache_ttl_minutes)
        if cached:
            return cached[:limit]

        fresh_items: List[Dict[str, Any]] = []
        async with self._client_factory() as client:  # type: ignore[func-returns-value]
            for source in self.sources:
                try:
                    if source.get("type") == "api":
                        fresh_items.extend(
                            await self._fetch_from_api(client, source, niche=niche, region=region)
                        )
                    elif source.get("type") == "html":
                        fresh_items.extend(
                            await self._fetch_from_html(client, source, niche=niche, region=region)
                        )
                except Exception:
                    # Падаем молча: источник может быть временно недоступен.
                    continue

        normalized = self._normalize_items(fresh_items, niche=niche, region=region)
        if normalized:
            cache_news_items(niche=niche, region=region, items=normalized)
        return normalized[:limit]

    async def _fetch_from_api(
        self,
        client: httpx.AsyncClient,
        source: Dict[str, Any],
        *,
        niche: str,
        region: str,
    ) -> List[Dict[str, Any]]:
        params = {}
        for key, value in source.get("params", {}).items():
            if isinstance(value, str):
                params[key] = value.format(niche=niche, region=region)
            else:
                params[key] = value

        response = await client.get(source["url"], params=params)
        response.raise_for_status()
        payload = response.json()

        for segment in source.get("data_path", "").split("."):
            if not segment:
                continue
            payload = payload.get(segment, [])

        items = []
        field_map = source.get("field_map", {})
        for raw in payload:
            item = {}
            for target_field, source_field in field_map.items():
                item[target_field] = raw.get(source_field)
            item.setdefault("source", source.get("name"))
            items.append(item)
        return items

    async def _fetch_from_html(
        self,
        client: httpx.AsyncClient,
        source: Dict[str, Any],
        *,
        niche: str,
        region: str,
    ) -> List[Dict[str, Any]]:
        url = source["url"].format(niche=niche, region=region)
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        selectors = source.get("selectors", {})
        attribute_fields = source.get("attribute_fields", {})
        items = []

        for element in soup.select(selectors.get("items", "")):
            item: Dict[str, Any] = {"source": source.get("name")}
            title_el = element.select_one(selectors.get("title", ""))
            if title_el:
                item["title"] = title_el.get_text(strip=True)
            url_el = element.select_one(selectors.get("url", ""))
            if url_el:
                attr = attribute_fields.get("url")
                item["url"] = url_el.get(attr) if attr else url_el.get_text(strip=True)
            summary_el = element.select_one(selectors.get("summary", ""))
            if summary_el:
                item["summary"] = summary_el.get_text(strip=True)
            date_el = element.select_one(selectors.get("date", ""))
            if date_el:
                item["published_at"] = date_el.get_text(strip=True)
            items.append(item)
        return items

    def _normalize_items(
        self, items: Iterable[Dict[str, Any]], *, niche: str, region: str
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for raw in items:
            title = raw.get("title")
            url = raw.get("url")
            if not title or not url:
                continue

            summary = raw.get("summary") or ""
            published_at = self._parse_datetime(raw.get("published_at"))
            source = raw.get("source") or "External"

            normalized.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "source": source,
                    "published_at": published_at,
                    "niche": niche,
                    "region": region,
                }
            )
        return normalized

    @staticmethod
    def _parse_datetime(value: Any) -> str:
        if value is None:
            return datetime.utcnow().isoformat()

        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value).isoformat()

        if isinstance(value, datetime):
            return value.isoformat()

        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(str(value), fmt).isoformat()
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(str(value)).isoformat()
        except ValueError:
            return datetime.utcnow().isoformat()
