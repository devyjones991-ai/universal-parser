"""
Модели алертов и уведомлений
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from typing import Optional


class Alert(Base):
    """Алерт для отслеживания изменений"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tracked_item_id = Column(Integer, ForeignKey("tracked_items.id"), nullable=True, index=True)
    
    # Тип алерта
    alert_type = Column(String(50), nullable=False, index=True)  # price_drop, price_rise, stock_change, etc.
    name = Column(String(255), nullable=False)  # Название алерта
    
    # Условия срабатывания
    conditions = Column(JSON, nullable=False)  # Условия срабатывания
    threshold_value = Column(Float, nullable=True)  # Пороговое значение
    threshold_percent = Column(Float, nullable=True)  # Пороговый процент
    
    # Настройки уведомлений
    notification_methods = Column(JSON, default=["telegram"])  # telegram, email, webhook
    message_template = Column(Text, nullable=True)  # Шаблон сообщения
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    
    # Статистика
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="alerts")
    tracked_item = relationship("TrackedItem", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, name={self.name})>"


class Notification(Base):
    """История отправленных уведомлений"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Данные уведомления
    notification_type = Column(String(50), nullable=False)  # telegram, email, webhook
    title = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    
    # Статус отправки
    status = Column(String(50), default="pending")  # pending, sent, failed, delivered
    error_message = Column(Text, nullable=True)
    
    # Метаданные
    metadata = Column(JSON, default={})
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Связи
    alert = relationship("Alert", back_populates="notifications")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"


class AlertTemplate(Base):
    """Шаблоны алертов"""
    __tablename__ = "alert_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    alert_type = Column(String(50), nullable=False)
    
    # Шаблон
    title_template = Column(String(500), nullable=True)
    message_template = Column(Text, nullable=False)
    
    # Настройки
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AlertTemplate(id={self.id}, name={self.name}, type={self.alert_type})>"
