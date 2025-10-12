import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import settings

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
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


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
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class ItemSnapshot(Base):
    __tablename__ = "item_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    stock = Column(Integer, nullable=True)
    availability = Column(String, nullable=True)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    price_history = relationship(
        "PriceHistory", back_populates="snapshot", cascade="all, delete-orphan"
    )