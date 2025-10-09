import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
from datetime import datetime

engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class ParseResult(Base):
    __tablename__ = "parse_results"
    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False)
    data_json = Column(Text, nullable=False)
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Инициализация всех таблиц проекта."""

    # Импортируем модели, чтобы SQLAlchemy знала о них перед созданием таблиц
    import profiles.models  # noqa: F401

    Base.metadata.create_all(engine)

def save_results(profile_name: str, results):
    """Сохраняет результаты парсинга в БД"""
    init_db()
    with SessionLocal() as session:
        pr = ParseResult(
            profile_name=profile_name,
            data_json=json.dumps(results, ensure_ascii=False),
            count=len(results),
            timestamp=datetime.utcnow()
        )
        session.add(pr)
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
