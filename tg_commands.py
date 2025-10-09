import asyncio
import io
import json
from contextlib import contextmanager

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from config import settings, parsing_profiles
from database import get_session
from db import get_recent_results, save_results
from parser import UniversalParser
from profiles.service import ProfileService

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@contextmanager
def profile_scope(message: types.Message):
    """Создаёт профиль при первом обращении и возвращает сервис."""

    session = get_session()
    try:
        service = ProfileService(session)
        user = message.from_user
        profile = service.get_or_create_profile(
            telegram_id=user.id,
            username=user.username,
            full_name=getattr(user, "full_name", None),
            language_code=getattr(user, "language_code", None),
        )
        yield profile, service
    finally:
        session.close()


def get_profile_settings(service: ProfileService, profile) -> dict:
    """Возвращает настройки пользователя в виде словаря."""

    return {setting.key: setting.value for setting in service.list_settings(profile)}


def log_profile_action(
    service: ProfileService,
    profile,
    action: str,
    payload: str | None = None,
):
    """Фиксирует действие пользователя в истории."""

    service.add_history(profile, action=action, payload=payload)


def get_message_payload(message: types.Message) -> str:
    """Извлекает текст команды для сохранения в истории."""

    return message.text or message.caption or ""

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            await message.reply("❌ Доступ запрещён")
            return

        log_profile_action(
            service,
            profile,
            "command_start",
            payload=get_message_payload(message),
        )

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
async def cmd_profiles(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            return

        log_profile_action(
            service,
            profile,
            "command_profiles",
            payload=get_message_payload(message),
        )

        if not parsing_profiles:
            await message.reply("❌ Профили не настроены")
            return

        text = "📋 Доступные профили:\n\n"
        for key, profile_cfg in parsing_profiles.items():
            text += f"🔸 `{key}` - {profile_cfg['name']}\n"

        await message.reply(text, parse_mode="Markdown")

@dp.message(Command("parse"))
async def cmd_parse(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            return

        args = (message.text or "").split(" ", 1)
        if len(args) < 2 or not args[1].strip():
            await message.reply("❌ Использование: /parse <url>")
            return

        url = args[1].strip()
        log_profile_action(
            service,
            profile,
            "command_parse",
            payload=url,
        )

        await message.reply(f"🔄 Парсим {url}...")

        try:
            async with UniversalParser() as parser:
                results = await parser.parse_url(url)

            if results:
                save_results("manual_parse", results)
                log_profile_action(
                    service,
                    profile,
                    "command_parse_success",
                    payload=url,
                )

                # Отправляем первые результаты
                preview = results[:5]
                text = f"✅ Найдено {len(results)} элементов\n\n"
                text += json.dumps(preview, ensure_ascii=False, indent=2)

                if len(text) > 4000:
                    text = text[:3900] + "..."

                await message.reply(f"``````", parse_mode="Markdown")
            else:
                log_profile_action(
                    service,
                    profile,
                    "command_parse_empty",
                    payload=url,
                )
                await message.reply("❌ Данные не найдены")

        except Exception as e:
            log_profile_action(
                service,
                profile,
                "command_parse_error",
                payload=str(e),
            )
            await message.reply(f"❌ Ошибка: {str(e)}")

@dp.message(Command("run"))
async def cmd_run(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            return

        args = (message.text or "").split(" ", 1)
        if len(args) < 2 or not args[1].strip():
            await message.reply("❌ Использование: /run <profile_name>")
            return

        profile_name = args[1].strip()
        log_profile_action(
            service,
            profile,
            "command_run",
            payload=profile_name,
        )

        if profile_name not in parsing_profiles:
            await message.reply(f"❌ Профиль '{profile_name}' не найден")
            return

        await message.reply(f"🔄 Запускаем профиль '{profile_name}'...")

        try:
            async with UniversalParser() as parser:
                results = await parser.parse_by_profile(profile_name)

            if results:
                save_results(profile_name, results)
                log_profile_action(
                    service,
                    profile,
                    "command_run_success",
                    payload=profile_name,
                )

                text = f"✅ Профиль '{profile_name}' выполнен\n"
                text += f"Найдено: {len(results)} элементов\n\n"

                # Показываем примеры
                for i, result in enumerate(results[:3]):
                    text += f"{i+1}. {json.dumps(result, ensure_ascii=False)}\n"

                if len(results) > 3:
                    text += f"... и ещё {len(results)-3} элементов"

                await message.reply(text)
            else:
                log_profile_action(
                    service,
                    profile,
                    "command_run_empty",
                    payload=profile_name,
                )
                await message.reply("❌ Данные не найдены")

        except Exception as e:
            log_profile_action(
                service,
                profile,
                "command_run_error",
                payload=str(e),
            )
            await message.reply(f"❌ Ошибка: {str(e)}")

@dp.message(Command("results"))
async def cmd_results(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            return

        log_profile_action(
            service,
            profile,
            "command_results",
            payload=get_message_payload(message),
        )

        results = get_recent_results(limit=100)

        if not results:
            await message.reply("❌ Результаты не найдены")
            return

        text = f"📊 Последние {len(results)} результатов:\n\n"

        for result in results[:10]:
            text += (
                f"🔸 {result['timestamp']} - {result['profile_name']}: {result['count']} элементов\n"
            )

        await message.reply(text)

@dp.message(Command("export"))
async def cmd_export(message: types.Message):
    with profile_scope(message) as (profile, service):
        if not is_admin(message.from_user.id):
            log_profile_action(
                service,
                profile,
                "access_denied",
                payload=get_message_payload(message),
            )
            return

        log_profile_action(
            service,
            profile,
            "command_export",
            payload=get_message_payload(message),
        )

        results = get_recent_results(limit=1000)

        if not results:
            await message.reply("❌ Нет данных для экспорта")
            return

        # Создаём Excel файл
        df = pd.DataFrame(results)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Results')

        buffer.seek(0)

        file = BufferedInputFile(buffer.read(), filename="parsing_results.xlsx")
        await message.reply_document(file, caption=f"📈 Экспорт: {len(results)} записей")

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
