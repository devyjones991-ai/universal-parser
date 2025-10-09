import asyncio
import json
import io
from typing import Any, Dict, List, Optional

import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from urllib.parse import quote_plus, unquote_plus

from config import settings, parsing_profiles
from parser import UniversalParser
from db import save_results, get_recent_results
from navigator.suppliers import search_suppliers, OPEN_CATALOGS
from navigator.guides import get_section, get_paginated_faq
from navigator.logistics import Carrier, find_carriers, initialise_storage

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

SUPPLIERS_PAGE_SIZE = 5
LOGISTICS_PAGE_SIZE = 5
FAQ_PAGE_SIZE = 2


# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS


def _make_callback(prefix: str, page: int, *parts: str) -> str:
    encoded = [quote_plus(str(page))]
    encoded.extend(quote_plus(part or "") for part in parts)
    return "|".join([prefix, *encoded])


def _parse_callback(data: str) -> tuple[str, int, list[str]]:
    parts = data.split("|")
    prefix = parts[0]
    if len(parts) < 2:
        return prefix, 1, []
    page = int(unquote_plus(parts[1])) if parts[1] else 1
    payload = [unquote_plus(part) for part in parts[2:]] if len(parts) > 2 else []
    return prefix, max(1, page), payload


def _build_pagination_keyboard(
    prefix: str, page: int, has_prev: bool, has_next: bool, payload: list[str]
) -> Optional[InlineKeyboardMarkup]:
    buttons = []
    if has_prev:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=_make_callback(prefix, page - 1, *payload),
            )
        )
    if has_next:
        buttons.append(
            InlineKeyboardButton(
                text="➡️ Вперёд",
                callback_data=_make_callback(prefix, page + 1, *payload),
            )
        )
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def _format_supplier_item(item: Dict[str, Any]) -> str:
    name = item.get("name") or item.get("title") or "Без названия"
    parts = [f"🏷️ {name}"]
    if item.get("category"):
        parts.append(f"📂 Категория: {item['category']}")
    if item.get("location"):
        parts.append(f"📍 Город: {item['location']}")
    if item.get("phone"):
        parts.append(f"☎️ Телефон: {item['phone']}")
    if item.get("website"):
        parts.append(f"🌐 {item['website']}")
    return "\n".join(parts)


def _format_carrier_item(carrier: Carrier) -> str:
    parts = [f"🚚 {carrier.name}"]
    if carrier.regions:
        parts.append(f"🗺️ Регионы: {', '.join(carrier.regions)}")
    if carrier.vehicle_types:
        parts.append(f"🚛 Транспорт: {', '.join(carrier.vehicle_types)}")
    if carrier.phone:
        parts.append(f"☎️ {carrier.phone}")
    if carrier.email:
        parts.append(f"✉️ {carrier.email}")
    if carrier.rating is not None:
        parts.append(f"⭐ Рейтинг: {carrier.rating:.1f}")
    return "\n".join(parts)


def _format_section(key: str) -> str:
    section = get_section(key)
    header = f"📘 {section.title} (обновлено {section.updated_at:%d.%m.%Y %H:%M} UTC)"
    return "\n\n".join([header, "\n".join(section.content)])


async def _send_supplier_results(
    message: types.Message,
    query: str,
    source: str,
    page: int,
    *,
    edit: bool = False,
) -> None:
    try:
        result = await search_suppliers(
            query=query,
            source_name=source,
            page=page,
            limit=SUPPLIERS_PAGE_SIZE + 1,
        )
    except KeyError:
        text = f"❌ Источник '{source}' не найден."
        keyboard = None
    except Exception as exc:
        text = f"❌ Ошибка поиска поставщиков: {exc}"
        keyboard = None
    else:
        items = result.results[:SUPPLIERS_PAGE_SIZE]
        has_more = len(result.results) > SUPPLIERS_PAGE_SIZE
        has_prev = page > 1
        keyboard = _build_pagination_keyboard(
            "sup", page, has_prev, has_more, [source, query]
        )
        if items:
            offset = (page - 1) * SUPPLIERS_PAGE_SIZE
            body = []
            for idx, item in enumerate(items, start=1):
                body.append(f"{offset + idx}. {_format_supplier_item(item)}")
            text = (
                f"📦 Источник: {source}\n"
                f"🔎 Запрос: {query}\n"
                f"Страница {page}\n\n"
                + "\n\n".join(body)
            )
        else:
            text = f"⚠️ По запросу '{query}' ничего не найдено."
            keyboard = None

    if edit:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)


async def _send_logistics_results(
    message: types.Message,
    query: Optional[str],
    regions: List[str],
    min_rating: Optional[float],
    page: int,
    *,
    edit: bool = False,
) -> None:
    initialise_storage()
    carriers = find_carriers(
        query=query,
        regions=regions or None,
        min_rating=min_rating,
        limit=LOGISTICS_PAGE_SIZE + 1,
        offset=(page - 1) * LOGISTICS_PAGE_SIZE,
    )
    items = carriers[:LOGISTICS_PAGE_SIZE]
    has_more = len(carriers) > LOGISTICS_PAGE_SIZE
    has_prev = page > 1
    payload = [query or "", ",".join(regions), str(min_rating or "")]
    keyboard = _build_pagination_keyboard("log", page, has_prev, has_more, payload)

    if items:
        offset = (page - 1) * LOGISTICS_PAGE_SIZE
        body = []
        for idx, carrier in enumerate(items, start=1):
            body.append(f"{offset + idx}. {_format_carrier_item(carrier)}")
        filters = ["🚚 Каталог перевозчиков"]
        if query:
            filters.append(f"🔍 Имя содержит: {query}")
        if regions:
            filters.append(f"🌍 Регионы: {', '.join(regions)}")
        if min_rating is not None:
            filters.append(f"⭐ Рейтинг от {min_rating}")
        text = "\n".join(filters) + "\n\n" + "\n\n".join(body)
    else:
        text = "⚠️ Перевозчики по заданным условиям не найдены."
        keyboard = None

    if edit:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)


async def _send_faq(message: types.Message, page: int, *, edit: bool = False) -> None:
    items, total_pages = get_paginated_faq(page=page, per_page=FAQ_PAGE_SIZE)
    if not items and total_pages and page > total_pages:
        items, total_pages = get_paginated_faq(page=total_pages, per_page=FAQ_PAGE_SIZE)
        page = total_pages

    has_prev = page > 1
    has_next = page < total_pages
    keyboard = _build_pagination_keyboard("faq", page, has_prev, has_next, [])

    if items:
        pairs = []
        for idx in range(0, len(items), 2):
            question = items[idx]
            answer = items[idx + 1] if idx + 1 < len(items) else ""
            pairs.append(f"❓ {question}\n💡 {answer}")
        text = "📚 FAQ\n\n" + "\n\n".join(pairs) + f"\n\nСтраница {page} из {total_pages}"
    else:
        text = "FAQ пока пуст."

    if edit:
        await message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

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


@dp.message(Command("quickstart"))
async def cmd_quickstart(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.reply(_format_section("quickstart"))


@dp.message(Command("roadmap"))
async def cmd_roadmap(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await message.reply(_format_section("roadmap"))


@dp.message(Command("faq"))
async def cmd_faq(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    await _send_faq(message, page=1)


@dp.callback_query(F.data.startswith("faq|"))
async def pagination_faq(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, page, _ = _parse_callback(callback.data)
    await _send_faq(callback.message, page=page, edit=True)
    await callback.answer()

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


@dp.message(Command("suppliers"))
async def cmd_suppliers(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    if not OPEN_CATALOGS:
        await message.reply("❌ Каталоги поставщиков не настроены")
        return

    args = message.text.split(" ", 1)
    if len(args) < 2 or not args[1].strip():
        catalogs_list = ", ".join(OPEN_CATALOGS.keys())
        await message.reply(
            "ℹ️ Использование: /suppliers <запрос> или /suppliers <источник>;<запрос>\n"
            f"Доступные источники: {catalogs_list}"
        )
        return

    raw = args[1].strip()
    if ";" in raw:
        source_name, query = [part.strip() for part in raw.split(";", 1)]
        if not source_name:
            source_name = next(iter(OPEN_CATALOGS))
    else:
        source_name = next(iter(OPEN_CATALOGS))
        query = raw

    await _send_supplier_results(message, query=query, source=source_name, page=1)


@dp.callback_query(F.data.startswith("sup|"))
async def pagination_suppliers(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, page, payload = _parse_callback(callback.data)
    source = payload[0] if payload else next(iter(OPEN_CATALOGS))
    query = payload[1] if len(payload) > 1 else ""
    await _send_supplier_results(callback.message, query=query, source=source, page=page, edit=True)
    await callback.answer()

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


@dp.message(Command("logistics"))
async def cmd_logistics(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split(" ", 1)
    query = None
    regions: List[str] = []
    min_rating: Optional[float] = None

    if len(args) > 1 and args[1].strip():
        parts = [part.strip() for part in args[1].split(";")]
        if parts:
            query = parts[0] or None
        if len(parts) > 1 and parts[1]:
            regions = [region.strip() for region in parts[1].split(",") if region.strip()]
        if len(parts) > 2 and parts[2]:
            try:
                min_rating = float(parts[2].replace(",", "."))
            except ValueError:
                await message.reply("⚠️ Некорректное значение рейтинга. Используйте число.")
                return
    else:
        await message.reply(
            "ℹ️ Использование: /logistics <название>;<регионы через запятую>;<мин. рейтинг>"
        )
        return

    await _send_logistics_results(message, query=query, regions=regions, min_rating=min_rating, page=1)


@dp.callback_query(F.data.startswith("log|"))
async def pagination_logistics(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, page, payload = _parse_callback(callback.data)
    query = payload[0] if payload else None
    regions = payload[1].split(",") if len(payload) > 1 and payload[1] else []
    rating_value = payload[2] if len(payload) > 2 else ""
    try:
        min_rating = float(rating_value) if rating_value else None
    except ValueError:
        min_rating = None
    await _send_logistics_results(
        callback.message,
        query=query or None,
        regions=[region for region in regions if region],
        min_rating=min_rating,
        page=page,
        edit=True,
    )
    await callback.answer()

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

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
