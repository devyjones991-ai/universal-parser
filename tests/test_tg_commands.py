import asyncio
import datetime
import os
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("UVLOOP_NO_EXTENSION", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
os.environ.setdefault("TELEGRAM_CHAT_ID", "1")

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import (
    AnswerCallbackQuery,
    SendChatAction,
    SendDocument,
    SendMessage,
)
from aiogram.types import Message, Update

from bot.middleware import setup_middlewares
from bot.services import get_alerts, get_imports, reset_storage
from config import settings
settings.TELEGRAM_CHAT_ID = 1
settings.ADMIN_CHAT_IDS = [1]
settings.TELEGRAM_BOT_TOKEN = "123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
from tg_commands import router



class DummySession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.sent_messages: List[SendMessage] = []
        self.updates: List[Any] = []
        self.messages: List[Message] = []

    async def close(self) -> None:
        return None

    async def stream_content(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ):
        if False:
            yield b""
        return

    async def make_request(self, bot: Bot, method, timeout: Optional[int] = None):
        self.updates.append(method)
        if isinstance(method, SendMessage):
            self.sent_messages.append(method)
            message = Message.model_validate(
                {
                    "message_id": len(self.messages) + 1,
                    "date": datetime.datetime.now(datetime.UTC),
                    "chat": {"id": method.chat_id, "type": "private"},
                    "from": {"id": method.chat_id, "is_bot": False, "first_name": "Bot"},
                    "text": method.text or "",
                }
            )
            self.messages.append(message)
            return message
        if isinstance(method, SendDocument):
            message = Message.model_validate(
                {
                    "message_id": len(self.messages) + 1,
                    "date": datetime.datetime.now(datetime.UTC),
                    "chat": {"id": method.chat_id, "type": "private"},
                    "from": {"id": method.chat_id, "is_bot": False, "first_name": "Bot"},
                    "document": {"file_id": "test", "file_unique_id": "test", "file_name": "doc"},
                }
            )
            self.messages.append(message)
            return message
        if isinstance(method, (SendChatAction, AnswerCallbackQuery)):
            return True
        return True


class AiogramTestClient:
    def __init__(self) -> None:
        self.session = DummySession()
        self.bot = Bot(token="123456:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", session=self.session)
        self.dispatcher = Dispatcher(storage=MemoryStorage())
        setup_middlewares(self.dispatcher, self.bot)
        router._parent_router = None
        self.dispatcher.include_router(router)
        self._update_id = 0

    @property
    def last_bot_text(self) -> Optional[str]:
        for method in reversed(self.session.sent_messages):
            if isinstance(method, SendMessage):
                return method.text
        return None

    async def send_message(self, text: str, user_id: int = 1) -> None:
        self._update_id += 1
        update = Update.model_validate(
            {
                "update_id": self._update_id,
                "message": {
                    "message_id": self._update_id,
                    "date": datetime.datetime.now(datetime.UTC),
                    "chat": {"id": user_id, "type": "private"},
                    "from": {"id": user_id, "is_bot": False, "first_name": "Tester"},
                    "text": text,
                },
            }
        )
        await self.dispatcher.feed_update(self.bot, update)

    async def send_callback(self, data: str, message: Optional[Message] = None, user_id: int = 1) -> None:
        self._update_id += 1
        source_message = message or self.session.messages[-1]
        update = Update.model_validate(
            {
                "update_id": self._update_id,
                "callback_query": {
                    "id": str(self._update_id),
                    "from": {"id": user_id, "is_bot": False, "first_name": "Tester"},
                    "chat_instance": "test",
                    "data": data,
                    "message": source_message.model_dump(),
                },
            }
        )
        await self.dispatcher.feed_update(self.bot, update)


@pytest.mark.asyncio
async def test_alert_fsm_flow() -> None:
    reset_storage()
    client = AiogramTestClient()

    await client.send_message("/start")
    client.session.sent_messages.clear()

    await client.send_message("➕ Добавить алерт")
    assert "Введите название" in (client.last_bot_text or "")

    await client.send_message("Тестовый алерт")
    assert "Укажите URL" in (client.last_bot_text or "")

    await client.send_message("https://example.com")
    assert "ключевые слова" in (client.last_bot_text or "")

    await client.send_message("цена, скидка")
    assert "Алерт «Тестовый алерт»" in (client.last_bot_text or "")

    alerts = get_alerts()
    assert len(alerts) == 1
    assert alerts[0].url == "https://example.com"
    assert alerts[0].conditions == ["цена", "скидка"]


@pytest.mark.asyncio
async def test_import_fsm_flow() -> None:
    reset_storage()
    client = AiogramTestClient()

    await client.send_message("/start")
    client.session.sent_messages.clear()

    await client.send_message("📥 Импорт списка")
    assert "Отправьте список" in (client.last_bot_text or "")

    await client.send_message("https://example.com\nhttps://example.org")
    assert "Получено 2 элементов" in (client.last_bot_text or "")

    await client.send_callback("import:confirm")
    assert "Импорт сохранён" in (client.last_bot_text or "")

    batches = get_imports()
    assert len(batches) == 1
    assert batches[0].items == ["https://example.com", "https://example.org"]
