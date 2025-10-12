import json
from datetime import datetime, timedelta
from typing import Any, Iterable, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base, SessionLocal, engine


class ParseResult(Base):
    __tablename__ = "parse_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ExternalNews(Base):
    __tablename__ = "external_news"

    id = Column(Integer, primary_key=True, index=True)
    niche = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, default="")
    source = Column(String, nullable=False)
    published_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DirectoryEntry(Base):
    __tablename__ = "directory_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_type = Column(String, nullable=False, index=True)
    niche = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    contact_json = Column(Text)
    metadata_json = Column(Text)
    updated_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """Инициализация всех таблиц проекта."""

    # Импортируем модели для регистрации метаданных
    from profiles import models  # noqa: F401

    Base.metadata.create_all(engine)


def save_results(profile_name: str, results):
    """Сохраняет результаты парсинга в БД"""
    init_db()
    with SessionLocal() as session:
        pr = ParseResult(
            profile_name=profile_name,
            data_json=json.dumps(results, ensure_ascii=False),
            count=len(results),
            timestamp=datetime.utcnow(),
        )
        session.add(pr)
        session.commit()