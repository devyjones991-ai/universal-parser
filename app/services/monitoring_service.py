"""Сервис мониторинга и алертов"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.cache import cache_service
from app.services.performance_monitor import performance_monitor
from app.services.database_optimizer import database_optimizer
from app.services.cache_optimizer import cache_optimizer

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Уровни серьезности алертов"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Статусы алертов"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Каналы уведомлений"""
    EMAIL = "email"
    SLACK = "slack"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"
    PUSH = "push"


@dataclass
class AlertRule:
    """Правило алерта"""
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # ">", "<", ">=", "<=", "==", "!="
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 15
    notification_channels: List[NotificationChannel] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = [NotificationChannel.EMAIL]


@dataclass
class Alert:
    """Алерт"""
    id: str
    rule_id: str
    title: str
    message: str
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationConfig:
    """Конфигурация уведомлений"""
    channel: NotificationChannel
    enabled: bool
    config: Dict[str, Any]


class MonitoringService:
    """Сервис мониторинга"""
    
    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_configs: Dict[NotificationChannel, NotificationConfig] = {}
        self.monitoring_active = False
        self.monitoring_task = None
        self.check_interval = 30  # секунд
        
        # Загружаем правила алертов
        self._load_default_alert_rules()
        
        # Запускаем мониторинг
        self.start_monitoring()
    
    def _load_default_alert_rules(self):
        """Загрузить правила алертов по умолчанию"""
        default_rules = [
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above threshold",
                metric_name="cpu_usage",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                id="critical_cpu_usage",
                name="Critical CPU Usage",
                description="CPU usage is critically high",
                metric_name="cpu_usage",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is above threshold",
                metric_name="memory_usage",
                condition=">",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                id="critical_memory_usage",
                name="Critical Memory Usage",
                description="Memory usage is critically high",
                metric_name="memory_usage",
                condition=">",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                id="high_disk_usage",
                name="High Disk Usage",
                description="Disk usage is above threshold",
                metric_name="disk_usage",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10
            ),
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate is above threshold",
                metric_name="error_rate",
                condition=">",
                threshold=5.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5
            ),
            AlertRule(
                id="critical_error_rate",
                name="Critical Error Rate",
                description="Error rate is critically high",
                metric_name="error_rate",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=2
            ),
            AlertRule(
                id="low_cache_hit_rate",
                name="Low Cache Hit Rate",
                description="Cache hit rate is below threshold",
                metric_name="cache_hit_rate",
                condition="<",
                threshold=70.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=15
            ),
            AlertRule(
                id="slow_database_queries",
                name="Slow Database Queries",
                description="Database query time is above threshold",
                metric_name="database_query_time",
                condition=">",
                threshold=1000.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=10
            ),
            AlertRule(
                id="high_response_time",
                name="High Response Time",
                description="API response time is above threshold",
                metric_name="request_latency",
                condition=">",
                threshold=2000.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=5
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
    
    def start_monitoring(self):
        """Запустить мониторинг"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Monitoring service started")
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
            logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                await self._check_alert_rules()
                await self._cleanup_resolved_alerts()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_alert_rules(self):
        """Проверить правила алертов"""
        try:
            # Получаем текущие метрики
            performance_summary = await performance_monitor.get_performance_summary()
            cache_stats = await cache_optimizer.get_stats()
            db_stats = await database_optimizer.get_database_stats()
            
            # Объединяем все метрики
            metrics = {
                "cpu_usage": performance_summary.get("performance_metrics", {}).get("cpu_usage", {}).get("current", 0),
                "memory_usage": performance_summary.get("performance_metrics", {}).get("memory_usage", {}).get("current", 0),
                "disk_usage": performance_summary.get("performance_metrics", {}).get("disk_usage", {}).get("current", 0),
                "error_rate": performance_summary.get("performance_metrics", {}).get("error_rate", {}).get("current", 0),
                "cache_hit_rate": cache_stats.hit_rate,
                "database_query_time": performance_summary.get("performance_metrics", {}).get("database_query_time", {}).get("current", 0),
                "request_latency": performance_summary.get("performance_metrics", {}).get("request_latency", {}).get("current", 0),
            }
            
            # Проверяем каждое правило
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                await self._check_alert_rule(rule, metrics)
        
        except Exception as e:
            logger.error(f"Error checking alert rules: {e}")
    
    async def _check_alert_rule(self, rule: AlertRule, metrics: Dict[str, float]):
        """Проверить конкретное правило алерта"""
        try:
            if rule.metric_name not in metrics:
                return
            
            current_value = metrics[rule.metric_name]
            threshold = rule.threshold
            
            # Проверяем условие
            condition_met = False
            if rule.condition == ">":
                condition_met = current_value > threshold
            elif rule.condition == ">=":
                condition_met = current_value >= threshold
            elif rule.condition == "<":
                condition_met = current_value < threshold
            elif rule.condition == "<=":
                condition_met = current_value <= threshold
            elif rule.condition == "==":
                condition_met = current_value == threshold
            elif rule.condition == "!=":
                condition_met = current_value != threshold
            
            if condition_met:
                # Проверяем cooldown
                if await self._is_in_cooldown(rule):
                    return
                
                # Создаем алерт
                await self._create_alert(rule, current_value)
            else:
                # Разрешаем алерт если он был активен
                await self._resolve_alert_if_active(rule.id)
        
        except Exception as e:
            logger.error(f"Error checking alert rule {rule.id}: {e}")
    
    async def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Проверить, находится ли правило в cooldown"""
        try:
            # Ищем активные алерты для этого правила
            for alert in self.active_alerts.values():
                if (alert.rule_id == rule.id and 
                    alert.status == AlertStatus.ACTIVE and
                    (datetime.utcnow() - alert.created_at).total_seconds() < rule.cooldown_minutes * 60):
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    async def _create_alert(self, rule: AlertRule, current_value: float):
        """Создать алерт"""
        try:
            alert_id = str(uuid.uuid4())
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                title=f"{rule.name} - {rule.severity.value.upper()}",
                message=f"{rule.description}. Current value: {current_value:.2f}, Threshold: {rule.threshold:.2f}",
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                created_at=datetime.utcnow(),
                metadata={
                    "current_value": current_value,
                    "threshold": rule.threshold,
                    "condition": rule.condition
                }
            )
            
            self.active_alerts[alert_id] = alert
            
            # Отправляем уведомления
            await self._send_notifications(alert, rule)
            
            logger.warning(f"Alert created: {alert.title}")
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def _resolve_alert_if_active(self, rule_id: str):
        """Разрешить алерт если он активен"""
        try:
            for alert in self.active_alerts.values():
                if (alert.rule_id == rule_id and 
                    alert.status == AlertStatus.ACTIVE):
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.utcnow()
                    alert.resolved_by = "system"
                    
                    logger.info(f"Alert resolved: {alert.title}")
        
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
    
    async def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Отправить уведомления"""
        try:
            for channel in rule.notification_channels:
                config = self.notification_configs.get(channel)
                if config and config.enabled:
                    await self._send_notification(alert, channel, config)
        
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    async def _send_notification(self, alert: Alert, channel: NotificationChannel, config: NotificationConfig):
        """Отправить уведомление по каналу"""
        try:
            if channel == NotificationChannel.EMAIL:
                await self._send_email_notification(alert, config)
            elif channel == NotificationChannel.SLACK:
                await self._send_slack_notification(alert, config)
            elif channel == NotificationChannel.TELEGRAM:
                await self._send_telegram_notification(alert, config)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(alert, config)
        
        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {e}")
    
    async def _send_email_notification(self, alert: Alert, config: NotificationConfig):
        """Отправить email уведомление"""
        try:
            # В реальном приложении здесь была бы отправка email
            logger.info(f"Email notification: {alert.title} - {alert.message}")
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert, config: NotificationConfig):
        """Отправить Slack уведомление"""
        try:
            # В реальном приложении здесь была бы отправка в Slack
            logger.info(f"Slack notification: {alert.title} - {alert.message}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    async def _send_telegram_notification(self, alert: Alert, config: NotificationConfig):
        """Отправить Telegram уведомление"""
        try:
            # В реальном приложении здесь была бы отправка в Telegram
            logger.info(f"Telegram notification: {alert.title} - {alert.message}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert, config: NotificationConfig):
        """Отправить webhook уведомление"""
        try:
            # В реальном приложении здесь была бы отправка webhook
            logger.info(f"Webhook notification: {alert.title} - {alert.message}")
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    async def _cleanup_resolved_alerts(self):
        """Очистить разрешенные алерты"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            resolved_alerts = [
                alert_id for alert_id, alert in self.active_alerts.items()
                if alert.status == AlertStatus.RESOLVED and alert.resolved_at < cutoff_time
            ]
            
            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]
            
            if resolved_alerts:
                logger.info(f"Cleaned up {len(resolved_alerts)} resolved alerts")
        
        except Exception as e:
            logger.error(f"Error cleaning up resolved alerts: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Подтвердить алерт"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Разрешить алерт"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def get_active_alerts(self) -> List[Alert]:
        """Получить активные алерты"""
        return [alert for alert in self.active_alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    async def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Получить историю алертов"""
        return list(self.active_alerts.values())[-limit:]
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Получить данные для дашборда мониторинга"""
        try:
            active_alerts = await self.get_active_alerts()
            performance_summary = await performance_monitor.get_performance_summary()
            cache_stats = await cache_optimizer.get_stats()
            db_stats = await database_optimizer.get_database_stats()
            
            # Группируем алерты по серьезности
            alerts_by_severity = {}
            for severity in AlertSeverity:
                alerts_by_severity[severity.value] = len([
                    alert for alert in active_alerts if alert.severity == severity
                ])
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system_health": performance_summary.get("status", "unknown"),
                "active_alerts": {
                    "total": len(active_alerts),
                    "by_severity": alerts_by_severity
                },
                "performance_metrics": performance_summary.get("performance_metrics", {}),
                "cache_stats": asdict(cache_stats),
                "database_stats": asdict(db_stats),
                "monitoring_active": self.monitoring_active
            }
        
        except Exception as e:
            logger.error(f"Error getting monitoring dashboard: {e}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()


