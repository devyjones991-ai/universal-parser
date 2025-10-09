"""Инициализация Telegram-бота и диспетчера."""
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from .middleware import setup_middlewares

bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML"),
)
dispatcher_storage = MemoryStorage()
dp = Dispatcher(storage=dispatcher_storage)

setup_middlewares(dp, bot)

__all__ = ("bot", "dp")
