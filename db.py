import json
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config import settings
from datetime import datetime
from typing import Optional, List, Dict, Any

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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="free")  # free, premium, enterprise
    subscription_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})  # Персональные настройки пользователя
    
    # Связи
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    tracked_items = relationship("TrackedItem", back_populates="user", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="user", cascade="all, delete-orphan")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String, nullable=False)  # price_drop, price_rise, stock_change, review_change
    conditions = Column(JSON, nullable=False)  # Условия срабатывания
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    # Связи
    user = relationship("User", back_populates="alerts")

class TrackedItem(Base):
    __tablename__ = "tracked_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(String, nullable=False)  # ID товара на маркетплейсе
    marketplace = Column(String, nullable=False)  # wb, ozon, yandex
    name = Column(String, nullable=False)
    url = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    current_stock = Column(Integer, nullable=True)
    current_rating = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="tracked_items")
    price_history = relationship("PriceHistory", back_populates="tracked_item", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tracked_item_id = Column(Integer, ForeignKey("tracked_items.id"), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="price_history")
    tracked_item = relationship("TrackedItem", back_populates="price_history")

def init_db():
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

# Функции для работы с пользователями
def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    """Получить или создать пользователя"""
    init_db()
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Обновляем информацию о пользователе
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_activity = datetime.utcnow()
            session.commit()
        return user

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    init_db()
    with SessionLocal() as session:
        return session.query(User).filter(User.telegram_id == telegram_id).first()

def update_user_subscription(telegram_id: int, tier: str, expires: datetime = None):
    """Обновить подписку пользователя"""
    init_db()
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            user.subscription_tier = tier
            user.subscription_expires = expires
            session.commit()

# Функции для работы с отслеживаемыми товарами
def add_tracked_item(user_id: int, item_id: str, marketplace: str, name: str, url: str = None) -> TrackedItem:
    """Добавить товар для отслеживания"""
    init_db()
    with SessionLocal() as session:
        # Проверяем, не отслеживается ли уже этот товар
        existing = session.query(TrackedItem).filter(
            TrackedItem.user_id == user_id,
            TrackedItem.item_id == item_id,
            TrackedItem.marketplace == marketplace
        ).first()
        
        if existing:
            existing.is_active = True
            session.commit()
            return existing
        
        tracked_item = TrackedItem(
            user_id=user_id,
            item_id=item_id,
            marketplace=marketplace,
            name=name,
            url=url
        )
        session.add(tracked_item)
        session.commit()
        session.refresh(tracked_item)
        return tracked_item

def get_user_tracked_items(user_id: int) -> List[TrackedItem]:
    """Получить все отслеживаемые товары пользователя"""
    init_db()
    with SessionLocal() as session:
        return session.query(TrackedItem).filter(
            TrackedItem.user_id == user_id,
            TrackedItem.is_active == True
        ).all()

def remove_tracked_item(user_id: int, item_id: str, marketplace: str):
    """Удалить товар из отслеживания"""
    init_db()
    with SessionLocal() as session:
        item = session.query(TrackedItem).filter(
            TrackedItem.user_id == user_id,
            TrackedItem.item_id == item_id,
            TrackedItem.marketplace == marketplace
        ).first()
        if item:
            item.is_active = False
            session.commit()

def update_tracked_item_price(tracked_item_id: int, price: float, stock: int = None, rating: float = None):
    """Обновить цену и другие данные товара"""
    init_db()
    with SessionLocal() as session:
        item = session.query(TrackedItem).filter(TrackedItem.id == tracked_item_id).first()
        if item:
            # Сохраняем историю цен
            price_history = PriceHistory(
                user_id=item.user_id,
                tracked_item_id=tracked_item_id,
                price=price,
                stock=stock,
                rating=rating
            )
            session.add(price_history)
            
            # Обновляем текущие данные
            item.current_price = price
            if stock is not None:
                item.current_stock = stock
            if rating is not None:
                item.current_rating = rating
            item.last_updated = datetime.utcnow()
            session.commit()

# Функции для работы с алертами
def create_alert(user_id: int, alert_type: str, conditions: Dict[str, Any]) -> Alert:
    """Создать алерт для пользователя"""
    init_db()
    with SessionLocal() as session:
        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            conditions=conditions
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert

def get_user_alerts(user_id: int) -> List[Alert]:
    """Получить все алерты пользователя"""
    init_db()
    with SessionLocal() as session:
        return session.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_active == True
        ).all()

def deactivate_alert(alert_id: int):
    """Деактивировать алерт"""
    init_db()
    with SessionLocal() as session:
        alert = session.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_active = False
            session.commit()

def trigger_alert(alert_id: int):
    """Отметить алерт как сработавший"""
    init_db()
    with SessionLocal() as session:
        alert = session.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.last_triggered = datetime.utcnow()
            alert.trigger_count += 1
            session.commit()

# Функции для аналитики
def get_price_history(user_id: int, tracked_item_id: int = None, days: int = 30) -> List[PriceHistory]:
    """Получить историю цен"""
    init_db()
    with SessionLocal() as session:
        query = session.query(PriceHistory).filter(PriceHistory.user_id == user_id)
        
        if tracked_item_id:
            query = query.filter(PriceHistory.tracked_item_id == tracked_item_id)
        
        # Фильтр по дате
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceHistory.timestamp >= cutoff_date)
        
        return query.order_by(PriceHistory.timestamp.desc()).all()

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Получить статистику пользователя"""
    init_db()
    with SessionLocal() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        tracked_count = session.query(TrackedItem).filter(
            TrackedItem.user_id == user_id,
            TrackedItem.is_active == True
        ).count()
        
        alerts_count = session.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.is_active == True
        ).count()
        
        return {
            "user_id": user_id,
            "subscription_tier": user.subscription_tier,
            "tracked_items_count": tracked_count,
            "alerts_count": alerts_count,
            "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "last_activity": user.last_activity.strftime('%Y-%m-%d %H:%M:%S')
        }
