"""Модуль для создания движка БД и фабрики сессий."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings


engine = create_engine(settings.DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base = declarative_base()


def get_session():
    """Возвращает новую сессию SQLAlchemy."""
    return SessionLocal()

