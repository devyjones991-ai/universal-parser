import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from alerts.checker import AlertChecker
from alerts.service import AlertService
from db import Base


@pytest.fixture()
def session_factory(tmp_path):
    db_path = tmp_path / "alerts.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def alert_service(session_factory):
    return AlertService(session_factory=session_factory, auto_init=False)


@pytest.mark.asyncio()
async def test_alert_crud(alert_service):
    alert = await alert_service.add_alert(123, "SKU-1", "lt", 100)

    alerts = await alert_service.list_alerts(123)
    assert len(alerts) == 1
    assert alerts[0].sku == "SKU-1"

    paused = await alert_service.pause_alert(123, alert.id)
    assert not paused.is_active

    resumed = await alert_service.resume_alert(123, alert.id)
    assert resumed.is_active

    await alert_service.delete_alert(123, alert.id)
    alerts_after_delete = await alert_service.list_alerts(123)
    assert alerts_after_delete == []


class DummyParser:
    def __init__(self, data):
        self._data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    async def parse_by_profile(self, profile_name, **kwargs):
        return self._data


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        )


@pytest.mark.asyncio()
async def test_alert_checker_triggers_once(alert_service):
    await alert_service.add_alert(321, "SKU-2", "lt", 50)

    fake_bot = FakeBot()

    # Передаем фабрику, возвращающую асинхронный контекстный менеджер
    checker = AlertChecker(
        bot=fake_bot,
        service=alert_service,
        parser_factory=lambda: DummyParser([{"price": 40}]),
    )

    await checker.run_once()

    assert len(fake_bot.messages) == 1
    message = fake_bot.messages[0]
    assert "SKU-2" in message["text"]
    assert "40.00" in message["text"]
    assert message["reply_markup"] is not None
    assert message["reply_markup"].inline_keyboard

    # Повторная проверка с тем же значением не должна отправлять сообщение
    fake_bot.messages.clear()
    await checker.run_once()
    assert fake_bot.messages == []

    alerts = await alert_service.list_alerts(321)
    assert alerts[0].last_value == 40
