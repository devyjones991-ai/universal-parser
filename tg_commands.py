import asyncio
import contextlib
import io
import json
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from config import parsing_profiles, settings
from parser import UniversalParser
from db import SessionLocal, get_recent_results, save_results, init_db
from profiles.models import UserTip
from profiles.tip_service import (
    approve_tip,
    archive_tip,
    create_tip,
    get_top_tips,
    iter_subscribers,
    record_feedback,
    reject_tip,
)

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

SUBSCRIBERS: set[int] = set()

init_db()


def register_subscriber(chat_id: int) -> None:
    """Добавляет чат в список получателей дайджеста."""

    SUBSCRIBERS.add(chat_id)


def tip_rating_keyboard(tip_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍", callback_data=f"tip_like:{tip_id}:1"),
                InlineKeyboardButton(text="👎", callback_data=f"tip_like:{tip_id}:-1"),
            ]
        ]
    )


def moderation_keyboard(tip_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"tip_moderate:approve:{tip_id}"),
                InlineKeyboardButton(text="🚫 Отклонить", callback_data=f"tip_moderate:reject:{tip_id}"),
            ]
        ]
    )


def format_tip_message(tip: UserTip) -> str:
    author = tip.author_username or "Аноним"
    rating = tip.rating
    header = f"💡 Совет от {author}"
    rating_line = f"⭐️ Рейтинг: {rating}"
    return f"{header}\n\n{tip.content}\n\n{rating_line}"


async def broadcast_tip(tip: UserTip, *, origin_chat_id: int | None = None) -> None:
    recipients = set(SUBSCRIBERS)
    recipients.update(iter_subscribers(settings.TELEGRAM_CHAT_ID, settings.ADMIN_CHAT_IDS))
    if origin_chat_id:
        recipients.add(origin_chat_id)

    text = format_tip_message(tip)
    for chat_id in recipients:
        try:
            await bot.send_message(chat_id, text, reply_markup=tip_rating_keyboard(tip.id))
        except Exception as exc:  # pragma: no cover - сетевые ошибки
            print(f"Не удалось отправить совет в чат {chat_id}: {exc}")


async def notify_admins_about_tip(tip: UserTip) -> None:
    text = (
        "🆕 Новый совет ожидает модерации\n\n"
        f"Автор: {tip.author_username or tip.author_id}\n"
        f"ID совета: {tip.id}\n\n"
        f"{tip.content}"
    )

    for admin_id in iter_subscribers(None, settings.ADMIN_CHAT_IDS):
        try:
            await bot.send_message(admin_id, text, reply_markup=moderation_keyboard(tip.id))
        except Exception as exc:  # pragma: no cover - сетевые ошибки
            print(f"Не удалось уведомить администратора {admin_id}: {exc}")


async def send_weekly_digest() -> bool:
    with SessionLocal() as session:
        tips = get_top_tips(session, period_days=7, limit=5)

    if not tips:
        return False

    lines = ["🧠 Лайфхаки недели", ""]
    for index, tip in enumerate(tips, start=1):
        lines.append(f"{index}. {tip.content} (рейтинг: {tip.rating})")

    digest_text = "\n".join(lines)
    recipients = set(SUBSCRIBERS)
    recipients.update(iter_subscribers(settings.TELEGRAM_CHAT_ID, settings.ADMIN_CHAT_IDS))

    for chat_id in recipients:
        try:
            await bot.send_message(chat_id, digest_text)
        except Exception as exc:  # pragma: no cover - сетевые ошибки
            print(f"Не удалось отправить дайджест в чат {chat_id}: {exc}")

    return True


async def weekly_digest_worker() -> None:
    """Фоновый таск для периодической отправки дайджеста."""

    while True:
        try:
            await asyncio.sleep(7 * 24 * 60 * 60)
            await send_weekly_digest()
        except asyncio.CancelledError:  # pragma: no cover - завершение работы
            break
        except Exception as exc:  # pragma: no cover - логирование ошибок
            print(f"Ошибка при формировании дайджеста: {exc}")

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Доступ запрещён")
        return

    register_subscriber(message.chat.id)

    await message.reply(
        "🚀 Универсальный парсер запущен!\n\n"
        "Команды:\n"
        "/profiles - список профилей\n"
        "/parse <url> - парсить URL\n"
        "/run <profile> - запустить профиль\n"
        "/results - последние результаты\n"
        "/export - экспорт в Excel/CSV\n"
        "/tip_send <текст> - отправить лайфхак\n"
        "/tip_best - лучшие лайфхаки\n"
        "/tip_archive <id> [on|off] - архивировать совет"
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


@dp.message(Command("tip_send"))
async def cmd_tip_send(message: types.Message):
    args = message.text.split(" ", 1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("❌ Использование: /tip_send <текст совета>")
        return

    register_subscriber(message.chat.id)

    with SessionLocal() as session:
        tip = create_tip(
            session,
            author_id=message.from_user.id,
            author_username=message.from_user.username,
            content=args[1],
            approved=is_admin(message.from_user.id),
        )

        if tip.is_approved:
            await broadcast_tip(tip, origin_chat_id=message.chat.id)
            await message.reply("✅ Совет опубликован")
        else:
            await notify_admins_about_tip(tip)
            await message.reply("🕒 Совет отправлен на модерацию")


@dp.message(Command("tip_best"))
async def cmd_tip_best(message: types.Message):
    register_subscriber(message.chat.id)

    with SessionLocal() as session:
        tips = get_top_tips(session, limit=5)

    if not tips:
        await message.reply("❌ Подходящие советы не найдены")
        return

    lines = ["🔥 Лучшие лайфхаки:"]
    for index, tip in enumerate(tips, start=1):
        lines.append(f"{index}. {tip.content} — рейтинг {tip.rating}")

    await message.reply("\n".join(lines))


@dp.message(Command("tip_archive"))
async def cmd_tip_archive(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("❌ Недостаточно прав")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Использование: /tip_archive <id> [on|off]")
        return

    try:
        tip_id = int(args[1])
    except ValueError:
        await message.reply("❌ ID должен быть числом")
        return

    state = True
    if len(args) >= 3:
        flag = args[2].lower()
        if flag in {"off", "0", "false"}:
            state = False

    with SessionLocal() as session:
        try:
            tip = archive_tip(session, tip_id, value=state)
        except Exception as exc:
            await message.reply(f"❌ {exc}")
            return

    status = "в архиве" if tip.is_archived else "активен"
    await message.reply(f"ℹ️ Совет #{tip.id} теперь {status}")


@dp.callback_query(F.data.startswith("tip_"))
async def tip_callback_handler(callback: CallbackQuery):
    data = callback.data.split(":")

    if data[0] == "tip_like":
        tip_id = int(data[1])
        value = int(data[2])

        with SessionLocal() as session:
            try:
                tip = record_feedback(session, tip_id, callback.from_user.id, value)
            except Exception as exc:
                await callback.answer(str(exc), show_alert=True)
                return

        await callback.answer(f"Текущий рейтинг: {tip.rating}")
        try:
            await callback.message.edit_text(
                format_tip_message(tip), reply_markup=tip_rating_keyboard(tip.id)
            )
        except TelegramBadRequest:
            pass

    elif data[0] == "tip_moderate":
        action = data[1]
        tip_id = int(data[2])

        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Только администраторы могут модерировать", show_alert=True)
            return

        with SessionLocal() as session:
            try:
                if action == "approve":
                    tip = approve_tip(session, tip_id)
                else:
                    tip = reject_tip(session, tip_id)
            except Exception as exc:
                await callback.answer(str(exc), show_alert=True)
                return

        if action == "approve":
            await callback.answer("✅ Опубликовано")
            await broadcast_tip(tip)
        else:
            await callback.answer("🚫 Отклонено")
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except TelegramBadRequest:
                pass

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

async def start_bot():
    print("🤖 Telegram бот запущен!")
    digest_task = asyncio.create_task(weekly_digest_worker())
    try:
        await dp.start_polling(bot)
    finally:
        digest_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await digest_task

if __name__ == "__main__":
    asyncio.run(start_bot())
