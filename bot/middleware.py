"""Промежуточные слои для бота."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import settings

logger = logging.getLogger(__name__)


class TypingStatusMiddleware(BaseMiddleware):
    """Отправляет статус набора сообщения во время обработки."""

    def __init__(self, bot: Bot, interval: float = 4.0) -> None:
        self.bot = bot
        self.interval = interval

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        chat_id: Optional[int] = None
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        typing_task: Optional[asyncio.Task[None]] = None

        async def send_typing() -> None:
            try:
                while True:
                    await self.bot.send_chat_action(chat_id, ChatAction.TYPING)
                    await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                return

        if chat_id is not None:
            typing_task = asyncio.create_task(send_typing())

        try:
            return await handler(event, data)
        finally:
            if typing_task:
                typing_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await typing_task


class ErrorNotifierMiddleware(BaseMiddleware):
    """Централизованный перехват ошибок и уведомление администраторов."""

    def __init__(self, bot: Bot, admin_ids: list[int]) -> None:
        self.bot = bot
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:  # pragma: no cover - поведение проверяется интеграционно
            logger.exception("Unhandled bot error: %s", exc)
            text = "❌ Произошла непредвиденная ошибка. Команда уже разбирается."
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                if event.message:
                    await event.message.answer(text)
                with contextlib.suppress(Exception):
                    await event.answer("Ошибка обработана", show_alert=True)

            for admin_id in self.admin_ids:
                if not admin_id:
                    continue
                with contextlib.suppress(Exception):
                    await self.bot.send_message(admin_id, f"⚠️ Ошибка бота: {exc}")
            return None


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """Подключает промежуточные слои к диспетчеру."""
    admin_ids = list({settings.TELEGRAM_CHAT_ID, *settings.ADMIN_CHAT_IDS})
    dispatcher.update.outer_middleware(ErrorNotifierMiddleware(bot, admin_ids))
    dispatcher.message.outer_middleware(TypingStatusMiddleware(bot))
    dispatcher.callback_query.outer_middleware(TypingStatusMiddleware(bot))


__all__ = ("setup_middlewares", "TypingStatusMiddleware", "ErrorNotifierMiddleware")
