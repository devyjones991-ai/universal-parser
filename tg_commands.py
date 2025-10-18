import asyncio
import json
import io
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings, parsing_profiles
from parser import UniversalParser
from db import (
    save_results, get_recent_results, get_or_create_user, get_user_by_telegram_id,
    add_tracked_item, get_user_tracked_items, remove_tracked_item, create_alert,
    get_user_alerts, deactivate_alert, get_user_stats, get_price_history
)
from alert_system import monitoring_service, AlertNotificationService
from analytics import analytics_service
from subscription import subscription_service, payment_service

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация сервиса уведомлений
alert_notification_service = AlertNotificationService(bot)

# Состояния для FSM
class AddItemStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()
    waiting_for_marketplace = State()

class AddAlertStates(StatesGroup):
    waiting_for_alert_type = State()
    waiting_for_conditions = State()

# Проверка доступа
def is_admin(user_id: int) -> bool:
    return user_id == settings.TELEGRAM_CHAT_ID or user_id in settings.ADMIN_CHAT_IDS

def get_user_or_create(message: types.Message):
    """Получить или создать пользователя"""
    return get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем или получаем пользователя
    user = get_user_or_create(message)
    
    # Создаем клавиатуру
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Моя статистика"), KeyboardButton(text="📦 Мои товары")],
            [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="🔔 Мои алерты")],
            [KeyboardButton(text="📈 Аналитика"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="💳 Подписка")]
        ],
        resize_keyboard=True
    )
    
    welcome_text = f"""
🎯 <b>Добро пожаловать в Universal Parser!</b>

👋 Привет, {user.first_name or 'пользователь'}!

🚀 <b>Что я умею:</b>
• 📦 Отслеживать товары на маркетплейсах
• 🔔 Уведомлять об изменениях цен и остатков
• 📈 Анализировать динамику цен
• 📊 Создавать отчеты и графики

💡 <b>Начните с добавления товара для отслеживания!</b>

Используйте кнопки ниже или команды:
/monitor - добавить товар
/alerts - настроить алерты
/stats - ваша статистика
    """
    
    await message.reply(welcome_text, reply_markup=keyboard, parse_mode="HTML")

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
            
            await message.reply(f"```json\n{text}\n```", parse_mode="Markdown")
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

# Новые команды для пользователей
@dp.message(Command("monitor"))
async def cmd_monitor(message: types.Message, state: FSMContext):
    """Добавить товар для отслеживания"""
    user = get_user_or_create(message)
    
    # Проверяем лимиты подписки
    stats = get_user_stats(user.id)
    if stats["subscription_tier"] == "free" and stats["tracked_items_count"] >= 3:
        await message.reply(
            "❌ <b>Достигнут лимит бесплатной подписки!</b>\n\n"
            "Вы можете отслеживать только 3 товара.\n"
            "Для увеличения лимита оформите Premium подписку: /subscription",
            parse_mode="HTML"
        )
        return
    
    await state.set_state(AddItemStates.waiting_for_url)
    await message.reply(
        "📦 <b>Добавление товара для отслеживания</b>\n\n"
        "Отправьте ссылку на товар или его артикул:",
        parse_mode="HTML"
    )

@dp.message(AddItemStates.waiting_for_url)
async def process_item_url(message: types.Message, state: FSMContext):
    """Обработка URL товара"""
    url = message.text.strip()
    
    # Определяем маркетплейс по URL
    marketplace = None
    if "wildberries.ru" in url or "wb.ru" in url:
        marketplace = "wb"
    elif "ozon.ru" in url:
        marketplace = "ozon"
    elif "market.yandex.ru" in url:
        marketplace = "yandex"
    else:
        await message.reply(
            "❌ Неподдерживаемый маркетплейс!\n\n"
            "Поддерживаются: Wildberries, Ozon, Яндекс.Маркет"
        )
        return
    
    await state.update_data(url=url, marketplace=marketplace)
    await state.set_state(AddItemStates.waiting_for_name)
    
    await message.reply(
        f"✅ Маркетплейс: {marketplace.upper()}\n\n"
        "Введите название товара:"
    )

@dp.message(AddItemStates.waiting_for_name)
async def process_item_name(message: types.Message, state: FSMContext):
    """Обработка названия товара"""
    name = message.text.strip()
    data = await state.get_data()
    
    user = get_user_by_telegram_id(message.from_user.id)
    
    # Извлекаем ID товара из URL
    item_id = extract_item_id(data["url"], data["marketplace"])
    
    try:
        tracked_item = add_tracked_item(
            user_id=user.id,
            item_id=item_id,
            marketplace=data["marketplace"],
            name=name,
            url=data["url"]
        )
        
        await state.clear()
        
        await message.reply(
            f"✅ <b>Товар добавлен для отслеживания!</b>\n\n"
            f"📦 <b>Название:</b> {name}\n"
            f"🏪 <b>Маркетплейс:</b> {data['marketplace'].upper()}\n"
            f"🔗 <b>Ссылка:</b> {data['url']}\n\n"
            f"Теперь вы будете получать уведомления об изменениях цены и остатков!",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при добавлении товара: {str(e)}")
        await state.clear()

def extract_item_id(url: str, marketplace: str) -> str:
    """Извлечь ID товара из URL"""
    if marketplace == "wb":
        # Для Wildberries извлекаем ID из URL
        import re
        match = re.search(r'/(\d+)/', url)
        return match.group(1) if match else url
    elif marketplace == "ozon":
        # Для Ozon
        import re
        match = re.search(r'product/(\d+)', url)
        return match.group(1) if match else url
    else:
        return url

@dp.message(Command("myitems"))
async def cmd_my_items(message: types.Message):
    """Показать отслеживаемые товары"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    items = get_user_tracked_items(user.id)
    
    if not items:
        await message.reply(
            "📦 <b>У вас пока нет отслеживаемых товаров</b>\n\n"
            "Добавьте товар командой /monitor",
            parse_mode="HTML"
        )
        return
    
    text = f"📦 <b>Ваши товары ({len(items)}):</b>\n\n"
    
    for i, item in enumerate(items, 1):
        price_text = f"💰 {item.current_price} ₽" if item.current_price else "💰 Цена неизвестна"
        stock_text = f"📦 {item.current_stock} шт" if item.current_stock is not None else "📦 Остаток неизвестен"
        
        text += f"{i}. <b>{item.name}</b>\n"
        text += f"   {price_text} | {stock_text}\n"
        text += f"   🏪 {item.marketplace.upper()} | 🔗 {item.url}\n\n"
    
    # Добавляем кнопки управления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="remove_item")],
        [InlineKeyboardButton(text="🔔 Настроить алерты", callback_data="setup_alerts")]
    ])
    
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("alerts"))
async def cmd_alerts(message: types.Message):
    """Показать алерты пользователя"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    alerts = get_user_alerts(user.id)
    
    if not alerts:
        await message.reply(
            "🔔 <b>У вас нет настроенных алертов</b>\n\n"
            "Создайте алерт для отслеживания изменений цен и остатков!",
            parse_mode="HTML"
        )
        return
    
    text = f"🔔 <b>Ваши алерты ({len(alerts)}):</b>\n\n"
    
    for i, alert in enumerate(alerts, 1):
        alert_type_names = {
            "price_drop": "📉 Падение цены",
            "price_rise": "📈 Рост цены", 
            "stock_change": "📦 Изменение остатков",
            "review_change": "⭐ Изменение рейтинга"
        }
        
        text += f"{i}. {alert_type_names.get(alert.alert_type, alert.alert_type)}\n"
        text += f"   Условия: {json.dumps(alert.conditions, ensure_ascii=False)}\n"
        text += f"   Срабатываний: {alert.trigger_count}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать алерт", callback_data="create_alert")],
        [InlineKeyboardButton(text="🗑 Удалить алерт", callback_data="remove_alert")]
    ])
    
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Показать статистику пользователя"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    stats = get_user_stats(user.id)
    
    text = f"""
📊 <b>Ваша статистика</b>

👤 <b>Профиль:</b>
• Имя: {user.first_name or 'Не указано'}
• Подписка: {stats['subscription_tier'].upper()}
• Регистрация: {stats['created_at']}
• Последняя активность: {stats['last_activity']}

📦 <b>Отслеживание:</b>
• Товаров: {stats['tracked_items_count']}
• Алертов: {stats['alerts_count']}

💡 <b>Советы:</b>
• Добавляйте товары для отслеживания цен
• Настраивайте алерты для уведомлений
• Используйте аналитику для принятия решений
    """
    
    await message.reply(text, parse_mode="HTML")

# Обработчики кнопок
@dp.message(F.text == "📊 Моя статистика")
async def handle_stats_button(message: types.Message):
    await cmd_stats(message)

@dp.message(F.text == "📦 Мои товары")
async def handle_items_button(message: types.Message):
    await cmd_my_items(message)

@dp.message(F.text == "➕ Добавить товар")
async def handle_add_item_button(message: types.Message, state: FSMContext):
    await cmd_monitor(message, state)

@dp.message(F.text == "🔔 Мои алерты")
async def handle_alerts_button(message: types.Message):
    await cmd_alerts(message)

@dp.message(F.text == "❓ Помощь")
async def handle_help_button(message: types.Message):
    help_text = """
❓ <b>Помощь по использованию бота</b>

<b>Основные команды:</b>
/monitor - добавить товар для отслеживания
/myitems - показать ваши товары
/alerts - настроить алерты
/stats - ваша статистика

<b>Как добавить товар:</b>
1. Нажмите "➕ Добавить товар" или /monitor
2. Отправьте ссылку на товар
3. Введите название товара
4. Готово! Товар добавлен для отслеживания

<b>Как настроить алерты:</b>
1. Перейдите в "🔔 Мои алерты"
2. Выберите тип алерта
3. Настройте условия
4. Получайте уведомления!

<b>Поддерживаемые маркетплейсы:</b>
• Wildberries
• Ozon  
• Яндекс.Маркет

<b>Нужна помощь?</b>
Напишите @support_username
    """
    await message.reply(help_text, parse_mode="HTML")

# Команды аналитики
@dp.message(Command("analytics"))
async def cmd_analytics(message: types.Message):
    """Показать аналитику пользователя"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    # Генерируем отчет
    report = analytics_service.generate_analytics_report(user.id, days=30)
    
    if not report:
        await message.reply(
            "📈 <b>Аналитика недоступна</b>\n\n"
            "Добавьте товары для отслеживания, чтобы получить аналитику!",
            parse_mode="HTML"
        )
        return
    
    text = f"""
📈 <b>Аналитический отчет за {report['period_days']} дней</b>

📊 <b>Общая статистика:</b>
• Отслеживаемых товаров: {report['total_items']}
• Активных трендов: {report['active_trends']}

📈 <b>Тренды:</b>
• Растущие: {report['trends_summary']['up']} товаров
• Падающие: {report['trends_summary']['down']} товаров  
• Стабильные: {report['trends_summary']['stable']} товаров

🔥 <b>Топ изменений:</b>
"""
    
    for i, change in enumerate(report['top_changes'][:3], 1):
        trend_emoji = "📈" if change['price_change_percent'] > 0 else "📉"
        text += f"{i}. {trend_emoji} {change['price_change_percent']:+.1f}% - {change['item_id']}\n"
    
    if report['recommendations']:
        text += "\n💡 <b>Рекомендации:</b>\n"
        for rec in report['recommendations'][:3]:
            text += f"• {rec}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Подробная аналитика", callback_data="detailed_analytics")],
        [InlineKeyboardButton(text="📈 Графики цен", callback_data="price_charts")],
        [InlineKeyboardButton(text="📄 Экспорт в Excel", callback_data="export_excel")]
    ])
    
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("export"))
async def cmd_export(message: types.Message):
    """Экспорт данных в Excel"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    await message.reply("📄 <b>Генерирую Excel отчет...</b>", parse_mode="HTML")
    
    try:
        excel_data = analytics_service.export_to_excel(user.id, days=30)
        
        if not excel_data:
            await message.reply("❌ Нет данных для экспорта")
            return
        
        file = BufferedInputFile(excel_data, filename=f"analytics_report_{user.id}.xlsx")
        await message.reply_document(
            file, 
            caption="📊 <b>Аналитический отчет</b>\n\nСодержит данные о ценах, трендах и рекомендациях",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при создании отчета: {str(e)}")

@dp.message(F.text == "📈 Аналитика")
async def handle_analytics_button(message: types.Message):
    await cmd_analytics(message)

# Обработчики callback-кнопок
@dp.callback_query(F.data == "detailed_analytics")
async def handle_detailed_analytics(callback: types.CallbackQuery):
    """Показать подробную аналитику"""
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    trends = analytics_service.get_price_trends(user.id, days=30)
    
    if not trends:
        await callback.answer("📈 Нет данных для аналитики")
        return
    
    text = "📊 <b>Подробная аналитика по товарам:</b>\n\n"
    
    for name, trend in trends.items():
        trend_emoji = "📈" if trend['trend'] == 'up' else "📉" if trend['trend'] == 'down' else "➡️"
        text += f"{trend_emoji} <b>{name}</b>\n"
        text += f"   Цена: {trend['current_price']:.0f} ₽\n"
        text += f"   Изменение: {trend['price_change_percent']:+.1f}%\n"
        text += f"   Диапазон: {trend['min_price']:.0f} - {trend['max_price']:.0f} ₽\n\n"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "price_charts")
async def handle_price_charts(callback: types.CallbackQuery):
    """Показать графики цен"""
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    tracked_items = get_user_tracked_items(user.id)
    
    if not tracked_items:
        await callback.answer("📦 Нет товаров для отображения графиков")
        return
    
    # Создаем график для первого товара
    chart_data = analytics_service.create_price_chart(user.id, tracked_items[0].id, days=30)
    
    if chart_data:
        file = BufferedInputFile(chart_data, filename="price_chart.png")
        await callback.message.reply_photo(
            file,
            caption=f"📈 <b>График цены: {tracked_items[0].name}</b>\n\nЗа последние 30 дней",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Не удалось создать график")
    
    await callback.answer()

@dp.callback_query(F.data == "export_excel")
async def handle_export_excel(callback: types.CallbackQuery):
    """Экспорт в Excel"""
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    await callback.answer("📄 Генерирую Excel файл...")
    
    try:
        excel_data = analytics_service.export_to_excel(user.id, days=30)
        
        if excel_data:
            file = BufferedInputFile(excel_data, filename=f"analytics_{user.id}.xlsx")
            await callback.message.reply_document(
                file,
                caption="📊 <b>Аналитический отчет в Excel</b>",
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Нет данных для экспорта")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

# Команды подписки
@dp.message(Command("subscription"))
async def cmd_subscription(message: types.Message):
    """Показать информацию о подписке"""
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    
    subscription_info = subscription_service.get_subscription_info(user.id)
    
    text = f"""
💳 <b>Ваша подписка</b>

📋 <b>Текущий тариф:</b> {subscription_info['plan_name']}
💰 <b>Стоимость:</b> {subscription_info['price']} ₽/месяц
📅 <b>Действует до:</b> {subscription_info['expires'] or 'Бессрочно'}

📊 <b>Ваши лимиты:</b>
• Товаров: {subscription_info['limits']['tracked_items']} {'(без ограничений)' if subscription_info['limits']['tracked_items'] == -1 else ''}
• Алертов: {subscription_info['limits']['alerts']} {'(без ограничений)' if subscription_info['limits']['alerts'] == -1 else ''}
• Аналитика: {subscription_info['limits']['analytics_days']} дней

✨ <b>Доступные функции:</b>
"""
    
    for feature in subscription_info['features']:
        text += f"• {feature}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сменить тариф", callback_data="change_plan")],
        [InlineKeyboardButton(text="💳 Оплатить", callback_data="make_payment")],
        [InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_plans")]
    ])
    
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("plans"))
async def cmd_plans(message: types.Message):
    """Показать доступные тарифные планы"""
    plans = subscription_service.get_available_plans()
    
    text = "💳 <b>Доступные тарифные планы</b>\n\n"
    
    for tier, plan in plans.items():
        text += f"🔸 <b>{plan['name']}</b>\n"
        text += f"💰 {plan['price']} ₽/месяц\n"
        text += f"📦 Товаров: {plan['tracked_items_limit']} {'(без ограничений)' if plan['tracked_items_limit'] == -1 else ''}\n"
        text += f"🔔 Алертов: {plan['alerts_limit']} {'(без ограничений)' if plan['alerts_limit'] == -1 else ''}\n"
        text += f"📈 Аналитика: {plan['analytics_days']} дней\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Бесплатный", callback_data="select_plan_free")],
        [InlineKeyboardButton(text="⭐ Premium", callback_data="select_plan_premium")],
        [InlineKeyboardButton(text="🏢 Enterprise", callback_data="select_plan_enterprise")]
    ])
    
    await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(F.text == "💳 Подписка")
async def handle_subscription_button(message: types.Message):
    await cmd_subscription(message)

# Обработчики callback-кнопок подписки
@dp.callback_query(F.data == "change_plan")
async def handle_change_plan(callback: types.CallbackQuery):
    """Сменить тарифный план"""
    await callback.answer("🔄 Переходим к выбору тарифа...")
    await cmd_plans(callback.message)

@dp.callback_query(F.data == "make_payment")
async def handle_make_payment(callback: types.CallbackQuery):
    """Оплатить подписку"""
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    subscription_info = subscription_service.get_subscription_info(user.id)
    
    if subscription_info['current_tier'] == 'free':
        # Предлагаем Premium
        amount = 990
        description = "Premium подписка на 1 месяц"
    else:
        # Продление текущей подписки
        amount = subscription_info['price']
        description = f"Продление {subscription_info['plan_name']} на 1 месяц"
    
    try:
        payment_link = await payment_service.create_payment_link(
            user.id, amount, description
        )
        
        if payment_link:
            await callback.message.reply(
                f"💳 <b>Оплата подписки</b>\n\n"
                f"💰 Сумма: {amount} ₽\n"
                f"📝 Описание: {description}\n\n"
                f"🔗 <a href='{payment_link}'>Перейти к оплате</a>\n\n"
                f"После оплаты ваша подписка будет активирована автоматически.",
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Ошибка создания ссылки для оплаты")
    
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

@dp.callback_query(F.data == "compare_plans")
async def handle_compare_plans(callback: types.CallbackQuery):
    """Сравнить тарифные планы"""
    plans = subscription_service.get_available_plans()
    
    text = "📊 <b>Сравнение тарифных планов</b>\n\n"
    
    # Создаем таблицу сравнения
    features = [
        "Отслеживание товаров",
        "Алерты",
        "Аналитика",
        "Экспорт данных",
        "Графики",
        "Поддержка"
    ]
    
    text += "| Функция | Бесплатный | Premium | Enterprise |\n"
    text += "|---------|------------|---------|------------|\n"
    text += "| Товары | 3 | 50 | ∞ |\n"
    text += "| Алерты | 5 | 100 | ∞ |\n"
    text += "| Аналитика | 7 дней | 90 дней | 365 дней |\n"
    text += "| Экспорт | ❌ | ✅ | ✅ |\n"
    text += "| Графики | ❌ | ✅ | ✅ |\n"
    text += "| Поддержка | Базовая | Приоритет | Персональная |\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Выбрать Бесплатный", callback_data="select_plan_free")],
        [InlineKeyboardButton(text="⭐ Выбрать Premium", callback_data="select_plan_premium")],
        [InlineKeyboardButton(text="🏢 Выбрать Enterprise", callback_data="select_plan_enterprise")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("select_plan_"))
async def handle_select_plan(callback: types.CallbackQuery):
    """Выбрать тарифный план"""
    plan_tier = callback.data.replace("select_plan_", "")
    
    if plan_tier == "free":
        await callback.answer("✅ Вы уже используете бесплатный тариф")
        return
    
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    # Получаем информацию о плане
    plan_info = subscription_service.get_subscription_benefits(plan_tier)
    
    text = f"""
🎯 <b>Выбран тариф: {plan_info['name']}</b>

💰 <b>Стоимость:</b> {plan_info['price']} ₽/месяц

✨ <b>Что включено:</b>
"""
    
    for feature in plan_info['features']:
        text += f"• {feature}\n"
    
    text += f"\n📊 <b>Лимиты:</b>\n"
    text += f"• Товаров: {plan_info['limits']['tracked_items']} {'(без ограничений)' if plan_info['limits']['tracked_items'] == -1 else ''}\n"
    text += f"• Алертов: {plan_info['limits']['alerts']} {'(без ограничений)' if plan_info['limits']['alerts'] == -1 else ''}\n"
    text += f"• Аналитика: {plan_info['limits']['analytics_days']} дней\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить сейчас", callback_data=f"pay_{plan_tier}")],
        [InlineKeyboardButton(text="🔙 Назад к тарифам", callback_data="compare_plans")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def handle_pay_plan(callback: types.CallbackQuery):
    """Оплатить выбранный план"""
    plan_tier = callback.data.replace("pay_", "")
    
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден")
        return
    
    plan_info = subscription_service.get_subscription_benefits(plan_tier)
    
    try:
        payment_link = await payment_service.create_payment_link(
            user.id, 
            plan_info['price'], 
            f"{plan_info['name']} подписка на 1 месяц"
        )
        
        if payment_link:
            await callback.message.reply(
                f"💳 <b>Оплата тарифа {plan_info['name']}</b>\n\n"
                f"💰 Сумма: {plan_info['price']} ₽\n"
                f"📝 Описание: {plan_info['name']} подписка на 1 месяц\n\n"
                f"🔗 <a href='{payment_link}'>Перейти к оплате</a>\n\n"
                f"После успешной оплаты ваш тариф будет обновлен автоматически.",
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Ошибка создания ссылки для оплаты")
    
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

async def start_bot():
    print("🤖 Telegram бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
