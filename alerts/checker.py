from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts.service import AlertService, AlertServiceError
from profiles.models import Alert
from profiles.monitoring import MonitoringStorage, UserTrackedItem
from parser import UniversalParser


class AlertChecker:
    """Периодическая проверка активных алертов."""

    def __init__(
        self,
        bot: Bot,
        service: Optional[AlertService] = None,
        parser_factory: Callable[[], UniversalParser] = UniversalParser,
        *,
        scheduler: Optional[AsyncIOScheduler] = None,
        interval_seconds: int = 300,
    ) -> None:
        self.bot = bot
        self.service = service or AlertService()
        self.parser_factory = parser_factory
        self.scheduler = scheduler or AsyncIOScheduler()
        self.interval_seconds = interval_seconds
        self._job = None

    def start(self) -> None:
        """Запускает периодическую задачу проверки алертов."""

        if self._job is None:
            self._job = self.scheduler.add_job(
                self.run_once, "interval", seconds=self.interval_seconds
            )
        if not self.scheduler.running:
            self.scheduler.start()

    async def run_once(self) -> None:
        """Единовременный запуск проверки всех активных алертов."""

        alerts = await self.service.get_active_alerts()
        for alert in alerts:
            try:
                await self._process_alert(alert)
            except Exception as error:  # pragma: no cover - защитная ветка
                await self.bot.send_message(
                    alert.user_id,
                    f"⚠️ Ошибка проверки алерта {alert.sku}: {error}",
                )

    async def _process_alert(self, alert: Alert) -> None:
        value = await self._fetch_value(alert)
        if not self._should_notify(alert, value):
            return

        updated_alert = await self.service.mark_triggered(alert.id, value)
        text = self._render_message(updated_alert, value)
        await self.bot.send_message(
            updated_alert.user_id,
            text,
            reply_markup=self._build_keyboard(updated_alert),
        )

    async def _fetch_value(self, alert: Alert) -> float:
        parser = self.parser_factory()
        async with parser as client:  # type: ignore[call-arg]
            data = await client.parse_by_profile(alert.sku, sku=alert.sku)
        return self._extract_numeric_value(data)

    def _extract_numeric_value(self, data: Any) -> float:
        if isinstance(data, dict):
            iterable: Sequence = [data]
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
            iterable = data
        else:
            iterable = [data]

        for item in iterable:
            if isinstance(item, dict):
                for key in ("value", "price", "amount", "metric"):
                    candidate = item.get(key)
                    if candidate is None:
                        continue
                    try:
                        return float(candidate)
                    except (TypeError, ValueError):
                        continue
            elif isinstance(item, (int, float)):
                return float(item)
        raise AlertServiceError("Не удалось определить числовое значение для сравнения")

    def _should_notify(self, alert: Alert, value: float) -> bool:
        condition = alert.condition_type.lower()
        threshold = alert.threshold

        if condition in {"lt", "less", "below", "price_below"}:
            triggered = value < threshold
        elif condition in {"gt", "greater", "above", "price_above"}:
            triggered = value > threshold
        elif condition in {"eq", "equals", "equal", "price_equal"}:
            triggered = value == threshold
        else:
            raise AlertServiceError(
                f"Неизвестный тип условия '{alert.condition_type}' для алерта"
            )

        if not triggered:
            return False

        if alert.last_value is not None and abs(alert.last_value - value) < 1e-9:
            return False

        return True

    def _render_message(self, alert: Alert, value: float) -> str:
        descriptions = {
            "lt": "значение ниже порога",
            "less": "значение ниже порога",
            "below": "значение ниже порога",
            "price_below": "значение ниже порога",
            "gt": "значение выше порога",
            "greater": "значение выше порога",
            "above": "значение выше порога",
            "price_above": "значение выше порога",
            "eq": "значение равно порогу",
            "equals": "значение равно порогу",
            "equal": "значение равно порогу",
            "price_equal": "значение равно порогу",
        }
        condition_key = alert.condition_type.lower()
        description = descriptions.get(condition_key, alert.condition_type)

        return (
            f"🚨 Алерт #{alert.id} для SKU {alert.sku} сработал!\n"
            f"Текущее значение: {value:.2f}\n"
            f"Порог: {alert.threshold:.2f}\n"
            f"Условие: {description}"
        )

    def _build_keyboard(self, alert: Alert) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔕 Отписаться",
                        callback_data=f"alert:pause:{alert.id}",
                    ),
                    InlineKeyboardButton(
                        text="▶️ Повторный запуск",
                        callback_data=f"alert:resume:{alert.id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить",
                        callback_data=f"alert:delete:{alert.id}",
                    )
                ],
            ]
        )

    async def shutdown(self) -> None:
        """Останавливает планировщик."""

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self._job = None


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
