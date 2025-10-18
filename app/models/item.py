"""
Модели товаров и отслеживания
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from typing import Optional


class TrackedItem(Base):
    """Отслеживаемый товар"""
    __tablename__ = "tracked_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Идентификация товара
    item_id = Column(String(255), nullable=False, index=True)  # ID товара на маркетплейсе
    marketplace = Column(String(50), nullable=False, index=True)  # wb, ozon, yandex, etc.
    sku = Column(String(255), nullable=True, index=True)  # SKU товара
    
    # Основная информация
    name = Column(String(500), nullable=False)
    brand = Column(String(255), nullable=True)
    category = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    
    # Текущие данные
    current_price = Column(Float, nullable=True)
    current_stock = Column(Integer, nullable=True)
    current_rating = Column(Float, nullable=True)
    current_reviews_count = Column(Integer, nullable=True)
    
    # Дополнительные данные
    image_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    specifications = Column(JSON, default={})
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    
    # Настройки отслеживания
    tracking_settings = Column(JSON, default={})
    
    # Связи
    user = relationship("User", back_populates="tracked_items")
    price_history = relationship("PriceHistory", back_populates="tracked_item", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="tracked_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrackedItem(id={self.id}, name={self.name[:50]}...)>"


class PriceHistory(Base):
    """История цен товаров"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tracked_item_id = Column(Integer, ForeignKey("tracked_items.id"), nullable=False, index=True)
    
    # Данные о цене
    price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)  # Предыдущая цена
    discount_percent = Column(Float, nullable=True)  # Процент скидки
    
    # Дополнительные данные
    stock = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    
    # Метаданные
    source = Column(String(50), nullable=True)  # Источник данных
    raw_data = Column(JSON, default={})  # Сырые данные парсинга
    
    # Временная метка
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = relationship("User", back_populates="price_history")
    tracked_item = relationship("TrackedItem", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(id={self.id}, price={self.price}, timestamp={self.timestamp})>"


class Marketplace(Base):
    """Справочник маркетплейсов"""
    __tablename__ = "marketplaces"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    api_url = Column(String(500), nullable=True)
    
    # Настройки парсинга
    parsing_config = Column(JSON, default={})
    rate_limits = Column(JSON, default={})
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_api_available = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Marketplace(id={self.id}, code={self.code}, name={self.name})>"
