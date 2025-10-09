import asyncio
import json
import io
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from alerts.checker import AlertChecker
from alerts.service import AlertNotFoundError, AlertService, AlertServiceError
from config import settings, parsing_profiles
from parser import UniversalParser
from db import save_results, get_recent_results

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
alert_service = AlertService()
alert_checker = AlertChecker(bot=bot, service=alert_service)

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS


def build_alert_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с быстрыми действиями для алертов."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔕 Отписаться", callback_data=f"alert:pause:{alert_id}"
                ),
                InlineKeyboardButton(
                    text="▶️ Повторный запуск",
                    callback_data=f"alert:resume:{alert_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить", callback_data=f"alert:delete:{alert_id}"
                )
            ],
        ]
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
        "/export - экспорт в Excel/CSV\n"
        "/alert_add <sku> <условие> <порог> - создать алерт\n"
        "/alert_list - список алертов\n"
        "/alert_delete <id> - удалить алерт\n"
        "/alert_pause <id> [resume] - пауза или запуск"
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
    print("🤖 Telegram бот запущен!")
    alert_checker.start()
    try:
        await dp.start_polling(bot)
    finally:
        await alert_checker.shutdown()

if __name__ == "__main__":
    asyncio.run(start_bot())
