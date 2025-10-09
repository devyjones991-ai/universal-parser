from __future__ import annotations

import asyncio
import json
import io

import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from config import settings, parsing_profiles
from parser import UniversalParser
from db import get_recent_results, save_results
from alerts.checker import AlertChecker

alert_checker = AlertChecker()

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
        "/export - экспорт в Excel/CSV\n"
        "/news [niche] [region] - свежие новости\n"
        "/digest [niche] [region] - дайджест\n"
        "/directory <type> [niche] [region] - справочники"
    )


def _parse_filters(message_text: str) -> dict:
    tokens = message_text.split()[1:]
    filters = {"niche": "all", "region": "all"}
    positional_order = ["niche", "region"]
    position = 0

    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            key = key.lower()
            if key in filters:
                filters[key] = value
        else:
            if position < len(positional_order):
                filters[positional_order[position]] = token
                position += 1
    return filters


def _parse_directory_args(message_text: str) -> tuple[str, dict]:
    tokens = message_text.split()[1:]
    entry_type = "supplier"
    filters = {"niche": "all", "region": "all"}
    positional_order = ["niche", "region"]
    position = 0

    if tokens and "=" not in tokens[0]:
        entry_type = tokens[0]
        tokens = tokens[1:]

    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            key = key.lower()
            if key in filters:
                filters[key] = value
        else:
            if position < len(positional_order):
                filters[positional_order[position]] = token
                position += 1
    return entry_type, filters

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

@dp.message(Command("export"))
async def cmd_export(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
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


@dp.message(Command("news"))
async def cmd_news(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    filters = _parse_filters(message.text)
    news_items = await alert_checker.get_news(
        niche=filters["niche"], region=filters["region"], limit=5
    )

    if not news_items:
        await message.reply("❌ Новости не найдены")
        return

    lines = [
        f"📰 Новости для {filters['niche']} / {filters['region']}",
        "",
    ]
    for idx, item in enumerate(news_items, start=1):
        lines.append(
            f"{idx}. {item['title']}\nИсточник: {item['source']}\n"
            f"Дата: {item['published_at']}\nСсылка: {item['url']}"
        )
        if item.get("summary"):
            lines.append(f"Описание: {item['summary']}")
        lines.append("")

    await message.reply("\n".join(lines[:20]))


@dp.message(Command("digest"))
async def cmd_digest(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    filters = _parse_filters(message.text)
    digest = await alert_checker.build_digest(
        niche=filters["niche"], region=filters["region"], news_limit=3
    )

    lines = [
        f"📬 Дайджест для {digest['niche']} / {digest['region']}",
        "",
        "Новости:",
    ]

    if digest["news"]:
        for item in digest["news"]:
            lines.append(f"- {item['title']} ({item['source']})")
    else:
        lines.append("- новостей нет")

    lines.append("")
    lines.append("Справочники:")
    for entry_type, info in digest["directories"].items():
        lines.append(f"- {entry_type}: {info['count']} записей")

    await message.reply("\n".join(lines))


@dp.message(Command("directory"))
async def cmd_directory(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    entry_type, filters = _parse_directory_args(message.text)
    entries = await alert_checker.get_directory_entries(
        entry_type=entry_type, niche=filters["niche"], region=filters["region"], limit=10
    )

    if not entries:
        await message.reply("❌ Записи не найдены")
        return

    lines = [
        f"📚 {entry_type.capitalize()} для {filters['niche']} / {filters['region']}",
        "",
    ]

    for entry in entries:
        lines.append(f"🔸 {entry['name']} (обновлено {entry['updated_at']})")
        if entry.get("contact_info"):
            lines.append(f"Контакты: {entry['contact_info']}")
        if entry.get("metadata"):
            lines.append(f"Детали: {entry['metadata']}")
        lines.append("")

    await message.reply("\n".join(lines[:30]))

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
