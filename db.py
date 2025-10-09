import json
import time
from datetime import datetime
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
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ParseResult(Base):
    __tablename__ = "parse_results"
    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    price_history = relationship(
        "PriceHistory", back_populates="snapshot", cascade="all, delete-orphan"
    )
    inventory_history = relationship(
        "InventoryHistory", back_populates="snapshot", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("item_snapshots.id"), nullable=False)
    profile_name = Column(String, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    price_change = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    snapshot = relationship("ItemSnapshot", back_populates="price_history")


class InventoryHistory(Base):
    __tablename__ = "inventory_history"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("item_snapshots.id"), nullable=False)
    profile_name = Column(String, index=True, nullable=False)
    item_id = Column(String, index=True, nullable=False)
    stock_level = Column(Integer, nullable=True)
    availability = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    snapshot = relationship("ItemSnapshot", back_populates="inventory_history")

def init_db():
    Base.metadata.create_all(engine)

def _extract_item_id(item: Dict[str, Any], fallback_index: int, profile_name: str) -> str:
    for key in ("id", "item_id", "sku", "product_id", "uuid", "url", "link"):
        value = item.get(key)
        if value:
            return str(value)
    return f"{profile_name}:{fallback_index}"


def _extract_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("\xa0", " ").replace(",", ".")
        digits = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")
        if digits:
            try:
                return float(digits)
            except ValueError:
                return None
    return None


def _extract_currency(value: Any) -> Optional[str]:
    if isinstance(value, str):
        value = value.strip()
        if len(value) <= 8 and value.isalpha():
            return value.upper()
        for symbol, code in {"₽": "RUB", "$": "USD", "€": "EUR"}.items():
            if symbol in value:
                return code
    return None


def _extract_stock(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            try:
                return int(digits)
            except ValueError:
                return None
    return None


def _compute_price_diff(
    session, profile_name: str, item_id: str, new_price: Optional[float]
) -> Dict[str, Optional[float]]:
    if new_price is None:
        return {"price_change": None, "change_percent": None}

    last_entry = (
        session.query(PriceHistory)
        .filter(PriceHistory.profile_name == profile_name, PriceHistory.item_id == item_id)
        .order_by(PriceHistory.created_at.desc())
        .first()
    )
    if not last_entry or last_entry.price is None:
        return {"price_change": None, "change_percent": None}

    diff = new_price - last_entry.price
    percent = (diff / last_entry.price * 100.0) if last_entry.price else None
    return {"price_change": diff, "change_percent": percent}


def save_results(profile_name: str, results):
    """Сохраняет результаты парсинга в БД"""
    init_db()
    timestamp = datetime.utcnow()
    with SessionLocal() as session:
        pr = ParseResult(
            profile_name=profile_name,
            data_json=json.dumps(results, ensure_ascii=False),
            count=len(results),
            timestamp=timestamp,
        )
        session.add(pr)
        session.flush()

        for index, item in enumerate(results):
            item_id = _extract_item_id(item, index, profile_name)
            price = _extract_price(item.get("price"))
            currency = (
                item.get("currency")
                or _extract_currency(item.get("currency"))
                or _extract_currency(str(item.get("price", "")))
            )
            stock = _extract_stock(item.get("stock") or item.get("availability") or item.get("inventory"))
            availability = item.get("availability")

            snapshot = ItemSnapshot(
                profile_name=profile_name,
                item_id=item_id,
                name=item.get("name") or item.get("title"),
                category=item.get("category"),
                price=price,
                currency=currency,
                stock=stock,
                availability=availability,
                data_json=json.dumps(item, ensure_ascii=False),
                created_at=timestamp,
            )
            session.add(snapshot)
            session.flush()

            price_diff = _compute_price_diff(session, profile_name, item_id, price)
            price_entry = PriceHistory(
                snapshot_id=snapshot.id,
                profile_name=profile_name,
                item_id=item_id,
                price=price,
                currency=currency,
                price_change=price_diff["price_change"],
                change_percent=price_diff["change_percent"],
                created_at=timestamp,
            )
            session.add(price_entry)

            inventory_entry = InventoryHistory(
                snapshot_id=snapshot.id,
                profile_name=profile_name,
                item_id=item_id,
                stock_level=stock,
                availability=availability,
                created_at=timestamp,
            )
            session.add(inventory_entry)

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
                "timestamp": row.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "data": json.loads(row.data_json)
            }
            for row in query
        ]
