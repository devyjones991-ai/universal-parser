"""Пакет Telegram-бота."""
from .commands import bot, dp, get_bot_components
from .runner import start_bot

__all__ = ["bot", "dp", "get_bot_components", "start_bot"]
