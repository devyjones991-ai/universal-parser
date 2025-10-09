import asyncio
import json
import io
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from config import settings, parsing_profiles
from parser import UniversalParser
from db import save_results, get_recent_results
from profiles.monitoring import MonitoringStorage, UserTrackedItem
from profiles.import_export import (
    export_items,
    import_items_from_clipboard,
    import_items_from_file,
)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
monitoring_storage = MonitoringStorage()

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS


def _parse_sources(raw_sources: str) -> list[str]:
    return [s.strip() for s in raw_sources.split(",") if s.strip()]


def _parse_monitor_payload(raw: str) -> UserTrackedItem:
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 2:
        raise ValueError("Ожидается минимум два поля: профиль|запрос|[SKU]|[название]|[источники]")
    profile, query = parts[0], parts[1]
    sku = parts[2] or None if len(parts) > 2 else None
    title = parts[3] or None if len(parts) > 3 else None
    sources = _parse_sources(parts[4]) if len(parts) > 4 else []
    return UserTrackedItem(
        user_id=0,
        profile=profile,
        query=query,
        sku=sku,
        title=title,
        sources=sources,
    )

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


@dp.message(Command("monitor_add"))
async def cmd_monitor_add(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply(
            "❌ Использование: /monitor_add профиль|запрос|[SKU]|[название]|[источники]"
        )
        return

    try:
        item = _parse_monitor_payload(args[1])
    except ValueError as exc:
        await message.reply(f"❌ {exc}")
        return

    item.user_id = message.from_user.id
    added = monitoring_storage.add_item(item)
    if added:
        await message.reply("✅ Мониторинг добавлен")
    else:
        await message.reply("ℹ️ Такой элемент уже есть в списке")


@dp.message(Command("monitor_remove"))
async def cmd_monitor_remove(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.reply("❌ Использование: /monitor_remove профиль|запрос")
        return

    parts = [part.strip() for part in args[1].split("|")]
    if len(parts) < 1 or not parts[0]:
        await message.reply("❌ Укажите профиль")
        return

    profile = parts[0]
    query = parts[1] if len(parts) > 1 and parts[1] else None

    removed = monitoring_storage.remove_item(message.from_user.id, profile, query)
    if removed:
        await message.reply("✅ Элемент удалён")
    else:
        await message.reply("❌ Элемент не найден")


@dp.message(Command("monitor_list"))
async def cmd_monitor_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    profile_filter = args[1].strip() if len(args) > 1 else None

    items = monitoring_storage.list_user_items(message.from_user.id, profile_filter or None)
    if not items:
        await message.reply("ℹ️ Список мониторинга пуст")
        return

    text_lines = ["📋 Текущие элементы мониторинга:"]
    for idx, item in enumerate(items, start=1):
        sources = ", ".join(item.sources) if item.sources else "-"
        parts = [f"{idx}. {item.profile}", f"запрос: {item.query}"]
        if item.sku:
            parts.append(f"SKU: {item.sku}")
        if item.title:
            parts.append(f"название: {item.title}")
        text_lines.append(" | ".join(parts))
        text_lines.append(f"   Источники: {sources}")

    await message.reply("\n".join(text_lines))


@dp.message(Command("batchmonitor"))
async def cmd_batchmonitor(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    if message.document:
        buffer = io.BytesIO()
        await bot.download(message.document, destination=buffer)
        buffer.seek(0)
        try:
            items = import_items_from_file(
                buffer.read(),
                message.document.file_name or "import.xlsx",
                default_user_id=message.from_user.id,
            )
        except ValueError as exc:
            await message.reply(f"❌ {exc}")
            return

        imported = monitoring_storage.extend_user_items(message.from_user.id, items)
        await message.reply(f"📥 Импортировано записей: {imported}")
        return

    args = message.text.split(" ", 1)
    payload = args[1] if len(args) > 1 else ""

    if payload.lower().startswith("import"):
        fmt_and_data = payload[6:].lstrip()
        fmt_line, _, data = fmt_and_data.partition("\n")
        fmt = fmt_line.strip() or "csv"
        data = data.strip()
        if not data:
            await message.reply("❌ Не найдены данные для импорта")
            return
        try:
            items = import_items_from_clipboard(
                data,
                fmt=fmt,
                default_user_id=message.from_user.id,
            )
        except ValueError as exc:
            await message.reply(f"❌ {exc}")
            return
        imported = monitoring_storage.extend_user_items(message.from_user.id, items)
        await message.reply(f"📥 Импортировано записей: {imported}")
        return

    fmt = payload.strip().lower() if payload else "xlsx"
    if fmt not in {"csv", "xlsx"}:
        await message.reply("❌ Формат должен быть csv или xlsx")
        return

    items = monitoring_storage.list_user_items(message.from_user.id)
    if not items:
        await message.reply("ℹ️ Нет элементов для экспорта")
        return

    filename, content = export_items(items, fmt=fmt)
    document = BufferedInputFile(content, filename=filename)
    await message.reply_document(
        document,
        caption=f"📤 Экспортировано {len(items)} записей",
    )

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
