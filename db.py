import json
from datetime import datetime, timedelta
from typing import Any, Iterable, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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


def get_recent_results(limit=100):
    """Получить последние результаты из БД"""
    init_db()
    with SessionLocal() as session:
        query = session.query(ParseResult).order_by(ParseResult.timestamp.desc()).limit(limit)
        return [
            {
                "profile_name": row.profile_name,
                "count": row.count,
                "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "data": json.loads(row.data_json),
            }
            for row in query
        ]


def cache_news_items(niche: str, region: str, items: Iterable[dict]):
    init_db()
    with SessionLocal() as session:
        session.query(ExternalNews).filter_by(niche=niche, region=region).delete()
        now = datetime.utcnow()
        for item in items:
            session.add(
                ExternalNews(
                    niche=niche,
                    region=region,
                    title=item["title"],
                    url=item["url"],
                    summary=item.get("summary", ""),
                    source=item.get("source", "External"),
                    published_at=_ensure_datetime(item.get("published_at")),
                    fetched_at=now,
                )
            )
        session.commit()


def get_cached_news(niche: str, region: str, ttl_minutes: int = 60) -> List[dict]:
    init_db()
    with SessionLocal() as session:
        records: List[ExternalNews] = (
            session.query(ExternalNews)
            .filter_by(niche=niche, region=region)
            .order_by(ExternalNews.published_at.desc())
            .all()
        )
        if not records:
            return []

        threshold = datetime.utcnow() - timedelta(minutes=ttl_minutes)
        if any(record.fetched_at < threshold for record in records):
            return []

        return [
            {
                "title": record.title,
                "url": record.url,
                "summary": record.summary,
                "source": record.source,
                "published_at": record.published_at.isoformat(),
                "niche": record.niche,
                "region": record.region,
            }
            for record in records
        ]


def cache_directory_entries(entry_type: str, niche: str, region: str, items: Iterable[dict]):
    init_db()
    with SessionLocal() as session:
        session.query(DirectoryEntry).filter_by(
            entry_type=entry_type, niche=niche, region=region
        ).delete()
        now = datetime.utcnow()
        for item in items:
            contact = item.get("contact_info")
            metadata = item.get("metadata")
            session.add(
                DirectoryEntry(
                    entry_type=entry_type,
                    niche=niche,
                    region=region,
                    name=item["name"],
                    contact_json=json.dumps(contact, ensure_ascii=False)
                    if contact is not None
                    else None,
                    metadata_json=json.dumps(metadata, ensure_ascii=False)
                    if metadata is not None
                    else None,
                    updated_at=_ensure_datetime(item.get("updated_at")),
                    fetched_at=now,
                )
            )
        session.commit()


def get_directory_entries(entry_type: str, niche: str, region: str, ttl_hours: int = 12) -> List[dict]:
    init_db()
    with SessionLocal() as session:
        records: List[DirectoryEntry] = (
            session.query(DirectoryEntry)
            .filter_by(entry_type=entry_type, niche=niche, region=region)
            .order_by(DirectoryEntry.name.asc())
            .all()
        )
        if not records:
            return []

        threshold = datetime.utcnow() - timedelta(hours=ttl_hours)
        if any(record.fetched_at < threshold for record in records):
            return []

        results = []
        for record in records:
            contact = json.loads(record.contact_json) if record.contact_json else None
            metadata = json.loads(record.metadata_json) if record.metadata_json else None
            results.append(
                {
                    "name": record.name,
                    "entry_type": record.entry_type,
                    "niche": record.niche,
                    "region": record.region,
                    "contact_info": contact,
                    "metadata": metadata,
                    "updated_at": record.updated_at.isoformat(),
                }
            )
        return results


def _ensure_datetime(value: Optional[Any]) -> datetime:
    if value is None:
        return datetime.utcnow()

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.utcnow()
