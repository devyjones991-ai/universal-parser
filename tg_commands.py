import asyncio
import io
import json
from typing import Dict, Tuple

import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from config import settings, parsing_profiles
from parser import UniversalParser
from db import get_recent_results, save_results

from analytics.ai_advisor import advisor as ai_advisor
from analytics.service import (
    build_analytics_report,
    export_report,
    format_report_text,
    generate_price_chart,
)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS

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
        "/export - экспорт в Excel/CSV"
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
            
            # Отправляем первые результаты
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
            
            text = f"✅ Профиль '{profile_name}' выполнен\n"
            text += f"Найдено: {len(results)} элементов\n\n"
            
            # Показываем примеры
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

def _parse_command_args(text: str) -> Tuple[Dict[str, str], Tuple[str, ...]]:
    parts = text.split()
    params: Dict[str, str] = {}
    positional: Tuple[str, ...] = tuple()

    if len(parts) <= 1:
        return params, positional

    collected_positional = []
    for token in parts[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            params[key.lower()] = value
        else:
            collected_positional.append(token)

    return params, tuple(collected_positional)


@dp.message(Command("export"))
async def cmd_export(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    params, positional = _parse_command_args(message.text or "")
    export_format = params.get("format") or (positional[0] if positional else settings.EXPORT_FORMAT)
    export_format = (export_format or "xlsx").lower()

    if export_format in {"csv", "json"}:
        profile = params.get("profile") or (positional[1] if len(positional) > 1 else None)
        item_id = params.get("item") or params.get("item_id")
        period = params.get("period")
        start = params.get("start")
        end = params.get("end")

        report = build_analytics_report(
            profile_name=profile,
            item_id=item_id,
            period=period,
            start_date=start,
            end_date=end,
        )

        try:
            buffer, filename, _ = export_report(report, export_format)
        except ValueError as exc:
            await message.reply(f"❌ {exc}")
            return

        file = BufferedInputFile(buffer.read(), filename=filename)
        await message.reply_document(
            file,
            caption="📊 Экспорт аналитики",
        )
        return

    results = get_recent_results(limit=1000)

    if not results:
        await message.reply("❌ Нет данных для экспорта")
        return

    df = pd.DataFrame(results)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")

    buffer.seek(0)

    file = BufferedInputFile(buffer.read(), filename="parsing_results.xlsx")
    await message.reply_document(file, caption=f"📈 Экспорт: {len(results)} записей")


@dp.message(Command("analytics"))
async def cmd_analytics(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    params, positional = _parse_command_args(message.text or "")
    profile = params.get("profile") or (positional[0] if positional else None)
    if not profile:
        await message.reply("❌ Укажите профиль: /analytics profile=<имя> [item=<id>] [period=7d]")
        return

    item_id = params.get("item") or params.get("item_id") or (positional[1] if len(positional) > 1 else None)
    period = params.get("period") or (positional[2] if len(positional) > 2 else None)
    start = params.get("start")
    end = params.get("end")

    report = build_analytics_report(
        profile_name=profile,
        item_id=item_id,
        period=period,
        start_date=start,
        end_date=end,
    )

    text = format_report_text(report)
    await message.reply(text)

    chart_buffer = generate_price_chart(report)
    if chart_buffer:
        chart_file = BufferedInputFile(chart_buffer.read(), filename="analytics_chart.png")
        await message.reply_photo(chart_file, caption="График динамики цены")

    advice = ai_advisor.advise(report)
    if advice:
        await message.reply(f"🤖 AI подсказки:\n{advice}")

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
