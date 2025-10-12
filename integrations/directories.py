"""Интеграции для обновления справочников поставщиков и доставщиков."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional

import httpx

from db import cache_directory_entries, get_directory_entries

DEFAULT_DIRECTORY_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "MockDirectoryAPI",
        "type": "api",
        "url": "https://example.com/api/directories",
        "params": {
            "category": "{entry_type}",
            "niche": "{niche}",
            "region": "{region}",
        },
        "data_path": "entries",
        "field_map": {
            "name": "name",
            "contact_info": "contacts",
            "metadata": "details",
            "updated_at": "updated_at",
        },
    }
]


class DirectorySyncService:
    """Сервис синхронизации справочных данных."""

    def __init__(
        self,
        sources: Optional[Iterable[Dict[str, Any]]] = None,
        cache_ttl_hours: int = 12,
        client_factory: Optional[Callable[[], httpx.AsyncClient]] = None,
    ) -> None:
        self.sources = list(sources or DEFAULT_DIRECTORY_SOURCES)
        self.cache_ttl_hours = cache_ttl_hours
        self._client_factory = client_factory or (lambda: httpx.AsyncClient(timeout=10.0))

    async def sync(
        self, entry_type: str, niche: str, region: str, *, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        cached = get_directory_entries(
            entry_type=entry_type,
            niche=niche,
            region=region,
            ttl_hours=self.cache_ttl_hours,
        )
        if cached:
            return cached[:limit] if limit else cached

        aggregated: List[Dict[str, Any]] = []
        async with self._client_factory() as client:  # type: ignore[func-returns-value]
            for source in self.sources:
                if source.get("type") != "api":
                    continue
                try:
                    aggregated.extend(
                        await self._fetch_from_api(
                            client, source, entry_type=entry_type, niche=niche, region=region
                        )
                    )
                except Exception:
                    continue

        normalized = self._normalize_items(
            aggregated, entry_type=entry_type, niche=niche, region=region
        )
        if normalized:
            cache_directory_entries(
                entry_type=entry_type, niche=niche, region=region, items=normalized
            )
        if limit:
            return normalized[:limit]
        return normalized

    async def _fetch_from_api(
        self,
        client: httpx.AsyncClient,
        source: Dict[str, Any],
        *,
        entry_type: str,
        niche: str,
        region: str,
    ) -> List[Dict[str, Any]]:
        params = {}
        for key, value in source.get("params", {}).items():
            if isinstance(value, str):
                params[key] = value.format(entry_type=entry_type, niche=niche, region=region)
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
            items.append(item)
        return items

    def _normalize_items(
        self,
        items: Iterable[Dict[str, Any]],
        *,
        entry_type: str,
        niche: str,
        region: str,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for raw in items:
            name = raw.get("name")
            if not name:
                continue

            contact_info = raw.get("contact_info")
            metadata = raw.get("metadata") or {}
            updated_at = self._parse_datetime(raw.get("updated_at"))

            normalized.append(
                {
                    "name": name,
                    "entry_type": entry_type,
                    "niche": niche,
                    "region": region,
                    "contact_info": contact_info,
                    "metadata": metadata,
                    "updated_at": updated_at,
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

        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
            try:
                return datetime.strptime(str(value), fmt).isoformat()
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(str(value)).isoformat()
        except ValueError:
            return datetime.utcnow().isoformat()
