"""Сервисные функции для работы с советами."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from profiles.models import TipFeedback, UserTip


class TipNotFoundError(ValueError):
    """Исключение при попытке работы с отсутствующим советом."""


def create_tip(
    session: Session,
    *,
    author_id: int,
    author_username: Optional[str],
    content: str,
    approved: bool = False,
) -> UserTip:
    """Создаёт совет и сохраняет его в БД."""

    tip = UserTip(
        author_id=author_id,
        author_username=author_username,
        content=content.strip(),
        is_approved=approved,
        approved_at=datetime.utcnow() if approved else None,
    )
    session.add(tip)
    session.commit()
    session.refresh(tip)
    return tip


def update_tip_content(session: Session, tip_id: int, new_content: str) -> UserTip:
    """Обновляет содержимое совета."""

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    tip.content = new_content.strip()
    session.commit()
    session.refresh(tip)
    return tip


def approve_tip(session: Session, tip_id: int) -> UserTip:
    """Отмечает совет как одобренный."""

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    tip.is_approved = True
    tip.approved_at = datetime.utcnow()
    session.commit()
    session.refresh(tip)
    return tip


def archive_tip(session: Session, tip_id: int, value: bool = True) -> UserTip:
    """Переключает флаг архивации совета."""

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    tip.is_archived = value
    session.commit()
    session.refresh(tip)
    return tip


def delete_tip(session: Session, tip_id: int) -> None:
    """Удаляет совет полностью."""

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    session.delete(tip)
    session.commit()


def reject_tip(session: Session, tip_id: int) -> UserTip:
    """Отклоняет совет и отправляет его в архив."""

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    tip.is_approved = False
    tip.is_archived = True
    session.commit()
    session.refresh(tip)
    return tip


def record_feedback(session: Session, tip_id: int, user_id: int, value: int) -> UserTip:
    """Добавляет или обновляет реакцию пользователя."""

    if value not in (-1, 1):
        raise ValueError("Допустимы только значения -1 или 1")

    tip = session.get(UserTip, tip_id)
    if tip is None:
        raise TipNotFoundError(f"Совет #{tip_id} не найден")

    feedback = (
        session.execute(
            select(TipFeedback).where(
                TipFeedback.tip_id == tip_id,
                TipFeedback.user_id == user_id,
            )
        )
        .scalars()
        .first()
    )

    if feedback is None:
        feedback = TipFeedback(tip_id=tip_id, user_id=user_id, value=value)
        session.add(feedback)
    else:
        feedback.value = value

    try:
        session.commit()
    except IntegrityError as exc:  # pragma: no cover - защита от гонок
        session.rollback()
        raise ValueError("Не удалось сохранить оценку") from exc

    session.refresh(tip)
    return tip


def get_tip_rating(session: Session, tip_id: int) -> int:
    """Возвращает суммарный рейтинг совета."""

    rating_query = session.execute(
        select(func.coalesce(func.sum(TipFeedback.value), 0)).where(TipFeedback.tip_id == tip_id)
    )
    return int(rating_query.scalar_one())


def get_top_tips(
    session: Session,
    *,
    limit: int = 5,
    only_approved: bool = True,
    exclude_archived: bool = True,
    period_days: Optional[int] = None,
) -> List[UserTip]:
    """Возвращает советы, отсортированные по рейтингу."""

    stmt = select(UserTip).order_by(UserTip.created_at.desc())

    if only_approved:
        stmt = stmt.where(UserTip.is_approved.is_(True))
    if exclude_archived:
        stmt = stmt.where(UserTip.is_archived.is_(False))
    if period_days is not None:
        threshold = datetime.utcnow() - timedelta(days=period_days)
        stmt = stmt.where(UserTip.created_at >= threshold)

    tips = session.execute(stmt).unique().scalars().all()
    sorted_tips = sorted(tips, key=lambda tip: tip.rating, reverse=True)
    return sorted_tips[:limit]


def iter_subscribers(base_chat_id: Optional[int], extra_chat_ids: Iterable[int]) -> List[int]:
    """Возвращает уникальный список получателей дайджеста."""

    recipients = set(extra_chat_ids or [])
    if base_chat_id:
        recipients.add(base_chat_id)
    return sorted(recipients)
