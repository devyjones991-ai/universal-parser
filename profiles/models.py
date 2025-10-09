"""SQLAlchemy модели для работы с пользовательскими данными Telegram."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    language_code = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tracked_items = relationship(
        "UserTrackedItem",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    settings = relationship(
        "UserSetting",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    history = relationship(
        "UserHistory",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="UserHistory.created_at.desc()",
    )


class UserTrackedItem(Base):
    __tablename__ = "user_tracked_items"

    id = Column(Integer, primary_key=True)
    profile_id = Column(
        Integer,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("UserProfile", back_populates="tracked_items")


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    profile_id = Column(
        Integer,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    profile = relationship("UserProfile", back_populates="settings")

    __table_args__ = (
        UniqueConstraint("profile_id", "key", name="uq_user_settings_profile_key"),
    )


class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True)
    profile_id = Column(
        Integer,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    action = Column(String(255), nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("UserProfile", back_populates="history")

