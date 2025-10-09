"""Модуль для работы с базой перевозчиков и интеграциями."""
from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

__all__ = [
    "Carrier",
    "DEFAULT_DB_PATH",
    "initialise_storage",
    "add_carrier",
    "bulk_upsert_carriers",
    "find_carriers",
    "get_carrier_by_id",
]


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "logistics.db"


@dataclass(slots=True)
class Carrier:
    """Представление перевозчика в системе."""

    id: Optional[int]
    name: str
    regions: List[str]
    vehicle_types: List[str]
    phone: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Carrier":
        return cls(
            id=row["id"],
            name=row["name"],
            regions=row["regions"].split(",") if row["regions"] else [],
            vehicle_types=row["vehicle_types"].split(",") if row["vehicle_types"] else [],
            phone=row["phone"],
            email=row["email"],
            rating=row["rating"],
        )

    def to_record(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "regions": ",".join(self.regions),
            "vehicle_types": ",".join(self.vehicle_types),
            "phone": self.phone,
            "email": self.email,
            "rating": self.rating,
        }


def _get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialise_storage(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Создаёт таблицы для хранения перевозчиков."""

    with contextlib.closing(_get_connection(db_path)) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS carriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                regions TEXT NOT NULL,
                vehicle_types TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                rating REAL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_carriers_name ON carriers(name)"
        )


def add_carrier(carrier: Carrier, db_path: Path = DEFAULT_DB_PATH) -> int:
    """Добавляет нового перевозчика и возвращает его идентификатор."""

    with contextlib.closing(_get_connection(db_path)) as conn, conn:
        cursor = conn.execute(
            """
            INSERT INTO carriers (name, regions, vehicle_types, phone, email, rating)
            VALUES (:name, :regions, :vehicle_types, :phone, :email, :rating)
            """,
            carrier.to_record(),
        )
        return int(cursor.lastrowid)


def bulk_upsert_carriers(carriers: Iterable[Carrier], db_path: Path = DEFAULT_DB_PATH) -> None:
    """Массовое обновление или добавление перевозчиков по имени."""

    with contextlib.closing(_get_connection(db_path)) as conn, conn:
        for carrier in carriers:
            record = carrier.to_record()
            existing = conn.execute(
                "SELECT id FROM carriers WHERE name = :name", {"name": carrier.name}
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE carriers
                    SET regions = :regions,
                        vehicle_types = :vehicle_types,
                        phone = :phone,
                        email = :email,
                        rating = :rating
                    WHERE id = :id
                    """,
                    {**record, "id": existing["id"]},
                )
            else:
                conn.execute(
                    """
                    INSERT INTO carriers (name, regions, vehicle_types, phone, email, rating)
                    VALUES (:name, :regions, :vehicle_types, :phone, :email, :rating)
                    """,
                    record,
                )


def _build_filters(
    query: Optional[str], regions: Optional[Iterable[str]], min_rating: Optional[float]
) -> List[str]:
    filters: List[str] = []
    if query:
        filters.append("name LIKE :query")
    if regions:
        region_list = list(regions)
        if region_list:
            region_clauses = [f"regions LIKE :region_{i}" for i in range(len(region_list))]
            filters.append("(" + " OR ".join(region_clauses) + ")")
    if min_rating is not None:
        filters.append("rating >= :min_rating")
    return filters


def find_carriers(
    *,
    query: Optional[str] = None,
    regions: Optional[Iterable[str]] = None,
    min_rating: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
    db_path: Path = DEFAULT_DB_PATH,
) -> List[Carrier]:
    """Ищет перевозчиков по критериям."""

    initialise_storage(db_path)
    sql = "SELECT * FROM carriers"
    region_list: List[str] = list(regions) if regions else []
    filters = _build_filters(query, region_list, min_rating)
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += (
        " ORDER BY "
        "CASE WHEN rating IS NULL THEN 1 ELSE 0 END ASC, "
        "rating DESC, name ASC LIMIT :limit OFFSET :offset"
    )

    params: Dict[str, Any] = {"limit": limit, "offset": max(0, offset)}
    if query:
        params["query"] = f"%{query.strip()}%"
    for i, region in enumerate(region_list):
        params[f"region_{i}"] = f"%{region}%"
    if min_rating is not None:
        params["min_rating"] = float(min_rating)

    with contextlib.closing(_get_connection(db_path)) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Carrier.from_row(row) for row in rows]


def get_carrier_by_id(carrier_id: int, db_path: Path = DEFAULT_DB_PATH) -> Optional[Carrier]:
    initialise_storage(db_path)
    with contextlib.closing(_get_connection(db_path)) as conn:
        row = conn.execute("SELECT * FROM carriers WHERE id = ?", (carrier_id,)).fetchone()
    return Carrier.from_row(row) if row else None
