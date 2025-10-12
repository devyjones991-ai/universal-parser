import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
from datetime import datetime, timezone

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class ParseResult(Base):
    __tablename__ = "parse_results"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


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
            timestamp=datetime.now(timezone.utc)
        )
        session.add(pr)
        session.commit()