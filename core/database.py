"""База данных и модели приложения."""
from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from typing import Dict, Generator, Iterable, List

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings


Base = declarative_base()


class ParseResult(Base):
    __tablename__ = "parse_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    return create_engine(settings.storage.database_url, future=True)


def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


SessionLocal = get_session_factory()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Создаёт таблицы в БД, если их ещё нет."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def save_results(profile_name: str, results: Iterable[Dict]) -> None:
    """Сохраняет результаты парсинга."""
    init_db()
    data = list(results)
    serialized = json.dumps(data, ensure_ascii=False)
    with session_scope() as session:
        record = ParseResult(
            profile_name=profile_name,
            data_json=serialized,
            count=len(data),
            timestamp=datetime.utcnow(),
        )
        session.add(record)


def get_recent_results(limit: int = 100) -> List[Dict]:
    """Возвращает последние результаты парсинга."""
    init_db()
    with session_scope() as session:
        stmt = (
            select(ParseResult)
            .order_by(ParseResult.timestamp.desc())
            .limit(limit)
        )
        rows = session.execute(stmt).scalars().all()

    return [
        {
            "profile_name": row.profile_name,
            "count": row.count,
            "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "data": json.loads(row.data_json),
        }
        for row in rows
    ]


__all__ = [
    "Base",
    "ParseResult",
    "get_engine",
    "get_recent_results",
    "get_session_factory",
    "init_db",
    "save_results",
]
