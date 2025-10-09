from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import db  # noqa: E402,F401  # Регистрация моделей результатов парсинга
from database import Base  # noqa: E402
from profiles import models  # noqa: E402,F401  # Регистрация пользовательских моделей
from profiles.service import ProfileService  # noqa: E402


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    db_session = TestingSession()
    try:
        yield db_session
    finally:
        db_session.close()


def create_profile(service: ProfileService, telegram_id: int = 12345):
    return service.create_profile(
        telegram_id=telegram_id,
        username="tester",
        full_name="Test User",
        language_code="ru",
    )


def test_create_and_get_profile(session):
    service = ProfileService(session)
    profile = create_profile(service)

    assert profile.id is not None

    fetched = service.get_profile(profile.telegram_id)
    assert fetched is not None
    assert fetched.id == profile.id
    assert fetched.username == "tester"


def test_update_profile(session):
    service = ProfileService(session)
    profile = create_profile(service)

    updated = service.update_profile(profile, username="new_user", full_name="New Name")
    assert updated.username == "new_user"
    assert updated.full_name == "New Name"


def test_get_or_create_updates_existing_profile(session):
    service = ProfileService(session)
    profile = create_profile(service)

    fetched = service.get_or_create_profile(
        profile.telegram_id,
        username="updated",
        full_name="Updated Name",
    )

    assert fetched.id == profile.id
    assert fetched.username == "updated"
    assert fetched.full_name == "Updated Name"


def test_settings_crud(session):
    service = ProfileService(session)
    profile = create_profile(service)

    service.set_setting(profile, "format", "excel")
    service.set_setting(profile, "language", "ru")

    setting = service.get_setting(profile, "format")
    assert setting is not None
    assert setting.value == "excel"

    settings_dict = {s.key: s.value for s in service.list_settings(profile)}
    assert settings_dict == {"format": "excel", "language": "ru"}

    removed = service.delete_setting(profile, "format")
    assert removed is True
    assert service.get_setting(profile, "format") is None


def test_history_operations(session):
    service = ProfileService(session)
    profile = create_profile(service)

    service.add_history(profile, "command_start", payload="/start")
    service.add_history(profile, "command_run", payload="/run test")

    history = service.list_history(profile)
    assert len(history) == 2
    assert history[0].action == "command_run"

    deleted_count = service.clear_history(profile)
    assert deleted_count == 2
    assert service.list_history(profile) == []
