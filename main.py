import asyncio
from tg_commands import start_bot

if __name__ == "__main__":
    # Можно добавить логи, интеграции, автозапуск задач
    print("🚦 Universal Parser стартует...")
    # Просто запускаем Telegram-бот
    asyncio.run(start_bot())
