"""Глобальный контекст бота."""
from __future__ import annotations

from aiogram import Bot, Dispatcher

from core import configure_logging, create_task_queue, get_settings

settings = get_settings()
configure_logging()

bot = Bot(token=settings.telegram_bot_token)
dp = Dispatcher()
task_queue = create_task_queue(settings.queue)

__all__ = ["bot", "dp", "settings", "task_queue"]
