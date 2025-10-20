"""Сервис для аналитики использования API"""

from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.cache import cache_service
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, and_

logger = logging.getLogger(__name__)

class APIMetricType(Enum):
    """Типы метрик API"""
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_COUNT = "error_count"
    SUCCESS_RATE = "success_rate"
    BANDWIDTH = "bandwidth"
    USER_ACTIVITY = "user_activity"
    ENDPOINT_USAGE = "endpoint_usage"
    RATE_LIMIT_HITS = "rate_limit_hits"

@dataclass
class APIMetric:
    """Метрика API"""
    id: str
    metric_type: APIMetricType
    endpoint: str
    method: str
    user_id: Optional[str]
    ip_address: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class APIUsageStats:
    """Статистика использования API"""
    total_requests: int
    unique_users: int
    unique_ips: int
    average_response_time: float
    error_rate: float
    top_endpoints: List[Dict[str, Any]]
    top_users: List[Dict[str, Any]]
    top_ips: List[Dict[str, Any]]
    hourly_requests: List[Dict[str, Any]]
    daily_requests: List[Dict[str, Any]]

class APIAnalyticsService:
    """Сервис для аналитики API"""

    def __init__(self):
        self.metrics_cache: Dict[str, List[APIMetric]] = {}
        self.cache_ttl = 3600  # 1 час
        self.batch_size = 1000
        self.flush_interval = 300  # 5 минут

        # Запускаем фоновую задачу для сохранения метрик
        asyncio.create_task(self._flush_metrics_loop())

    async def record_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str],
        ip_address: str,
        response_time: float,
        status_code: int,
        request_size: int = 0,
        response_size: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Записать метрику запроса"""
        try:
            timestamp = datetime.utcnow()
            metric_id = str(uuid.uuid4())

            # Создаем метрики
            metrics = [
                APIMetric(
                    id=metric_id,
                    metric_type=APIMetricType.REQUEST_COUNT,
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    value=1.0,
                    timestamp=timestamp,
                    metadata=metadata or {}
                ),
                APIMetric(
                    id=metric_id,
                    metric_type=APIMetricType.RESPONSE_TIME,
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    value=response_time,
                    timestamp=timestamp,
                    metadata=metadata or {}
                )
            ]

            # Добавляем метрику ошибки если нужно
            if status_code >= 400:
                metrics.append(APIMetric(
                    id=metric_id,
                    metric_type=APIMetricType.ERROR_COUNT,
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    value=1.0,
                    timestamp=timestamp,
                    metadata=metadata or {}
                ))

            # Добавляем метрику пропускной способности
            if request_size > 0 or response_size > 0:
                metrics.append(APIMetric(
                    id=metric_id,
                    metric_type=APIMetricType.BANDWIDTH,
                    endpoint=endpoint,
                    method=method,
                    user_id=user_id,
                    ip_address=ip_address,
                    value=request_size + response_size,
                    timestamp=timestamp,
                    metadata=metadata or {}
                ))

            # Сохраняем в кэш
            await self._cache_metrics(metrics)

        except Exception as e:
            logger.error("Error recording API request: {e}")

    async def record_rate_limit_hit(
        self,
        endpoint: str,
        user_id: Optional[str],
        ip_address: str,
        limit_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Записать попадание в rate limit"""
        try:
            metric = APIMetric(
                id=str(uuid.uuid4()),
                metric_type=APIMetricType.RATE_LIMIT_HITS,
                endpoint=endpoint,
                method="RATE_LIMIT",
                user_id=user_id,
                ip_address=ip_address,
                value=1.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "limit_name": limit_name,
                    **(metadata or {})
                }
            )

            await self._cache_metrics([metric])

        except Exception as e:
            logger.error("Error recording rate limit hit: {e}")

    async def _cache_metrics(self, metrics: List[APIMetric]):
        """Кэшировать метрики"""
        try:
            # Добавляем в память
            for metric in metrics:
                cache_key = f"api_metrics:{metric.timestamp.strftime('%Y%m%d%H')}"
                if cache_key not in self.metrics_cache:
                    self.metrics_cache[cache_key] = []
                self.metrics_cache[cache_key].append(metric)

            # Сохраняем в Redis
            for metric in metrics:
                cache_key = f"api_metric:{metric.id}"
                await cache_service.set(
                    cache_key,
                    asdict(metric),
                    ttl=self.cache_ttl
                )

        except Exception as e:
            logger.error("Error caching metrics: {e}")

    async def _flush_metrics_loop(self):
        """Фоновая задача для сохранения метрик"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_metrics()
            except Exception as e:
                logger.error("Error in flush metrics loop: {e}")

    async def _flush_metrics(self):
        """Сохранить метрики в базу данных"""
        try:
            # В реальном приложении здесь было бы сохранение в БД
            # Пока просто очищаем старые метрики из кэша
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            for cache_key in list(self.metrics_cache.keys()):
                metrics = self.metrics_cache[cache_key]
                # Фильтруем старые метрики
                self.metrics_cache[cache_key] = [
                    metric for metric in metrics
                    if metric.timestamp > cutoff_time
                ]

                # Удаляем пустые ключи
                if not self.metrics_cache[cache_key]:
                    del self.metrics_cache[cache_key]

            logger.info("Flushed API metrics, {len(self.metrics_cache)} cache keys remaining")

        except Exception as e:
            logger.error("Error flushing metrics: {e}")

    async def get_usage_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> APIUsageStats:
        """Получить статистику использования API"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if end_time is None:
                end_time = datetime.utcnow()

            # Получаем метрики из кэша
            metrics = await self._get_metrics_from_cache(start_time, end_time, endpoint, user_id)

            # Анализируем метрики
            total_requests = len([m for m in metrics if m.metric_type == APIMetricType.REQUEST_COUNT])
            unique_users = len(set(m.user_id for m in metrics if m.user_id))
            unique_ips = len(set(m.ip_address for m in metrics))

            # Среднее время ответа
            response_times = [m.value for m in metrics if m.metric_type == APIMetricType.RESPONSE_TIME]
            average_response_time = sum(response_times) / len(response_times) if response_times else 0.0

            # Процент ошибок
            error_count = len([m for m in metrics if m.metric_type == APIMetricType.ERROR_COUNT])
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

            # Топ эндпоинты
            endpoint_counts = {}
            for metric in metrics:
                if metric.metric_type == APIMetricType.REQUEST_COUNT:
                    key = f"{metric.method} {metric.endpoint}"
                    endpoint_counts[key] = endpoint_counts.get(key, 0) + 1

            top_endpoints = [
                {"endpoint": endpoint, "count": count}
                for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
            ]

            # Топ пользователи
            user_counts = {}
            for metric in metrics:
                if metric.metric_type == APIMetricType.REQUEST_COUNT and metric.user_id  # noqa  # noqa: E501 E501
                    user_counts[metric.user_id] = user_counts.get(metric.user_id, 0) + 1

            top_users = [
                {"user_id": user_id, "count": count}
                for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
            ]

            # Топ IP адреса
            ip_counts = {}
            for metric in metrics:
                if metric.metric_type == APIMetricType.REQUEST_COUNT:
                    ip_counts[metric.ip_address] = ip_counts.get(metric.ip_address, 0) + 1

            top_ips = [
                {"ip_address": ip, "count": count}
                for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
            ]

            # Запросы по часам
            hourly_requests = await self._get_hourly_requests(metrics)

            # Запросы по дням
            daily_requests = await self._get_daily_requests(metrics)

            return APIUsageStats(
                total_requests=total_requests,
                unique_users=unique_users,
                unique_ips=unique_ips,
                average_response_time=average_response_time,
                error_rate=error_rate,
                top_endpoints=top_endpoints,
                top_users=top_users,
                top_ips=top_ips,
                hourly_requests=hourly_requests,
                daily_requests=daily_requests
            )

        except Exception as e:
            logger.error("Error getting usage stats: {e}")
            return APIUsageStats(
                total_requests=0,
                unique_users=0,
                unique_ips=0,
                average_response_time=0.0,
                error_rate=0.0,
                top_endpoints=[],
                top_users=[],
                top_ips=[],
                hourly_requests=[],
                daily_requests=[]
            )

    async def _get_metrics_from_cache(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[APIMetric]:
        """Получить метрики из кэша"""
        metrics = []

        try:
            # Получаем метрики из памяти
            for cache_key, cached_metrics in self.metrics_cache.items():
                for metric in cached_metrics:
                    if (start_time <= metric.timestamp <= end_time and
                        (endpoint is None or metric.endpoint == endpoint) and
                        (user_id is None or metric.user_id == user_id)):
                        metrics.append(metric)

            # Получаем метрики из Redis
            # В реальном приложении здесь был бы запрос к Redis

        except Exception as e:
            logger.error("Error getting metrics from cache: {e}")

        return metrics

    async def _get_hourly_requests(self, metrics: List[APIMetric]) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Получить запросы по часам"""
        hourly_counts = {}

        for metric in metrics:
            if metric.metric_type == APIMetricType.REQUEST_COUNT:
                hour = metric.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        return [
            {"hour": hour, "count": count}
            for hour, count in sorted(hourly_counts.items())
        ]

    async def _get_daily_requests(self, metrics: List[APIMetric]) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Получить запросы по дням"""
        daily_counts = {}

        for metric in metrics:
            if metric.metric_type == APIMetricType.REQUEST_COUNT:
                day = metric.timestamp.strftime("%Y-%m-%d")
                daily_counts[day] = daily_counts.get(day, 0) + 1

        return [
            {"day": day, "count": count}
            for day, count in sorted(daily_counts.items())
        ]

    async def get_endpoint_stats(
        self,
        endpoint: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получить статистику для конкретного эндпоинта"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if end_time is None:
                end_time = datetime.utcnow()

            metrics = await self._get_metrics_from_cache(start_time, end_time, endpoint)

            request_metrics = [m for m in metrics if m.metric_type == APIMetricType.REQUEST_COUNT]
            response_time_metrics = [m for m in metrics if m.metric_type == APIMetricType.RESPONSE_TIME]
            error_metrics = [m for m in metrics if m.metric_type == APIMetricType.ERROR_COUNT]

            total_requests = len(request_metrics)
            average_response_time = sum(m.value for m in response_time_metrics) / len(response_time_metrics) if response_time_metrics else 0.0
            error_count = len(error_metrics)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

            # Статистика по методам
            method_counts = {}
            for metric in request_metrics:
                method_counts[metric.method] = method_counts.get(metric.method, 0) + 1

            # Статистика по пользователям
            user_counts = {}
            for metric in request_metrics:
                if metric.user_id:
                    user_counts[metric.user_id] = user_counts.get(metric.user_id, 0) + 1

            return {
                "endpoint": endpoint,
                "total_requests": total_requests,
                "average_response_time": average_response_time,
                "error_count": error_count,
                "error_rate": error_rate,
                "method_counts": method_counts,
                "unique_users": len(user_counts),
                "top_users": [
                    {"user_id": user_id, "count": count}
                    for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E5015]
                ]
            }

        except Exception as e:
            logger.error("Error getting endpoint stats: {e}")
            return {"endpoint": endpoint, "error": str(e)}

    async def get_user_stats(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получить статистику для конкретного пользователя"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if end_time is None:
                end_time = datetime.utcnow()

            metrics = await self._get_metrics_from_cache(start_time, end_time, user_id=user_id)

            request_metrics = [m for m in metrics if m.metric_type == APIMetricType.REQUEST_COUNT]
            response_time_metrics = [m for m in metrics if m.metric_type == APIMetricType.RESPONSE_TIME]
            error_metrics = [m for m in metrics if m.metric_type == APIMetricType.ERROR_COUNT]

            total_requests = len(request_metrics)
            average_response_time = sum(m.value for m in response_time_metrics) / len(response_time_metrics) if response_time_metrics else 0.0
            error_count = len(error_metrics)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0.0

            # Статистика по эндпоинтам
            endpoint_counts = {}
            for metric in request_metrics:
                endpoint_counts[metric.endpoint] = endpoint_counts.get(metric.endpoint, 0) + 1

            return {
                "user_id": user_id,
                "total_requests": total_requests,
                "average_response_time": average_response_time,
                "error_count": error_count,
                "error_rate": error_rate,
                "top_endpoints": [
                    {"endpoint": endpoint, "count": count}
                    for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
                ]
            }

        except Exception as e:
            logger.error("Error getting user stats: {e}")
            return {"user_id": user_id, "error": str(e)}

    async def get_rate_limit_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получить статистику rate limiting"""
        try:
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if end_time is None:
                end_time = datetime.utcnow()

            metrics = await self._get_metrics_from_cache(start_time, end_time)
            rate_limit_metrics = [m for m in metrics if m.metric_type == APIMetricType.RATE_LIMIT_HITS]

            total_hits = len(rate_limit_metrics)

            # Статистика по лимитам
            limit_counts = {}
            for metric in rate_limit_metrics:
                limit_name = metric.metadata.get("limit_name", "unknown")
                limit_counts[limit_name] = limit_counts.get(limit_name, 0) + 1

            # Статистика по эндпоинтам
            endpoint_counts = {}
            for metric in rate_limit_metrics:
                endpoint_counts[metric.endpoint] = endpoint_counts.get(metric.endpoint, 0) + 1

            # Статистика по пользователям
            user_counts = {}
            for metric in rate_limit_metrics:
                if metric.user_id:
                    user_counts[metric.user_id] = user_counts.get(metric.user_id, 0) + 1

            return {
                "total_hits": total_hits,
                "limit_counts": limit_counts,
                "endpoint_counts": endpoint_counts,
                "user_counts": user_counts,
                "top_limited_endpoints": [
                    {"endpoint": endpoint, "count": count}
                    for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
                ],
                "top_limited_users": [
                    {"user_id": user_id, "count": count}
                    for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[  # noqa  # noqa: E501 E50110]
                ]
            }

        except Exception as e:
            logger.error("Error getting rate limit stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_metrics(self, days: int = 30):
        """Очистить старые метрики"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            # Очищаем из памяти
            for cache_key in list(self.metrics_cache.keys()):
                self.metrics_cache[cache_key] = [
                    metric for metric in self.metrics_cache[cache_key]
                    if metric.timestamp > cutoff_time
                ]
                if not self.metrics_cache[cache_key]:
                    del self.metrics_cache[cache_key]

            logger.info("Cleaned up API metrics older than {days} days")
            return True

        except Exception as e:
            logger.error("Error cleaning up old metrics: {e}")
            return False

# Глобальный экземпляр сервиса аналитики API
api_analytics_service = APIAnalyticsService()
