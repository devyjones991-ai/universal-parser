import asyncio
import logging
from tg_commands import start_bot
from scheduler import start_monitoring, stop_monitoring

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Главная функция приложения"""
    print("🚦 Universal Parser стартует...")
    
    try:
        # Запускаем планировщик мониторинга
        await start_monitoring()
        
        # Запускаем Telegram-бот
        await start_bot()
        
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        # Останавливаем планировщик
        await stop_monitoring()
        print("✅ Приложение остановлено")

if __name__ == "__main__":
    asyncio.run(main())
