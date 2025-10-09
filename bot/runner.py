"""Запуск бота и жизненный цикл очереди задач."""
from __future__ import annotations

from aiogram import Dispatcher

from .context import bot, dp, task_queue


async def on_startup(dispatcher: Dispatcher) -> None:  # noqa: ARG001 - сигнатура по требованию aiogram
    await task_queue.start()


async def on_shutdown(dispatcher: Dispatcher) -> None:  # noqa: ARG001
    await task_queue.drain()
    await task_queue.stop()
    await bot.session.close()


async def start_bot() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


__all__ = ["start_bot"]
