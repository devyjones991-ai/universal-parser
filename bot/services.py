"""Простейшее хранение данных для FSM сценариев."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass(slots=True)
class Alert:
    name: str
    url: str
    conditions: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(slots=True)
class ImportBatch:
    items: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)

_alerts: List[Alert] = []
_import_batches: List[ImportBatch] = []

def add_alert(alert: Alert) -> None:
    _alerts.append(alert)

def get_alerts() -> List[Alert]:
    return list(_alerts)

def register_import(batch: ImportBatch) -> None:
    _import_batches.append(batch)

def get_imports() -> List[ImportBatch]:
    return list(_import_batches)

def reset_storage() -> None:
    _alerts.clear()
    _import_batches.clear()

__all__ = (
    "Alert",
    "ImportBatch",
    "add_alert",
    "get_alerts",
    "register_import",
    "get_imports",
    "reset_storage",
)
