"""API эндпоинты для мониторинга производительности"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.performance_monitor import performance_monitor
from app.services.database_optimizer import database_optimizer
from app.services.cache_optimizer import cache_optimizer
from app.services.monitoring_service import monitoring_service, AlertSeverity, AlertStatus
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


class PerformanceSummaryResponse(BaseModel):
    """Ответ со сводкой производительности"""
    timestamp: str
    metrics_count: int
    active_alerts: int
    system_stats: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class SystemStatsResponse(BaseModel):
    """Ответ со статистикой системы"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    timestamp: str


class DatabaseStatsResponse(BaseModel):
    """Ответ со статистикой БД"""
    total_size_mb: float
    table_count: int
    index_count: int
    connection_count: int
    max_connections: int
    cache_hit_ratio: float
    index_usage_ratio: float
    slow_queries_count: int
    dead_tuples_count: int
    last_vacuum: Optional[str]
    last_analyze: Optional[str]


class CacheStatsResponse(BaseModel):
    """Ответ со статистикой кэша"""
    hits: int
    misses: int
    hit_rate: float
    total_requests: int
    memory_usage_mb: float
    redis_usage_mb: float
    cdn_usage_mb: float
    evictions: int
    errors: int


class AlertResponse(BaseModel):
    """Ответ с алертом"""
    id: str
    rule_id: str
    title: str
    message: str
    severity: str
    status: str
    created_at: str
    acknowledged_at: Optional[str]
    resolved_at: Optional[str]
    acknowledged_by: Optional[str]
    resolved_by: Optional[str]
    metadata: Dict[str, Any]


@router.get("/summary", response_model=PerformanceSummaryResponse)
async def get_performance_summary(
    current_user: User = Depends(get_current_active_user)
):
    """Получить сводку производительности"""
    try:
        summary = await performance_monitor.get_performance_summary()
        
        return PerformanceSummaryResponse(
            timestamp=summary["timestamp"],
            metrics_count=summary["metrics_count"],
            active_alerts=summary["active_alerts"],
            system_stats=summary["system_stats"],
            performance_metrics=summary["performance_metrics"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting performance summary: {e}"
        )


@router.get("/system", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику системы"""
    try:
        stats = await performance_monitor.get_system_stats()
        
        return SystemStatsResponse(
            cpu_percent=stats.cpu_percent,
            memory_percent=stats.memory_percent,
            memory_used_mb=stats.memory_used_mb,
            memory_available_mb=stats.memory_available_mb,
            disk_usage_percent=stats.disk_usage_percent,
            disk_free_gb=stats.disk_free_gb,
            network_bytes_sent=stats.network_bytes_sent,
            network_bytes_recv=stats.network_bytes_recv,
            timestamp=stats.timestamp.isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system stats: {e}"
        )


@router.get("/database", response_model=DatabaseStatsResponse)
async def get_database_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику базы данных"""
    try:
        stats = await database_optimizer.get_database_stats()
        
        return DatabaseStatsResponse(
            total_size_mb=stats.total_size_mb,
            table_count=stats.table_count,
            index_count=stats.index_count,
            connection_count=stats.connection_count,
            max_connections=stats.max_connections,
            cache_hit_ratio=stats.cache_hit_ratio,
            index_usage_ratio=stats.index_usage_ratio,
            slow_queries_count=stats.slow_queries_count,
            dead_tuples_count=stats.dead_tuples_count,
            last_vacuum=stats.last_vacuum.isoformat() if stats.last_vacuum else None,
            last_analyze=stats.last_analyze.isoformat() if stats.last_analyze else None
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting database stats: {e}"
        )


@router.get("/cache", response_model=CacheStatsResponse)
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику кэша"""
    try:
        stats = await cache_optimizer.get_stats()
        
        return CacheStatsResponse(
            hits=stats.hits,
            misses=stats.misses,
            hit_rate=stats.hit_rate,
            total_requests=stats.total_requests,
            memory_usage_mb=stats.memory_usage_mb,
            redis_usage_mb=stats.redis_usage_mb,
            cdn_usage_mb=stats.cdn_usage_mb,
            evictions=stats.evictions,
            errors=stats.errors
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache stats: {e}"
        )


@router.get("/health")
async def get_health_status(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статус здоровья системы"""
    try:
        health = await performance_monitor.get_health_status()
        return health
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting health status: {e}"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    current_user: User = Depends(get_current_active_user)
):
    """Получить активные алерты"""
    try:
        alerts = await monitoring_service.get_active_alerts()
        
        return [
            AlertResponse(
                id=alert.id,
                rule_id=alert.rule_id,
                title=alert.title,
                message=alert.message,
                severity=alert.severity.value,
                status=alert.status.value,
                created_at=alert.created_at.isoformat(),
                acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                acknowledged_by=alert.acknowledged_by,
                resolved_by=alert.resolved_by,
                metadata=alert.metadata
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting active alerts: {e}"
        )


@router.get("/alerts/history", response_model=List[AlertResponse])
async def get_alert_history(
    limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить историю алертов"""
    try:
        alerts = await monitoring_service.get_alert_history(limit)
        
        return [
            AlertResponse(
                id=alert.id,
                rule_id=alert.rule_id,
                title=alert.title,
                message=alert.message,
                severity=alert.severity.value,
                status=alert.status.value,
                created_at=alert.created_at.isoformat(),
                acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                acknowledged_by=alert.acknowledged_by,
                resolved_by=alert.resolved_by,
                metadata=alert.metadata
            )
            for alert in alerts
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting alert history: {e}"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Подтвердить алерт"""
    try:
        success = await monitoring_service.acknowledge_alert(alert_id, current_user.username)
        
        if success:
            return {"message": f"Alert {alert_id} acknowledged"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error acknowledging alert: {e}"
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Разрешить алерт"""
    try:
        success = await monitoring_service.resolve_alert(alert_id, current_user.username)
        
        if success:
            return {"message": f"Alert {alert_id} resolved"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving alert: {e}"
        )


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    """Получить данные для дашборда мониторинга"""
    try:
        dashboard = await monitoring_service.get_monitoring_dashboard()
        return dashboard
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting monitoring dashboard: {e}"
        )


@router.get("/database/tables")
async def get_table_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику таблиц"""
    try:
        tables = await database_optimizer.get_table_stats()
        
        return {
            "tables": [
                {
                    "table_name": table.table_name,
                    "row_count": table.row_count,
                    "size_mb": table.size_mb,
                    "index_count": table.index_count,
                    "last_vacuum": table.last_vacuum.isoformat() if table.last_vacuum else None,
                    "last_analyze": table.last_analyze.isoformat() if table.last_analyze else None,
                    "dead_tuples": table.dead_tuples,
                    "live_tuples": table.live_tuples
                }
                for table in tables
            ],
            "total_tables": len(tables)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting table stats: {e}"
        )


@router.get("/database/indexes")
async def get_index_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику индексов"""
    try:
        indexes = await database_optimizer.get_index_stats()
        
        return {
            "indexes": [
                {
                    "index_name": index.index_name,
                    "table_name": index.table_name,
                    "size_mb": index.size_mb,
                    "usage_count": index.usage_count,
                    "is_used": index.is_used,
                    "is_unique": index.is_unique,
                    "columns": index.columns
                }
                for index in indexes
            ],
            "total_indexes": len(indexes)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting index stats: {e}"
        )


@router.get("/database/slow-queries")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=100, description="Количество запросов"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить медленные запросы"""
    try:
        queries = await database_optimizer.get_slow_queries(limit)
        
        return {
            "queries": [
                {
                    "query": query.query,
                    "calls": query.calls,
                    "total_time": query.total_time,
                    "mean_time": query.mean_time,
                    "max_time": query.max_time,
                    "min_time": query.min_time,
                    "stddev_time": query.stddev_time,
                    "rows": query.rows,
                    "shared_blks_hit": query.shared_blks_hit,
                    "shared_blks_read": query.shared_blks_read
                }
                for query in queries
            ],
            "total_queries": len(queries)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting slow queries: {e}"
        )


@router.post("/database/optimize")
async def run_database_optimization(
    current_user: User = Depends(get_current_active_user)
):
    """Запустить оптимизацию базы данных"""
    try:
        result = await database_optimizer.run_auto_optimization()
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running database optimization: {e}"
        )


@router.get("/database/recommendations")
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_active_user)
):
    """Получить рекомендации по оптимизации"""
    try:
        recommendations = await database_optimizer.get_optimization_recommendations()
        return {"recommendations": recommendations}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting optimization recommendations: {e}"
        )


@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Паттерн для очистки"),
    current_user: User = Depends(get_current_active_user)
):
    """Очистить кэш"""
    try:
        success = await cache_optimizer.clear(pattern)
        
        if success:
            return {"message": f"Cache cleared{' with pattern: ' + pattern if pattern else ''}"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing cache: {e}"
        )


@router.get("/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """Получить метрики производительности в формате Prometheus"""
    try:
        # Получаем все метрики
        performance_summary = await performance_monitor.get_performance_summary()
        cache_stats = await cache_optimizer.get_stats()
        db_stats = await database_optimizer.get_database_stats()
        
        # Формируем метрики в формате Prometheus
        metrics = []
        
        # Системные метрики
        system_stats = performance_summary.get("system_stats", {})
        if system_stats:
            metrics.append(f"# HELP system_cpu_percent CPU usage percentage")
            metrics.append(f"# TYPE system_cpu_percent gauge")
            metrics.append(f"system_cpu_percent {system_stats.get('cpu_percent', 0)}")
            
            metrics.append(f"# HELP system_memory_percent Memory usage percentage")
            metrics.append(f"# TYPE system_memory_percent gauge")
            metrics.append(f"system_memory_percent {system_stats.get('memory_percent', 0)}")
            
            metrics.append(f"# HELP system_disk_percent Disk usage percentage")
            metrics.append(f"# TYPE system_disk_percent gauge")
            metrics.append(f"system_disk_percent {system_stats.get('disk_usage_percent', 0)}")
        
        # Метрики кэша
        metrics.append(f"# HELP cache_hits_total Total cache hits")
        metrics.append(f"# TYPE cache_hits_total counter")
        metrics.append(f"cache_hits_total {cache_stats.hits}")
        
        metrics.append(f"# HELP cache_misses_total Total cache misses")
        metrics.append(f"# TYPE cache_misses_total counter")
        metrics.append(f"cache_misses_total {cache_stats.misses}")
        
        metrics.append(f"# HELP cache_hit_ratio Cache hit ratio percentage")
        metrics.append(f"# TYPE cache_hit_ratio gauge")
        metrics.append(f"cache_hit_ratio {cache_stats.hit_rate}")
        
        # Метрики БД
        metrics.append(f"# HELP database_size_mb Database size in MB")
        metrics.append(f"# TYPE database_size_mb gauge")
        metrics.append(f"database_size_mb {db_stats.total_size_mb}")
        
        metrics.append(f"# HELP database_connections Database connections")
        metrics.append(f"# TYPE database_connections gauge")
        metrics.append(f"database_connections {db_stats.connection_count}")
        
        metrics.append(f"# HELP database_cache_hit_ratio Database cache hit ratio")
        metrics.append(f"# TYPE database_cache_hit_ratio gauge")
        metrics.append(f"database_cache_hit_ratio {db_stats.cache_hit_ratio}")
        
        return "\n".join(metrics)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting performance metrics: {e}"
        )
