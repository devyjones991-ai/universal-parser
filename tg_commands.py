import asyncio
import io
import json
from decimal import Decimal
from typing import Any, Awaitable, Callable, Dict, Tuple

import pandas as pd
from aiogram import BaseMiddleware, Bot, Dispatcher, types, F
from aiogram.exceptions import SkipHandler
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from sqlalchemy.exc import NoResultFound

from billing import BillingService, LimitExceededError, SubscriptionRequiredError
from config import settings, parsing_profiles
from db import get_recent_results, save_results
from parser import UniversalParser
from analytics.ai_advisor import advisor as ai_advisor
from analytics.service import (
    build_analytics_report,
    export_report,
    format_report_text,
    generate_price_chart,
)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
billing_service = BillingService()
billing_service.ensure_default_tariffs()


class BillingMiddleware(BaseMiddleware):
    """Проверяет лимиты перед выполнением ресурсоёмких команд."""

    def __init__(self, service: BillingService, command_limits: Dict[str, str]):
        super().__init__()
        self.service = service
        self.command_limits = command_limits

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, types.Message):
            return await handler(event, data)

        message = event
        if not message.text:
            return await handler(event, data)

        command = message.text.split()[0].lower()
        metric = self.command_limits.get(command)
        if not metric:
            return await handler(event, data)

        try:
            self.service.ensure_limit(message.from_user.id, metric)
        except SubscriptionRequiredError:
            await message.reply("ℹ️ Для выполнения команды нужна активная подписка.")
            raise SkipHandler()
        except LimitExceededError as exc:
            await message.reply(f"⚠️ {exc}")
            raise SkipHandler()

        return await handler(event, data)


COMMAND_LIMITS = {"/parse": "tracked_products", "/run": "tracked_products"}
dp.message.middleware(BillingMiddleware(billing_service, COMMAND_LIMITS))


# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS


def _format_price(value: Decimal) -> str:
    normalized = float(value)