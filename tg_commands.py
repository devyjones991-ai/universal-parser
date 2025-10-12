"""Основные обработчики Telegram-бота."""
from __future__ import annotations

import asyncio
import io
from typing import Any, Dict, List, Optional
import json
from typing import Iterable, List

import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from urllib.parse import quote_plus, unquote_plus

from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from alerts.checker import AlertChecker
from alerts.service import AlertNotFoundError, AlertService, AlertServiceError
from config import settings, parsing_profiles
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    Message,
    ReplyKeyboardRemove,
)

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
from parser import UniversalParser
from db import save_results, get_recent_results
from navigator.suppliers import search_suppliers, OPEN_CATALOGS
from navigator.guides import get_section, get_paginated_faq
from navigator.logistics import Carrier, find_carriers, initialise_storage

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
async def ensure_admin_message(message: Message) -> bool:
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
        "/alert_add <sku> <условие> <порог> - создать алерт\n"
        "/alert_list - список алертов\n"
        "/alert_delete <id> - удалить алерт\n"
        "/alert_pause <id> [resume] - пауза или запуск"
        await message.answer("❌ Доступ запрещён")
        return False
    return True


async def ensure_admin_callback(callback: CallbackQuery) -> bool:
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return False
    return True


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not await ensure_admin_message(message):
        return

    text = (
        "🚀 Универсальный парсер готов к работе!\n"
        "Выберите действие в главном меню или воспользуйтесь командами."
    )
    await message.answer(text, reply_markup=MAIN_MENU)


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message) -> None:
    if not await ensure_admin_message(message):
        return


    commands: Iterable[str] = (
        "/profiles — список профилей",
        "/parse <url> — спарсить произвольный URL",
        "/run <profile> — выполнить профиль",
        "/results — последние результаты",
        "/export — экспорт последних данных",
    )
    help_text = build_help_section(commands)
    await message.answer(help_text, reply_markup=MAIN_MENU)


@router.message(Command("profiles"))
async def cmd_profiles(message: Message) -> None:
    if not await ensure_admin_message(message):
        return

    if not parsing_profiles:
        await message.answer("❌ Профили не настроены", reply_markup=MAIN_MENU)
        return


    text = "📋 Доступные профили:\n\n"
    for key, profile in parsing_profiles.items():
        text += f"🔸 `{key}` - {profile['name']}\n"

    await message.reply(text, parse_mode="Markdown")


@dp.message(Command("alert_add"))
async def cmd_alert_add(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 4:
        await message.reply("❌ Использование: /alert_add <sku> <условие> <порог>")
        return

    sku = parts[1]
    condition_type = parts[2]
    threshold_raw = parts[3]

    try:
        threshold = float(threshold_raw.replace(",", "."))
    except ValueError:
        await message.reply("❌ Порог должен быть числом")
        return

    alert = await alert_service.add_alert(
        message.from_user.id, sku, condition_type, threshold
    )

    await message.reply(
        "✅ Алерт создан\n"
        f"ID: {alert.id}\n"
        f"SKU: {alert.sku}\n"
        f"Условие: {condition_type} {threshold}"
    )


@dp.message(Command("alert_list"))
async def cmd_alert_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    alerts = await alert_service.list_alerts(message.from_user.id)

    if not alerts:
        await message.reply("ℹ️ У вас нет настроенных алертов")
        return

    lines = ["📬 Ваши алерты:"]
    for alert in alerts:
        status = "активен" if alert.is_active else "на паузе"
        last_value = (
            f", последнее значение: {alert.last_value:.2f}"
            if alert.last_value is not None
            else ""
        )
        lines.append(
            f"#{alert.id}: SKU {alert.sku} — {alert.condition_type} {alert.threshold:.2f} ({status}{last_value})"
        )

    await message.reply("\n".join(lines))


@dp.message(Command("alert_delete"))
async def cmd_alert_delete(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("❌ Использование: /alert_delete <id>")
        return

    try:
        alert_id = int(parts[1])
    except ValueError:
        await message.reply("❌ ID должен быть числом")
        return

    try:
        await alert_service.delete_alert(message.from_user.id, alert_id)
    except AlertNotFoundError:
        await message.reply("❌ Алерт не найден")
        return
    except AlertServiceError as error:
        await message.reply(f"❌ {error}")
        return

    await message.reply(f"🗑️ Алерт #{alert_id} удалён")


@dp.message(Command("alert_pause"))
async def cmd_alert_pause(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("❌ Использование: /alert_pause <id> [resume]")
        return

    try:
        alert_id = int(parts[1])
    except ValueError:
        await message.reply("❌ ID должен быть числом")
        return

    action = parts[2].lower() if len(parts) > 2 else "pause"

    try:
        if action in {"resume", "start", "run", "on"}:
            alert = await alert_service.resume_alert(message.from_user.id, alert_id)
            await message.reply(f"▶️ Алерт #{alert.id} снова активен")
        else:
            alert = await alert_service.pause_alert(message.from_user.id, alert_id)
            await message.reply(f"⏸️ Алерт #{alert.id} поставлен на паузу")
    except AlertNotFoundError:
        await message.reply("❌ Алерт не найден")
    except AlertServiceError as error:
        await message.reply(f"❌ {error}")

@dp.message(Command("parse"))
async def cmd_parse(message: types.Message):
    if not is_admin(message.from_user.id):
    lines: List[str] = ["📋 Доступные профили:"]
    for key, profile in parsing_profiles.items():
        lines.append(f"🔸 <code>{key}</code> — {profile['name']}")

    await message.answer("\n".join(lines), reply_markup=MAIN_MENU)


@router.message(Command("parse"))
async def cmd_parse(message: Message) -> None:
    if not await ensure_admin_message(message):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.answer("❌ Использование: /parse <url>")
        return

    url = args[1].strip()
    await message.answer(f"🔄 Парсим {url}…", reply_markup=ReplyKeyboardRemove())

    try:
        async with UniversalParser() as parser:
            results = await parser.parse_url(url)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        await message.answer(f"❌ Ошибка: {exc}", reply_markup=MAIN_MENU)
        return

    if not results:
        await message.answer("❌ Данные не найдены", reply_markup=MAIN_MENU)
        return

    save_results("manual_parse", results)
    preview = json.dumps(results[:5], ensure_ascii=False, indent=2)
    text = f"✅ Найдено {len(results)} элементов\n<pre>{preview}</pre>"
    await message.answer(text, reply_markup=MAIN_MENU)


async def _run_profile(profile_name: str) -> List[dict]:
    async with UniversalParser() as parser:
        return await parser.parse_by_profile(profile_name)


@router.message(Command("run"))
async def cmd_run(message: Message) -> None:
    if not await ensure_admin_message(message):
        return

    args = message.text.split(" ", 1)
    if len(args) < 2:
        await message.answer("❌ Использование: /run <profile_name>")
        return

    profile_name = args[1].strip()
    if profile_name not in parsing_profiles:
        await message.answer(f"❌ Профиль '{profile_name}' не найден")
        return

    await message.answer(f"🔄 Запускаем профиль '{profile_name}'…", reply_markup=ReplyKeyboardRemove())

    try:
        results = await _run_profile(profile_name)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        await message.answer(f"❌ Ошибка: {exc}", reply_markup=MAIN_MENU)
        return

    if not results:
        await message.answer("❌ Данные не найдены", reply_markup=MAIN_MENU)
        return

    save_results(profile_name, results)
    text_lines = [
        f"✅ Профиль '{profile_name}' выполнен",
        f"Найдено элементов: {len(results)}",
    ]
    for idx, result in enumerate(results[:3], start=1):
        text_lines.append(f"{idx}. {json.dumps(result, ensure_ascii=False)}")
    if len(results) > 3:
        text_lines.append(f"… и ещё {len(results) - 3} элементов")

    await message.answer("\n".join(text_lines), reply_markup=MAIN_MENU)


async def _send_results(message: Message) -> None:
    results = get_recent_results(limit=100)
    if not results:
        await message.answer("❌ Результаты не найдены", reply_markup=MAIN_MENU)
        return

    text_lines = [f"📊 Последние {len(results)} результатов:"]
    for result in results[:10]:
        text_lines.append(
            f"🔸 {result['timestamp']} — {result['profile_name']}: {result['count']} элементов"
        )

    latest_profile = results[0]["profile_name"]
    await message.answer(
        "\n".join(text_lines),
        reply_markup=build_results_actions(latest_profile),
    )


@router.message(Command("results"))
@router.message(F.text == "📊 Последние результаты")
async def cmd_results(message: Message) -> None:
    if not await ensure_admin_message(message):
        return
    await _send_results(message)


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    if not await ensure_admin_message(message):
        return

    results = get_recent_results(limit=1000)
    if not results:
        await message.answer("❌ Нет данных для экспорта", reply_markup=MAIN_MENU)
        return

    dataframe = pd.DataFrame(results)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Results")
    buffer.seek(0)

    file = BufferedInputFile(buffer.read(), filename="parsing_results.xlsx")
    await message.answer_document(file, caption=f"📈 Экспорт: {len(results)} записей")


@dp.callback_query(F.data.startswith("alert:"))
async def alert_callback_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некорректный запрос", show_alert=True)
        return

    _, action, alert_id_raw = parts

    try:
        alert_id = int(alert_id_raw)
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    try:
        if action == "pause":
            await alert_service.pause_alert(callback.from_user.id, alert_id)
            await callback.answer("Алерт приостановлен")
        elif action == "resume":
            await alert_service.resume_alert(callback.from_user.id, alert_id)
            await callback.answer("Алерт запущен")
        elif action == "delete":
            await alert_service.delete_alert(callback.from_user.id, alert_id)
            await callback.answer("Алерт удалён")
            await callback.message.edit_reply_markup(reply_markup=None)
            return
        else:
            await callback.answer("Неизвестное действие", show_alert=True)
            return
    except AlertServiceError as error:
        await callback.answer(str(error), show_alert=True)
        return

    keyboard = build_alert_keyboard(alert_id)
    await callback.message.edit_reply_markup(reply_markup=keyboard)

async def start_bot():
@router.message(Command("alert"))
@router.message(F.text == "➕ Добавить алерт")
async def start_alert(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return

    await state.set_state(AlertScenario.waiting_for_name)
    await message.answer("Введите название алерта:", reply_markup=ReplyKeyboardRemove())


@router.message(AlertScenario.waiting_for_name)
async def alert_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте снова.")
        return

    await state.update_data(name=name)
    await state.set_state(AlertScenario.waiting_for_url)
    await message.answer("Укажите URL, который нужно отслеживать:")


@router.message(AlertScenario.waiting_for_url)
async def alert_url(message: Message, state: FSMContext) -> None:
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("Пожалуйста, введите корректный URL (http/https).")
        return

    await state.update_data(url=url)
    await state.set_state(AlertScenario.waiting_for_conditions)
    await message.answer("Перечислите условия/ключевые слова через запятую:")


@router.message(AlertScenario.waiting_for_conditions)
async def alert_finish(message: Message, state: FSMContext) -> None:
    conditions = [item.strip() for item in message.text.split(",") if item.strip()]
    if not conditions:
        await message.answer("Нужно указать хотя бы одно условие. Попробуйте снова.")
        return

    data = await state.get_data()
    alert = Alert(name=data["name"], url=data["url"], conditions=conditions)
    add_alert(alert)
    await state.clear()

    text = (
        f"✅ Алерт «{alert.name}» сохранён."
        f"\nURL: {alert.url}"
        f"\nУсловия: {', '.join(alert.conditions)}"
    )
    await message.answer(text, reply_markup=MAIN_MENU)


@router.message(Command("import"))
@router.message(F.text == "📥 Импорт списка")
async def start_import(message: Message, state: FSMContext) -> None:
    if not await ensure_admin_message(message):
        return

    await state.set_state(ImportListScenario.waiting_for_payload)
    await message.answer(
        "Отправьте список ссылок или значений. Можно вставить текст блоком или отправить файл .txt.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ImportListScenario.waiting_for_payload)
async def import_payload(message: Message, state: FSMContext) -> None:
    content = message.text or message.caption
    if not content:
        await message.answer("Не удалось прочитать данные. Вставьте текст со списком.")
        return

    parts = [item.strip() for item in content.replace(",", "\n").splitlines() if item.strip()]
    if not parts:
        await message.answer("Список пуст. Попробуйте снова.")
        return

    await state.update_data(items=parts)
    await state.set_state(ImportListScenario.waiting_for_confirmation)
    await message.answer(
        f"Получено {len(parts)} элементов. Сохранить?",
        reply_markup=build_import_confirmation_keyboard(),
    )


@router.callback_query(ImportListScenario.waiting_for_confirmation, F.data == "import:confirm")
async def import_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    if not await ensure_admin_callback(callback):
        return

    data = await state.get_data()
    items = data.get("items", [])
    register_import(ImportBatch(items=items))
    await state.clear()

    await callback.message.answer(
        f"✅ Импорт сохранён. Добавлено {len(items)} элементов.",
        reply_markup=MAIN_MENU,
    )
    await callback.answer("Импорт сохранён")


@router.callback_query(ImportListScenario.waiting_for_confirmation, F.data == "import:cancel")
async def import_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not await ensure_admin_callback(callback):
        return

    await state.clear()
    await callback.message.answer("Импорт отменён.", reply_markup=MAIN_MENU)
    await callback.answer("Отменено")


@router.callback_query(F.data.startswith("results:rerun:"))
async def results_rerun(callback: CallbackQuery) -> None:
    if not await ensure_admin_callback(callback):
        return

    _, _, profile_name = callback.data.partition("results:rerun:")
    profile_name = profile_name.strip()

    if profile_name not in parsing_profiles:
        await callback.message.answer(f"❌ Профиль '{profile_name}' не найден.")
        await callback.answer("Ошибка", show_alert=True)
        return

    try:
        results = await _run_profile(profile_name)
    except Exception as exc:  # pragma: no cover - сетевые ошибки
        await callback.message.answer(f"❌ Ошибка при запуске: {exc}")
        await callback.answer("Ошибка", show_alert=True)
        return

    if not results:
        await callback.message.answer("❌ Данные не найдены")
        await callback.answer("Готово")
        return

    save_results(profile_name, results)
    await callback.message.answer(
        f"✅ Повторный запуск профиля '{profile_name}' завершён. Найдено {len(results)} элементов.",
        reply_markup=MAIN_MENU,
    )
    await callback.answer("Готово")


@router.callback_query(F.data.startswith("results:export:"))
async def results_export(callback: CallbackQuery) -> None:
    if not await ensure_admin_callback(callback):
        return

    _, _, profile_name = callback.data.partition("results:export:")
    profile_name = profile_name.strip()

    results = [result for result in get_recent_results(limit=1000) if result["profile_name"] == profile_name]
    if not results:
        await callback.message.answer("❌ Нет данных для экспорта по выбранному профилю.")
        await callback.answer("Нет данных", show_alert=True)
        return

    dataframe = pd.DataFrame(results)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=profile_name[:31] or "Results")
    buffer.seek(0)

    file = BufferedInputFile(buffer.read(), filename=f"{profile_name}_results.xlsx")
    await callback.message.answer_document(file, caption=f"📈 Экспорт профиля {profile_name}")
    await callback.answer("Экспорт готов")


dp.include_router(router)


async def start_bot() -> None:
    print("🤖 Telegram бот запущен!")
    alert_checker.start()
    try:
        await dp.start_polling(bot)
    finally:
        await alert_checker.shutdown()


if __name__ == "__main__":
    asyncio.run(start_bot())
