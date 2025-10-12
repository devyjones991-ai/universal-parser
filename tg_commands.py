import io
import json
from decimal import Decimal
from typing import Any, Awaitable, Callable, Dict

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
    if normalized.is_integer():
        return f"{int(normalized)}₽"
    return f"{normalized:.2f}₽"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Доступ запрещён")
        return

    await message.reply(
        "🚀 Универсальный парсер запущен!\n\n"
        "Команды:\n"
        "/profiles - список профилей\n"
        "/parse <url> - парсить URL\n"
        "/run <profile> - запустить профиль\n"
        "/results - последние результаты\n"
        "/export - экспорт в Excel/CSV\n"
        "/plan - текущий тариф и варианты\n"
        "/subscribe <тариф> - запросить подписку\n"
        "/usage - текущее использование лимитов"
    )


@dp.message(Command("profiles"))
async def cmd_profiles(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    if not parsing_profiles:
        await message.reply("❌ Профили не настроены")
        return

    text = "📋 Доступные профили:\n\n"
    for key, profile in parsing_profiles.items():
        text += f"🔸 `{key}` - {profile['name']}\n"

    await message.reply(text, parse_mode="Markdown")


@dp.message(Command("parse"))
async def cmd_parse(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("❌ Использование: /parse <url>")
        return

    url = args[1]
    await message.reply(f"🔄 Парсим {url}...")

    try:
        async with UniversalParser() as parser:
            results = await parser.parse_url(url)

        if results:
            save_results("manual_parse", results)
            try:
                billing_service.increment_usage(message.from_user.id, "tracked_products")
            except (LimitExceededError, SubscriptionRequiredError):
                await message.reply("⚠️ Лимит мониторинга превышен, результаты не сохранены.")
                return

            preview = results[:5]
            text = f"✅ Найдено {len(results)} элементов\n\n"
            text += json.dumps(preview, ensure_ascii=False, indent=2)

            if len(text) > 4000:
                text = text[:3900] + "..."

            await message.reply(f"``````", parse_mode="Markdown")
        else:
            await message.reply("❌ Данные не найдены")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")


@dp.message(Command("run"))
async def cmd_run(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("❌ Использование: /run <profile_name>")
        return

    profile_name = args[1]

    if profile_name not in parsing_profiles:
        await message.reply(f"❌ Профиль '{profile_name}' не найден")
        return

    await message.reply(f"🔄 Запускаем профиль '{profile_name}'...")

    try:
        async with UniversalParser() as parser:
            results = await parser.parse_by_profile(profile_name)

        if results:
            save_results(profile_name, results)
            try:
                billing_service.increment_usage(message.from_user.id, "tracked_products")
            except (LimitExceededError, SubscriptionRequiredError):
                await message.reply("⚠️ Лимит мониторинга превышен, результаты не сохранены.")
                return

            text = f"✅ Профиль '{profile_name}' выполнен\n"
            text += f"Найдено: {len(results)} элементов\n\n"

            for i, result in enumerate(results[:3]):
                text += f"{i+1}. {json.dumps(result, ensure_ascii=False)}\n"

            if len(results) > 3:
                text += f"... и ещё {len(results)-3} элементов"

            await message.reply(text)
        else:
            await message.reply("❌ Данные не найдены")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")


@dp.message(Command("results"))
async def cmd_results(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    results = get_recent_results(limit=100)

    if not results:
        await message.reply("❌ Результаты не найдены")
        return

    text = f"📊 Последние {len(results)} результатов:\n\n"

    for result in results[:10]:
        text += f"🔸 {result['timestamp']} - {result['profile_name']}: {result['count']} элементов\n"

    await message.reply(text)


@dp.message(Command("export"))
async def cmd_export(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    results = get_recent_results(limit=1000)

    if not results:
        await message.reply("❌ Нет данных для экспорта")
        return

    df = pd.DataFrame(results)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
        writer.close()
        buffer.seek(0)

    await message.reply_document(
        BufferedInputFile(buffer.read(), filename="results.xlsx"),
        caption="📦 Экспорт выполнен"
    )


@dp.message(Command("plan"))
async def cmd_plan(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    subscription = billing_service.get_active_subscription(message.from_user.id)
    tariffs = billing_service.list_tariffs()

    lines = ["📦 Текущий план:"]
    if subscription:
        limit = subscription.tariff.tracked_products_limit or "∞"
        lines.append(
            f"- {subscription.tariff.name} ({subscription.tariff.code}), мониторинг до {limit} товаров"
        )
    else:
        lines.append("- нет активной подписки")

    lines.append("\n💳 Доступные тарифы:")
    for tariff in tariffs:
        price = _format_price(Decimal(tariff.monthly_price))
        limit = tariff.tracked_products_limit or "∞"
        lines.append(f"- {tariff.name} ({tariff.code}): до {limit} товаров, {price}")

    await message.reply("\n".join(lines))


@dp.message(Command("subscribe"))
async def cmd_subscribe(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("ℹ️ Использование: /subscribe <тариф> [провайдер]")
        return

    tariff_code = parts[1]
    provider_name = parts[2] if len(parts) > 2 else "manual"

    try:
        subscription = billing_service.create_subscription(
            message.from_user.id, tariff_code, provider_name
        )
    except NoResultFound:
        await message.reply("❌ Тариф не найден")
        return
    except ValueError as exc:
        await message.reply(f"❌ {exc}")
        return

    payment = billing_service.get_latest_payment(subscription.id)
    if provider_name == "manual":
        await message.reply(
            "🧾 Заявка создана. Администратор активирует подписку после оплаты."
        )
        return

    if payment and payment.confirmation_url:
        await message.reply("🧾 Ссылка для оплаты: " + payment.confirmation_url)
    else:
        await message.reply("🧾 Платёж создан. Дождитесь подтверждения провайдера.")


@dp.message(Command("usage"))
async def cmd_usage(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    try:
        usage = billing_service.get_usage_report(message.from_user.id)
    except SubscriptionRequiredError:
        await message.reply("ℹ️ У вас нет активной подписки.")
        return

    labels = {
        "tracked_products": "Мониторинг товаров",
        "alerts": "Алерты",
    }

    lines = ["📈 Использование лимитов:"]
    for metric, info in usage.items():
        limit_text = "∞" if info.limit == 0 else str(info.limit)
        lines.append(f"- {labels.get(metric, metric)}: {info.used}/{limit_text}")

    await message.reply("\n".join(lines))


__all__ = ["bot", "dp"]
"""Основные обработчики Telegram-бота."""
from __future__ import annotations

import asyncio
import io
import json
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from urllib.parse import quote_plus, unquote_plus

from alerts.checker import AlertChecker
from alerts.service import AlertNotFoundError, AlertService, AlertServiceError
from bot import bot, dp
from bot.keyboards import (
    MAIN_MENU,
    build_import_confirmation_keyboard,
    build_results_actions,
)
from bot.services import Alert, ImportBatch, add_alert, register_import
from bot.states import AlertScenario, ImportListScenario
from config import parsing_profiles, settings
from db import get_recent_results, save_results
from navigator import build_help_section
from navigator.guides import get_section, get_paginated_faq
from navigator.logistics import Carrier, find_carriers, initialise_storage
from navigator.suppliers import search_suppliers, OPEN_CATALOGS
from parser import UniversalParser
from profiles.monitoring import MonitoringStorage

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
alert_service = AlertService()
alert_checker = AlertChecker(bot=bot, service=alert_service)
monitoring_storage = MonitoringStorage()

router = Router(name="main")


SUPPLIERS_PAGE_SIZE = 5
LOGISTICS_PAGE_SIZE = 5
FAQ_PAGE_SIZE = 2


# Проверка доступа
