from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

from parser import UniversalParser
from profiles.monitoring import MonitoringStorage, UserTrackedItem


@dataclass
class MonitoringResult:
    item: UserTrackedItem
    results: List[Dict]
    error: Optional[str] = None


async def _process_item(parser: UniversalParser, item: UserTrackedItem) -> MonitoringResult:
    try:
        data = await parser.parse_by_profile(item.profile, **item.as_kwargs())
        return MonitoringResult(item=item, results=data)
    except Exception as exc:  # pragma: no cover - ошибки тестируются через значение
        return MonitoringResult(item=item, results=[], error=str(exc))


def _format_notification(results: Iterable[MonitoringResult]) -> str:
    lines: List[str] = []
    for result in results:
        item = result.item
        header_parts = [item.title or item.query, f"профиль {item.profile}"]
        if item.sku:
            header_parts.append(f"SKU {item.sku}")
        header = " | ".join(header_parts)
        if result.error:
            lines.append(f"❌ {header}: {result.error}")
            continue
        count = len(result.results)
        sources = ", ".join(item.sources) if item.sources else "нет источников"
        lines.append(f"✅ {header}: найдено {count} записей, источники: {sources}")
    return "\n".join(lines)


async def process_monitoring_batch(
    storage: Optional[MonitoringStorage] = None,
    parser_factory=UniversalParser,
) -> Dict[int, str]:
    storage = storage or MonitoringStorage()
    items = storage.list_items()
    if not items:
        return {}

    async with parser_factory() as parser:
        tasks = [asyncio.create_task(_process_item(parser, item)) for item in items]
        results = await asyncio.gather(*tasks)

    aggregated: Dict[int, List[MonitoringResult]] = defaultdict(list)
    for result in results:
        aggregated[result.item.user_id].append(result)

    notifications: Dict[int, str] = {}
    for user_id, entries in aggregated.items():
        notifications[user_id] = _format_notification(entries)
    return notifications
