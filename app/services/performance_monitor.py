"""Сервис мониторинга производительности"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading
from collections import deque, defaultdict

from app.core.cache import cache_service
from app.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Типы метрик производительности"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    DATABASE_CONNECTIONS = "database_connections"
    REDIS_CONNECTIONS = "redis_connections"
    REQUEST_LATENCY = "request_latency"
    REQUEST_THROUGHPUT = "request_throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_QUERY_TIME = "database_query_time"
    PARSING_PERFORMANCE = "parsing_performance"
    API_RESPONSE_TIME = "api_response_time"
    WEBSOCKET_CONNECTIONS = "websocket_connections"
    QUEUE_SIZE = "queue_size"


@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SystemStats:
    """Статистика системы"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """Алерт производительности"""
    id: str
    metric_type: MetricType
    threshold: float
    current_value: float
    severity: str  # "warning", "critical"
    message: str
    timestamp: datetime
    resolved: bool = False


class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.alerts: List[PerformanceAlert] = []
        self.thresholds = {
            MetricType.CPU_USAGE: {"warning": 80.0, "critical": 95.0},
            MetricType.MEMORY_USAGE: {"warning": 85.0, "critical": 95.0},
            MetricType.DISK_USAGE: {"warning": 80.0, "critical": 90.0},
            MetricType.REQUEST_LATENCY: {"warning": 1000.0, "critical": 5000.0},  # ms
            MetricType.ERROR_RATE: {"warning": 5.0, "critical": 10.0},  # %
            MetricType.CACHE_HIT_RATE: {"warning": 70.0, "critical": 50.0},  # %
            MetricType.DATABASE_QUERY_TIME: {"warning": 100.0, "critical": 500.0},  # ms
        }
        
        self.monitoring_active = False
        self.monitoring_task = None
        self.collection_interval = 10  # секунд
        self.alert_cooldown = 300  # 5 минут между одинаковыми алертами
        
        # Статистика
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Запускаем мониторинг
        self.start_monitoring()
    
    def start_monitoring(self):
        """Запустить мониторинг"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
            logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._check_thresholds()
                await self._cleanup_old_metrics()
                
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Собрать системные метрики"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            await self._record_metric(MetricType.CPU_USAGE, cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            await self._record_metric(MetricType.MEMORY_USAGE, memory.percent)
            await self._record_metric(MetricType.MEMORY_USAGE, memory.used / 1024 / 1024, 
                                    tags={"unit": "MB"})
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._record_metric(MetricType.DISK_USAGE, disk_percent)
            
            # Network
            network = psutil.net_io_counters()
            await self._record_metric(MetricType.NETWORK_IO, network.bytes_sent, 
                                    tags={"direction": "sent"})
            await self._record_metric(MetricType.NETWORK_IO, network.bytes_recv, 
                                    tags={"direction": "recv"})
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_application_metrics(self):
        """Собрать метрики приложения"""
        try:
            # Database connections
            db_connections = await self._get_database_connections()
            await self._record_metric(MetricType.DATABASE_CONNECTIONS, db_connections)
            
            # Redis connections
            redis_connections = await self._get_redis_connections()
            await self._record_metric(MetricType.REDIS_CONNECTIONS, redis_connections)
            
            # Request latency
            if self.request_times:
                avg_latency = sum(self.request_times) / len(self.request_times)
                await self._record_metric(MetricType.REQUEST_LATENCY, avg_latency)
            
            # Request throughput
            throughput = len(self.request_times) / 60  # requests per minute
            await self._record_metric(MetricType.REQUEST_THROUGHPUT, throughput)
            
            # Error rate
            total_requests = len(self.request_times) + sum(self.error_counts.values())
            if total_requests > 0:
                error_rate = (sum(self.error_counts.values()) / total_requests) * 100
                await self._record_metric(MetricType.ERROR_RATE, error_rate)
            
            # Cache hit rate
            total_cache_requests = self.cache_hits + self.cache_misses
            if total_cache_requests > 0:
                hit_rate = (self.cache_hits / total_cache_requests) * 100
                await self._record_metric(MetricType.CACHE_HIT_RATE, hit_rate)
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    async def _get_database_connections(self) -> int:
        """Получить количество подключений к БД"""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("SELECT count(*) FROM pg_stat_activity"))
                return result.scalar() or 0
        except Exception:
            return 0
    
    async def _get_redis_connections(self) -> int:
        """Получить количество подключений к Redis"""
        try:
            # В реальном приложении здесь был бы запрос к Redis
            return 0
        except Exception:
            return 0
    
    async def _record_metric(self, metric_type: MetricType, value: float, tags: Dict[str, str] = None):
        """Записать метрику"""
        metric = PerformanceMetric(
            id=str(uuid.uuid4()),
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )
        
        self.metrics_buffer.append(metric)
        
        # Сохраняем в кэш
        try:
            cache_key = f"perf_metric:{metric.id}"
            await cache_service.set(cache_key, asdict(metric), ttl=3600)
        except Exception as e:
            logger.error(f"Error caching metric: {e}")
    
    async def _check_thresholds(self):
        """Проверить пороговые значения"""
        try:
            # Получаем последние метрики
            recent_metrics = list(self.metrics_buffer)[-100:]  # последние 100 метрик
            
            for metric in recent_metrics:
                if metric.metric_type in self.thresholds:
                    thresholds = self.thresholds[metric.metric_type]
                    
                    # Проверяем критические пороги
                    if metric.value >= thresholds["critical"]:
                        await self._create_alert(metric, "critical", thresholds["critical"])
                    
                    # Проверяем предупреждения
                    elif metric.value >= thresholds["warning"]:
                        await self._create_alert(metric, "warning", thresholds["warning"])
        
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    async def _create_alert(self, metric: PerformanceMetric, severity: str, threshold: float):
        """Создать алерт"""
        try:
            # Проверяем cooldown
            recent_alerts = [
                alert for alert in self.alerts
                if (alert.metric_type == metric.metric_type and 
                    alert.severity == severity and
                    not alert.resolved and
                    (datetime.utcnow() - alert.timestamp).total_seconds() < self.alert_cooldown)
            ]
            
            if recent_alerts:
                return  # Алерт уже есть, не создаем дубликат
            
            alert = PerformanceAlert(
                id=str(uuid.uuid4()),
                metric_type=metric.metric_type,
                threshold=threshold,
                current_value=metric.value,
                severity=severity,
                message=f"{metric.metric_type.value} is {metric.value:.2f}, threshold: {threshold:.2f}",
                timestamp=datetime.utcnow()
            )
            
            self.alerts.append(alert)
            
            # Логируем алерт
            logger.warning(f"Performance alert: {alert.message}")
            
            # В реальном приложении здесь была бы отправка уведомлений
            await self._send_alert_notification(alert)
        
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def _send_alert_notification(self, alert: PerformanceAlert):
        """Отправить уведомление об алерте"""
        try:
            # В реальном приложении здесь была бы отправка в Slack, email, etc.
            logger.info(f"Alert notification: {alert.message}")
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
    
    async def _cleanup_old_metrics(self):
        """Очистить старые метрики"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Очищаем буфер
            while self.metrics_buffer and self.metrics_buffer[0].timestamp < cutoff_time:
                self.metrics_buffer.popleft()
            
            # Очищаем алерты
            self.alerts = [
                alert for alert in self.alerts
                if alert.timestamp > cutoff_time or not alert.resolved
            ]
        
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    def record_request_time(self, duration_ms: float):
        """Записать время выполнения запроса"""
        self.request_times.append(duration_ms)
    
    def record_error(self, error_type: str):
        """Записать ошибку"""
        self.error_counts[error_type] += 1
    
    def record_cache_hit(self):
        """Записать попадание в кэш"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Записать промах кэша"""
        self.cache_misses += 1
    
    async def get_system_stats(self) -> SystemStats:
        """Получить статистику системы"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemStats(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=(disk.used / disk.total) * 100,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return SystemStats(0, 0, 0, 0, 0, 0, 0, 0, datetime.utcnow())
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Получить сводку производительности"""
        try:
            recent_metrics = list(self.metrics_buffer)[-100:]
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_count": len(self.metrics_buffer),
                "active_alerts": len([a for a in self.alerts if not a.resolved]),
                "system_stats": await self.get_system_stats(),
                "performance_metrics": {}
            }
            
            # Группируем метрики по типам
            metrics_by_type = defaultdict(list)
            for metric in recent_metrics:
                metrics_by_type[metric.metric_type].append(metric.value)
            
            # Вычисляем статистики
            for metric_type, values in metrics_by_type.items():
                if values:
                    summary["performance_metrics"][metric_type.value] = {
                        "current": values[-1],
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            
            return summary
        
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    async def get_alerts(self, resolved: Optional[bool] = None) -> List[PerformanceAlert]:
        """Получить алерты"""
        if resolved is None:
            return self.alerts
        return [alert for alert in self.alerts if alert.resolved == resolved]
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Разрешить алерт"""
        try:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Получить статус здоровья системы"""
        try:
            system_stats = await self.get_system_stats()
            active_alerts = [a for a in self.alerts if not a.resolved]
            critical_alerts = [a for a in active_alerts if a.severity == "critical"]
            
            # Определяем общий статус
            if critical_alerts:
                status = "critical"
            elif active_alerts:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "system_stats": asdict(system_stats),
                "active_alerts": len(active_alerts),
                "critical_alerts": len(critical_alerts),
                "monitoring_active": self.monitoring_active
            }
        
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "error", "error": str(e)}


# Глобальный экземпляр монитора производительности
performance_monitor = PerformanceMonitor()
