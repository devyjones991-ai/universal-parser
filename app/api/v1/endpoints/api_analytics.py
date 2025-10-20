"""API эндпоинты для аналитики использования API"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.api_analytics_service import api_analytics_service
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

class APIUsageStatsResponse(BaseModel):
    """Ответ со статистикой использования API"""
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

class EndpointStatsResponse(BaseModel):
    """Ответ со статистикой эндпоинта"""
    endpoint: str
    total_requests: int
    average_response_time: float
    error_count: int
    error_rate: float
    method_counts: Dict[str, int]
    unique_users: int
    top_users: List[Dict[str, Any]]

class UserStatsResponse(BaseModel):
    """Ответ со статистикой пользователя"""
    user_id: str
    total_requests: int
    average_response_time: float
    error_count: int
    error_rate: float
    top_endpoints: List[Dict[str, Any]]

class RateLimitStatsResponse(BaseModel):
    """Ответ со статистикой rate limiting"""
    total_hits: int
    limit_counts: Dict[str, int]
    endpoint_counts: Dict[str, int]
    user_counts: Dict[str, int]
    top_limited_endpoints: List[Dict[str, Any]]
    top_limited_users: List[Dict[str, Any]]

@router.get("/usage", response_model=APIUsageStatsResponse)
async def get_api_usage_stats(
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    endpoint: Optional[str] = Query(None, description="Фильтр по эндпоинту"),
    user_id: Optional[str] = Query(None, description="Фильтр по пользователю"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить общую статистику использования API"""
    try:
        stats = await api_analytics_service.get_usage_stats(
            start_time=start_time,
            end_time=end_time,
            endpoint=endpoint,
            user_id=user_id
        )

        return APIUsageStatsResponse(
            total_requests=stats.total_requests,
            unique_users=stats.unique_users,
            unique_ips=stats.unique_ips,
            average_response_time=stats.average_response_time,
            error_rate=stats.error_rate,
            top_endpoints=stats.top_endpoints,
            top_users=stats.top_users,
            top_ips=stats.top_ips,
            hourly_requests=stats.hourly_requests,
            daily_requests=stats.daily_requests
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting API usage stats: {e}"
        )

@router.get("/endpoints/{endpoint}/stats", response_model=EndpointStatsResponse)
async def get_endpoint_stats(
    endpoint: str,
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику для конкретного эндпоинта"""
    try:
        stats = await api_analytics_service.get_endpoint_stats(
            endpoint=endpoint,
            start_time=start_time,
            end_time=end_time
        )

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stats["error"]
            )

        return EndpointStatsResponse(
            endpoint=stats["endpoint"],
            total_requests=stats["total_requests"],
            average_response_time=stats["average_response_time"],
            error_count=stats["error_count"],
            error_rate=stats["error_rate"],
            method_counts=stats["method_counts"],
            unique_users=stats["unique_users"],
            top_users=stats["top_users"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting endpoint stats: {e}"
        )

@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику для конкретного пользователя"""
    try:
        stats = await api_analytics_service.get_user_stats(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stats["error"]
            )

        return UserStatsResponse(
            user_id=stats["user_id"],
            total_requests=stats["total_requests"],
            average_response_time=stats["average_response_time"],
            error_count=stats["error_count"],
            error_rate=stats["error_rate"],
            top_endpoints=stats["top_endpoints"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user stats: {e}"
        )

@router.get("/rate-limits", response_model=RateLimitStatsResponse)
async def get_rate_limit_stats(
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику rate limiting"""
    try:
        stats = await api_analytics_service.get_rate_limit_stats(
            start_time=start_time,
            end_time=end_time
        )

        if "error" in stats:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=stats["error"]
            )

        return RateLimitStatsResponse(
            total_hits=stats["total_hits"],
            limit_counts=stats["limit_counts"],
            endpoint_counts=stats["endpoint_counts"],
            user_counts=stats["user_counts"],
            top_limited_endpoints=stats["top_limited_endpoints"],
            top_limited_users=stats["top_limited_users"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rate limit stats: {e}"
        )

@router.get("/health")
async def get_api_health():
    """Получить состояние API"""
    try:
        # Получаем базовую статистику за последний час
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        stats = await api_analytics_service.get_usage_stats(
            start_time=start_time,
            end_time=end_time
        )

        # Определяем состояние API
        health_status = "healthy"
        if stats.error_rate > 10:  # Более 10% ошибок
            health_status = "degraded"
        elif stats.error_rate > 25:  # Более 25% ошибок
            health_status = "unhealthy"

        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_requests": stats.total_requests,
                "error_rate": stats.error_rate,
                "average_response_time": stats.average_response_time,
                "unique_users": stats.unique_users
            },
            "uptime": "99.9%",  # Заглушка
            "version": "1.0.0"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "uptime": "unknown",
            "version": "1.0.0"
        }

@router.get("/metrics")
async def get_api_metrics(
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить метрики API в формате Prometheus"""
    try:
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if end_time is None:
            end_time = datetime.utcnow()

        stats = await api_analytics_service.get_usage_stats(
            start_time=start_time,
            end_time=end_time
        )

        # Формируем метрики в формате Prometheus
        metrics = []

        # Общие метрики
        metrics.append(f"# HELP api_requests_total Total number of API requests")
        metrics.append(f"# TYPE api_requests_total counter")
        metrics.append(f"api_requests_total {stats.total_requests}")

        metrics.append(f"# HELP api_response_time_seconds Average API response time")
        metrics.append(f"# TYPE api_response_time_seconds gauge")
        metrics.append(f"api_response_time_seconds {stats.average_response_time}")

        metrics.append(f"# HELP api_error_rate_percent API error rate percentage")
        metrics.append(f"# TYPE api_error_rate_percent gauge")
        metrics.append(f"api_error_rate_percent {stats.error_rate}")

        metrics.append(f"# HELP api_unique_users Total number of unique users")
        metrics.append(f"# TYPE api_unique_users gauge")
        metrics.append(f"api_unique_users {stats.unique_users}")

        metrics.append(f"# HELP api_unique_ips Total number of unique IP addresses")
        metrics.append(f"# TYPE api_unique_ips gauge")
        metrics.append(f"api_unique_ips {stats.unique_ips}")

        # Метрики по эндпоинтам
        for endpoint_data in stats.top_endpoints[:10]:
            endpoint = endpoint_data["endpoint"].replace(" ", "_").replace("/", "_")
            count = endpoint_data["count"]
            metrics.append(f"api_endpoint_requests_total{{endpoint=\"{endpoint}\"}} {count}")

        # Метрики по пользователям
        for user_data in stats.top_users[:10]:
            user_id = user_data["user_id"]
            count = user_data["count"]
            metrics.append(f"api_user_requests_total{{user_id=\"{user_id}\"}} {count}")

        return "\n".join(metrics)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting API metrics: {e}"
        )

@router.get("/endpoints")
async def list_endpoints(
    current_user: User = Depends(get_current_active_user)
):
    """Получить список всех эндпоинтов API"""
    try:
        # В реальном приложении здесь был бы список всех эндпоинтов
        endpoints = [
            {
                "path": "/api/v1/items",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "description": "Items management",
                "category": "items"
            },
            {
                "path": "/api/v1/parsing",
                "methods": ["POST"],
                "description": "Parsing operations",
                "category": "parsing"
            },
            {
                "path": "/api/v1/analytics",
                "methods": ["GET"],
                "description": "Analytics data",
                "category": "analytics"
            },
            {
                "path": "/api/v1/ai",
                "methods": ["GET", "POST"],
                "description": "AI features",
                "category": "ai"
            },
            {
                "path": "/api/v1/marketplaces",
                "methods": ["GET"],
                "description": "Marketplace data",
                "category": "marketplaces"
            },
            {
                "path": "/api/v1/webhooks",
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "description": "Webhook management",
                "category": "webhooks"
            },
            {
                "path": "/api/v1/websocket",
                "methods": ["GET"],
                "description": "WebSocket connections",
                "category": "websocket"
            },
            {
                "path": "/api/v1/graphql",
                "methods": ["GET", "POST"],
                "description": "GraphQL API",
                "category": "graphql"
            },
            {
                "path": "/api/v1/international",
                "methods": ["GET", "POST"],
                "description": "Internationalization",
                "category": "i18n"
            }
        ]

        return {
            "endpoints": endpoints,
            "total": len(endpoints)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing endpoints: {e}"
        )

@router.get("/performance")
async def get_performance_metrics(
    start_time: Optional[datetime] = Query(None, description="Начальное время"),
    end_time: Optional[datetime] = Query(None, description="Конечное время"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить метрики производительности API"""
    try:
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()

        stats = await api_analytics_service.get_usage_stats(
            start_time=start_time,
            end_time=end_time
        )

        # Вычисляем дополнительные метрики производительности
        requests_per_hour = stats.total_requests / ((end_time - start_time).total_seconds() / 3600) if start_time != end_time else 0

        return {
            "performance_metrics": {
                "requests_per_hour": round(requests_per_hour, 2),
                "average_response_time": round(stats.average_response_time, 3),
                "error_rate": round(stats.error_rate, 2),
                "throughput": {
                    "total_requests": stats.total_requests,
                    "unique_users": stats.unique_users,
                    "unique_ips": stats.unique_ips
                },
                "response_times": {
                    "average": round(stats.average_response_time, 3),
                    "p50": round(stats.average_response_time * 0.8, 3),  # Заглушка
                    "p95": round(stats.average_response_time * 1.5, 3),  # Заглушка
                    "p99": round(stats.average_response_time * 2.0, 3)   # Заглушка
                },
                "availability": {
                    "uptime_percentage": 99.9,  # Заглушка
                    "error_rate": round(stats.error_rate, 2),
                    "success_rate": round(100 - stats.error_rate, 2)
                }
            },
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting performance metrics: {e}"
        )

@router.post("/cleanup")
async def cleanup_old_metrics(
    days: int = Query(30, ge=1, le=365, description="Количество дней для очистки"),
    current_user: User = Depends(get_current_active_user)
):
    """Очистить старые метрики API"""
    try:
        success = await api_analytics_service.cleanup_old_metrics(days)

        if success:
            return {
                "message": f"Cleaned up API metrics older than {days} days",
                "days": days,
                "success": True
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cleanup old metrics"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up old metrics: {e}"
        )
