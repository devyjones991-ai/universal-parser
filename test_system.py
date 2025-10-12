#!/usr/bin/env python3
"""
Скрипт для тестирования системы Universal Parser
"""

import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, get_or_create_user, add_tracked_item, get_user_stats
from parser import UniversalParser
from analytics import analytics_service
from subscription import subscription_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Тестирование базы данных"""
    logger.info("🧪 Тестирование базы данных...")
    
    try:
        # Инициализация БД
        init_db()
        
        # Создание тестового пользователя
        user = get_or_create_user(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        
        logger.info(f"✅ Пользователь создан: {user.first_name} {user.last_name}")
        
        # Добавление тестового товара
        tracked_item = add_tracked_item(
            user_id=user.id,
            item_id="12345",
            marketplace="wb",
            name="Тестовый товар",
            url="https://example.com/product/12345"
        )
        
        logger.info(f"✅ Товар добавлен: {tracked_item.name}")
        
        # Получение статистики
        stats = get_user_stats(user.id)
        logger.info(f"✅ Статистика пользователя: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования БД: {e}")
        return False

async def test_parser():
    """Тестирование парсера"""
    logger.info("🧪 Тестирование парсера...")
    
    try:
        async with UniversalParser() as parser:
            # Тест автопарсинга
            results = await parser.parse_url("https://httpbin.org/json")
            
            if results:
                logger.info(f"✅ Парсер работает: получено {len(results)} результатов")
                return True
            else:
                logger.warning("⚠️ Парсер не вернул результатов")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования парсера: {e}")
        return False

def test_analytics():
    """Тестирование аналитики"""
    logger.info("🧪 Тестирование аналитики...")
    
    try:
        # Тест генерации отчета
        report = analytics_service.generate_analytics_report(1, days=7)
        
        if report:
            logger.info(f"✅ Аналитика работает: отчет за {report['period_days']} дней")
            return True
        else:
            logger.warning("⚠️ Аналитика не вернула данных")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования аналитики: {e}")
        return False

def test_subscription():
    """Тестирование системы подписок"""
    logger.info("🧪 Тестирование системы подписок...")
    
    try:
        # Тест получения информации о подписке
        subscription_info = subscription_service.get_subscription_info(1)
        
        if subscription_info:
            logger.info(f"✅ Подписки работают: тариф {subscription_info['plan_name']}")
            return True
        else:
            logger.warning("⚠️ Система подписок не вернула данных")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования подписок: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск тестирования системы Universal Parser...")
    
    tests = [
        ("База данных", test_database()),
        ("Парсер", test_parser()),
        ("Аналитика", test_analytics()),
        ("Подписки", test_subscription())
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Тест: {test_name}")
        logger.info(f"{'='*50}")
        
        if asyncio.iscoroutine(test_coro):
            result = await test_coro
        else:
            result = test_coro
            
        results.append((test_name, result))
        
        if result:
            logger.info(f"✅ {test_name}: ПРОЙДЕН")
        else:
            logger.error(f"❌ {test_name}: ПРОВАЛЕН")
    
    # Итоговый отчет
    logger.info(f"\n{'='*50}")
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 Все тесты пройдены! Система готова к работе.")
        return 0
    else:
        logger.error("💥 Некоторые тесты провалены. Проверьте конфигурацию.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
