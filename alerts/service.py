from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterable, List

from sqlalchemy.orm import Session

from db import SessionLocal, init_db
from profiles.models import Alert


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AlertServiceError(Exception):
    """Базовое исключение сервиса алертов."""


class AlertNotFoundError(AlertServiceError):
    """Выбрасывается при обращении к несуществующему алерту."""


class AlertService:
    """Сервис для управления алертами пользователей."""

    def __init__(self, session_factory=SessionLocal, auto_init: bool = True):
        self._session_factory = session_factory
        if auto_init:
            init_db()

    @contextmanager
    def _session(self) -> Iterable[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def add_alert(
        self, user_id: int, sku: str, condition_type: str, threshold: float
    ) -> Alert:
        return await asyncio.to_thread(
            self._add_alert, user_id, sku, condition_type, float(threshold)
        )

    def _add_alert(self, user_id: int, sku: str, condition_type: str, threshold: float) -> Alert:
        with self._session() as session:
            alert = Alert(
                user_id=user_id,
                sku=sku,
                condition_type=condition_type,
                threshold=threshold,
                is_active=True,
            )
            session.add(alert)
            session.flush()
            session.refresh(alert)
            return alert

    async def list_alerts(self, user_id: int) -> List[Alert]:
        return await asyncio.to_thread(self._list_alerts, user_id)

    def _list_alerts(self, user_id: int) -> List[Alert]:
        with self._session() as session:
            alerts = (
                session.query(Alert)
                .filter(Alert.user_id == user_id)
                .order_by(Alert.created_at.desc())
                .all()
            )
            return alerts

    async def delete_alert(self, user_id: int, alert_id: int) -> None:
        await asyncio.to_thread(self._delete_alert, user_id, alert_id)

    def _delete_alert(self, user_id: int, alert_id: int) -> None:
        with self._session() as session:
            alert = self._require_owner(session, user_id, alert_id)
            session.delete(alert)

    async def pause_alert(self, user_id: int, alert_id: int) -> Alert:
        return await asyncio.to_thread(self._set_active_state, user_id, alert_id, False)

    async def resume_alert(self, user_id: int, alert_id: int) -> Alert:
        return await asyncio.to_thread(self._set_active_state, user_id, alert_id, True)

    def _set_active_state(self, user_id: int, alert_id: int, state: bool) -> Alert:
        with self._session() as session:
            alert = self._require_owner(session, user_id, alert_id)
            alert.is_active = state
            alert.updated_at = _utcnow()
            session.add(alert)
            session.flush()
            session.refresh(alert)
            return alert

    async def get_active_alerts(self) -> List[Alert]:
        return await asyncio.to_thread(self._get_active_alerts)

    def _get_active_alerts(self) -> List[Alert]:
        with self._session() as session:
            alerts = (
                session.query(Alert)
                .filter(Alert.is_active.is_(True))
                .order_by(Alert.updated_at.desc())
                .all()
            )
            return alerts

    async def mark_triggered(
        self, alert_id: int, value: float, *, deactivate: bool = False
    ) -> Alert:
        return await asyncio.to_thread(self._mark_triggered, alert_id, float(value), deactivate)

    def _mark_triggered(self, alert_id: int, value: float, deactivate: bool) -> Alert:
        with self._session() as session:
            alert = self._get_alert(session, alert_id)
            alert.last_value = value
            alert.last_triggered_at = _utcnow()
            if deactivate:
                alert.is_active = False
            alert.updated_at = _utcnow()
            session.add(alert)
            session.flush()
            session.refresh(alert)
            return alert

    async def get_alert(self, user_id: int, alert_id: int) -> Alert:
        return await asyncio.to_thread(self._get_alert_for_owner, user_id, alert_id)

    def _get_alert_for_owner(self, user_id: int, alert_id: int) -> Alert:
        with self._session() as session:
            return self._require_owner(session, user_id, alert_id)

    def _get_alert(self, session: Session, alert_id: int) -> Alert:
        alert = session.query(Alert).filter(Alert.id == alert_id).one_or_none()
        if alert is None:
            raise AlertNotFoundError(f"Алерт с id={alert_id} не найден")
        return alert

    def _require_owner(self, session: Session, user_id: int, alert_id: int) -> Alert:
        alert = self._get_alert(session, alert_id)
        if alert.user_id != user_id:
            raise AlertServiceError("У вас нет прав на изменение этого алерта")
        return alert
