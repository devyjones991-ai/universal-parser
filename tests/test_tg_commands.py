import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db import Base  # noqa: E402
from profiles import models  # noqa: E402, F401 - регистрация моделей
from profiles.tip_service import (  # noqa: E402
    TipNotFoundError,
    approve_tip,
    archive_tip,
    create_tip,
    delete_tip,
    get_tip_rating,
    get_top_tips,
    record_feedback,
    reject_tip,
    update_tip_content,
)


@pytest.fixture()
def session(tmp_path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path}/tips.db", future=True)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_tip_crud_and_rating_flow(session: Session):
    tip = create_tip(session, author_id=1, author_username="user", content="  Первый совет  ")
    assert tip.content == "Первый совет"
    tip_id = tip.id

    tip = update_tip_content(session, tip_id, "Обновлённый совет")
    assert tip.content == "Обновлённый совет"

    tip = approve_tip(session, tip_id)
    assert tip.is_approved is True

    record_feedback(session, tip_id, user_id=11, value=1)
    record_feedback(session, tip_id, user_id=22, value=1)
    tip = record_feedback(session, tip_id, user_id=22, value=-1)
    assert tip.rating == 0
    assert get_tip_rating(session, tip_id) == 0

    top = get_top_tips(session, limit=5)
    assert len(top) == 1 and top[0].id == tip_id

    tip = archive_tip(session, tip_id, value=True)
    assert tip.is_archived is True
    assert get_top_tips(session) == []

    tip = archive_tip(session, tip_id, value=False)
    assert tip.is_archived is False

    tip = reject_tip(session, tip_id)
    assert tip.is_archived is True and tip.is_approved is False

    delete_tip(session, tip_id)
    assert session.get(models.UserTip, tip_id) is None


def test_tip_errors(session: Session):
    with pytest.raises(TipNotFoundError):
        update_tip_content(session, 999, "Нет совета")

    with pytest.raises(ValueError):
        record_feedback(session, 0, user_id=1, value=2)
