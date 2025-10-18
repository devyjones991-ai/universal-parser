"""
Модели пользователей и подписок
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from typing import Optional


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    
    # Статус и активность
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Подписка
    subscription_tier = Column(String(50), default="free")  # free, premium, enterprise
    subscription_expires = Column(DateTime, nullable=True)
    subscription_auto_renew = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Настройки
    settings = Column(JSON, default={})
    preferences = Column(JSON, default={})
    
    # Связи
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    tracked_items = relationship("TrackedItem", back_populates="user", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class APIKey(Base):
    """API ключи для пользователей"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name={self.key_name})>"
