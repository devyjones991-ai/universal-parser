"""SQLAlchemy модели для советов пользователей и обратной связи."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db import Base


class UserTip(Base):
    """Совет, созданный пользователем."""

    __tablename__ = "user_tips"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, nullable=False, index=True)
    author_username = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)

    feedbacks = relationship(
        "TipFeedback",
        back_populates="tip",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    @property
    def rating(self) -> int:
        """Возвращает агрегированный рейтинг совета."""

        return sum(feedback.value for feedback in self.feedbacks)


class TipFeedback(Base):
    """Оценка совета конкретным пользователем."""

    __tablename__ = "tip_feedback"
    __table_args__ = (
        UniqueConstraint("tip_id", "user_id", name="uq_tip_feedback_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tip_id = Column(Integer, ForeignKey("user_tips.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    value = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    tip = relationship("UserTip", back_populates="feedbacks")

