"""Проверка внешних источников и формирование дайджестов."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts.service import AlertService, AlertServiceError
from integrations.directories import DirectorySyncService
from integrations.news import NewsIntegration
from profiles.models import Alert
from profiles.monitoring import MonitoringStorage, UserTrackedItem
from parser import UniversalParser


class AlertChecker:
    """Периодическая проверка активных алертов с интеграцией новостей и справочников."""

    def __init__(
        self,
        bot: Bot,
        service: Optional[AlertService] = None,
        parser_factory: Callable[[], UniversalParser] = UniversalParser,
        *,
        scheduler: Optional[AsyncIOScheduler] = None,
        news_integration: Optional[NewsIntegration] = None,
        directory_service: Optional[DirectorySyncService] = None,
    ) -> None:
        self.bot = bot
        self.service = service or AlertService()
        self.parser_factory = parser_factory
        self.scheduler = scheduler
        self.news_integration = news_integration or NewsIntegration()
        self.directory_service = directory_service or DirectorySyncService()

    async def get_news(self, niche: str, region: str, limit: int = 5) -> List[Dict]:
        return await self.news_integration.fetch_news(niche=niche, region=region, limit=limit)

    async def get_directory_entries(
        self, entry_type: str, niche: str, region: str, limit: Optional[int] = None
    ) -> List[Dict]:
        return await self.directory_service.sync(
            entry_type=entry_type, niche=niche, region=region, limit=limit
        )

    async def build_digest(
        self,
        niche: str,
        region: str,
        *,
        directory_types: Iterable[str] = ("supplier", "delivery"),
        news_limit: int = 5,
    ) -> Dict[str, Dict]:
        news_items = await self.get_news(niche=niche, region=region, limit=news_limit)
        directory_summary: Dict[str, Dict[str, int]] = {}

        for entry_type in directory_types:
            entries = await self.get_directory_entries(entry_type, niche=niche, region=region)
            directory_summary[entry_type] = {
                "count": len(entries),
            }

        return {
            "niche": niche,
            "region": region,
            "news": news_items,
            "directories": directory_summary,
        }