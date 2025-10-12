#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных Universal Parser
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, Base, engine
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Инициализация базы данных"""
    try:
        logger.info("🚀 Инициализация базы данных...")
        
        # Создаем все таблицы
        init_db()
        
        logger.info("✅ База данных успешно инициализирована!")
        logger.info(f"📁 Путь к БД: {settings.DATABASE_URL}")
        
        # Показываем созданные таблицы
        inspector = engine.inspect()
        tables = inspector.get_table_names()
        
        logger.info("📊 Созданные таблицы:")
        for table in tables:
            logger.info(f"  • {table}")
        
        logger.info("\n🎉 Готово! Теперь можно запускать приложение.")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
