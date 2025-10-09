from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Alert(Base):
    """Модель алерта на изменение значений по SKU."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    condition_type = Column(String, nullable=False)
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
    last_value = Column(Float, nullable=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    def as_dict(self) -> dict:
        """Сериализация модели для удобства отображения."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "sku": self.sku,
            "condition_type": self.condition_type,
            "threshold": self.threshold,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_value": self.last_value,
            "last_triggered_at": self.last_triggered_at,
        }

    def __repr__(self) -> str:  # pragma: no cover - отладочное представление
        return (
            f"Alert(id={self.id}, user_id={self.user_id}, sku='{self.sku}', "
            f"condition_type='{self.condition_type}', threshold={self.threshold}, "
            f"is_active={self.is_active})"
        )
