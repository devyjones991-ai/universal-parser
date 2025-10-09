"""Команды Telegram-бота."""
from __future__ import annotations

import io
import json
from typing import Any, Dict

import pandas as pd
from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from analytics import UniversalParser
from core import get_recent_results, save_results
from profiles import load_profiles

from .context import bot, dp, settings, task_queue


def is_admin(user_id: int) -> bool:
    return user_id == settings.telegram_chat_id or user_id in settings.admin_chat_ids


async def _handle_parse_url(message: types.Message, url: str) -> None:
    await message.answer(f"🔄 Парсим {url}...")
    async with UniversalParser() as parser:
        results = await parser.parse_url(url)

    if results:
        save_results("manual_parse", results)
        preview = results[:5]
        text = f"✅ Найдено {len(results)} элементов\n\n"
        text += json.dumps(preview, ensure_ascii=False, indent=2)
        if len(text) > 4000:
            text = text[:3900] + "..."
        await message.answer(f"```{text}```", parse_mode="Markdown")
    else:
        await message.answer("❌ Данные не найдены")


async def _handle_run_profile(message: types.Message, profile_name: str) -> None:
    async with UniversalParser() as parser:
        results = await parser.parse_by_profile(profile_name)

    if results:
        save_results(profile_name, results)
        text = [
            f"✅ Профиль '{profile_name}' выполнен",
            f"Найдено: {len(results)} элементов",
            "",
        ]
        for i, result in enumerate(results[:3]):
            text.append(f"{i + 1}. {json.dumps(result, ensure_ascii=False)}")
        if len(results) > 3:
            text.append(f"... и ещё {len(results) - 3} элементов")
        await message.answer("\n".join(text))
    else:
        await message.answer("❌ Данные не найдены")


async def _handle_export(message: types.Message) -> None:
    results = get_recent_results(limit=1000)
    if not results:
        await message.answer("❌ Нет данных для экспорта")
        return

    df = pd.DataFrame(results)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    buffer.seek(0)
    file = BufferedInputFile(buffer.read(), filename="parsing_results.xlsx")
    await message.answer_document(file, caption=f"📈 Экспорт: {len(results)} записей")


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
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
        "/export - экспорт в Excel/CSV"
    )


@dp.message(Command("profiles"))
async def cmd_profiles(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        return

    profiles = load_profiles()
    if not profiles:
        await message.reply("❌ Профили не настроены")
        return

    text = "📋 Доступные профили:\n\n"
    for key, profile in profiles.items():
        text += f"🔸 `{key}` - {profile['name']}\n"

    await message.reply(text, parse_mode="Markdown")


@dp.message(Command("parse"))
async def cmd_parse(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("❌ Использование: /parse <url>")
        return

    url = args[1]
    await task_queue.enqueue("parse_url", message, url)


@dp.message(Command("run"))
async def cmd_run(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("❌ Использование: /run <profile_name>")
        return

    profile_name = args[1]
    profiles = load_profiles()
    if profile_name not in profiles:
        await message.reply(f"❌ Профиль '{profile_name}' не найден")
        return

    await message.answer(f"🔄 Профиль '{profile_name}' поставлен в очередь")
    await task_queue.enqueue("run_profile", message, profile_name)


@dp.message(Command("results"))
async def cmd_results(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        return

    results = get_recent_results(limit=100)
    if not results:
        await message.reply("❌ Результаты не найдены")
        return

    text = f"📊 Последние {len(results)} результатов:\n\n"
    for result in results[:10]:
        text += (
            f"🔸 {result['timestamp']} - {result['profile_name']}: "
            f"{result['count']} элементов\n"
        )
    await message.reply(text)


@dp.message(Command("export"))
async def cmd_export(message: types.Message) -> None:
    if not is_admin(message.from_user.id):
        return

    await _handle_export(message)


@dp.message(F.text)
async def cmd_unknown(message: types.Message) -> None:
    if is_admin(message.from_user.id):
        await message.reply("❓ Неизвестная команда. Используйте /help")


task_queue.register("parse_url", _handle_parse_url)
task_queue.register("run_profile", _handle_run_profile)

def get_bot_components() -> Dict[str, Any]:
    """Возвращает важные компоненты для использования вне пакета."""
    return {
        "bot": bot,
        "dispatcher": dp,
        "queue": task_queue,
    }


__all__ = [
    "bot",
    "dp",
    "get_bot_components",
]
