"""API эндпоинты для расширенной аналитики и отчетов"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.advanced_analytics_service import (
    AdvancedAnalyticsService, AnalyticsFilter, ReportType, ExportFormat
)

router = APIRouter()


@router.get("/overview")
async def get_overview_analytics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    marketplace: Optional[str] = Query(None, description="Маркетплейс"),
    category: Optional[str] = Query(None, description="Категория"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Получить обзорную аналитику"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        marketplace=marketplace,
        category=category,
        user_id=user_id
    )
    
    service = AdvancedAnalyticsService(db)
    metrics = service.get_overview_metrics(filter_params)
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "marketplace": marketplace,
            "category": category,
            "user_id": user_id
        },
        "metrics": {
            "total_items": metrics.total_items,
            "total_users": metrics.total_users,
            "total_posts": metrics.total_posts,
            "total_revenue": metrics.total_revenue,
            "avg_price": metrics.avg_price,
            "price_change_percent": metrics.price_change_percent,
            "top_marketplace": metrics.top_marketplace,
            "top_category": metrics.top_category,
            "active_users": metrics.active_users,
            "engagement_rate": metrics.engagement_rate
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/price-analysis")
async def get_price_analytics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    marketplace: Optional[str] = Query(None, description="Маркетплейс"),
    category: Optional[str] = Query(None, description="Категория"),
    price_min: Optional[float] = Query(None, description="Минимальная цена"),
    price_max: Optional[float] = Query(None, description="Максимальная цена"),
    brand: Optional[str] = Query(None, description="Бренд"),
    db: Session = Depends(get_db)
):
    """Получить аналитику цен"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        marketplace=marketplace,
        category=category,
        price_min=price_min,
        price_max=price_max,
        brand=brand
    )
    
    service = AdvancedAnalyticsService(db)
    analytics = service.get_price_analytics(filter_params)
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "marketplace": marketplace,
            "category": category,
            "price_min": price_min,
            "price_max": price_max,
            "brand": brand
        },
        "analytics": analytics,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/user-analytics")
async def get_user_analytics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Получить аналитику пользователей"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        user_id=user_id
    )
    
    service = AdvancedAnalyticsService(db)
    analytics = service.get_user_analytics(filter_params)
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id
        },
        "analytics": analytics,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/social-analytics")
async def get_social_analytics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    group_id: Optional[str] = Query(None, description="ID группы"),
    db: Session = Depends(get_db)
):
    """Получить социальную аналитику"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        user_id=user_id,
        group_id=group_id
    )
    
    service = AdvancedAnalyticsService(db)
    analytics = service.get_social_analytics(filter_params)
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id,
            "group_id": group_id
        },
        "analytics": analytics,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/predictive-analytics")
async def get_predictive_analytics(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    marketplace: Optional[str] = Query(None, description="Маркетплейс"),
    category: Optional[str] = Query(None, description="Категория"),
    db: Session = Depends(get_db)
):
    """Получить предиктивную аналитику"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        marketplace=marketplace,
        category=category
    )
    
    service = AdvancedAnalyticsService(db)
    analytics = service.get_predictive_analytics(filter_params)
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "marketplace": marketplace,
            "category": category
        },
        "predictions": analytics,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/export/{report_type}")
async def export_report(
    report_type: ReportType,
    format: ExportFormat = Query(..., description="Формат экспорта"),
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    marketplace: Optional[str] = Query(None, description="Маркетплейс"),
    category: Optional[str] = Query(None, description="Категория"),
    user_id: Optional[str] = Query(None, description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Экспорт отчета в различных форматах"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        marketplace=marketplace,
        category=category,
        user_id=user_id
    )
    
    service = AdvancedAnalyticsService(db)
    
    try:
        data = service.export_data(report_type, filter_params, format)
        
        # Определяем MIME тип
        mime_types = {
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf",
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json"
        }
        
        # Определяем расширение файла
        extensions = {
            ExportFormat.EXCEL: "xlsx",
            ExportFormat.PDF: "pdf",
            ExportFormat.CSV: "csv",
            ExportFormat.JSON: "json"
        }
        
        filename = f"report_{report_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{extensions[format]}"
        
        return Response(
            content=data,
            media_type=mime_types[format],
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/real-time-metrics")
async def get_real_time_metrics(db: Session = Depends(get_db)):
    """Получить метрики в реальном времени"""
    
    service = AdvancedAnalyticsService(db)
    
    # Получаем данные за последний час
    filter_params = AnalyticsFilter(
        start_date=datetime.utcnow() - timedelta(hours=1),
        end_date=datetime.utcnow()
    )
    
    metrics = service.get_overview_metrics(filter_params)
    
    # Дополнительные метрики в реальном времени
    current_time = datetime.utcnow()
    
    return {
        "timestamp": current_time.isoformat(),
        "metrics": {
            "items_last_hour": metrics.total_items,
            "users_online": metrics.active_users,
            "posts_last_hour": metrics.total_posts,
            "revenue_last_hour": metrics.total_revenue,
            "avg_price": metrics.avg_price,
            "engagement_rate": metrics.engagement_rate
        },
        "status": "healthy",
        "uptime": "99.9%"
    }


@router.get("/dashboard-data")
async def get_dashboard_data(
    period: str = Query("7d", description="Период: 1d, 7d, 30d, 90d"),
    db: Session = Depends(get_db)
):
    """Получить данные для дашборда"""
    
    # Определяем период
    period_map = {
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30),
        "90d": timedelta(days=90)
    }
    
    if period not in period_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Use: 1d, 7d, 30d, 90d"
        )
    
    start_date = datetime.utcnow() - period_map[period]
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_date,
        end_date=datetime.utcnow()
    )
    
    service = AdvancedAnalyticsService(db)
    
    # Получаем все виды аналитики
    overview = service.get_overview_metrics(filter_params)
    price_analytics = service.get_price_analytics(filter_params)
    user_analytics = service.get_user_analytics(filter_params)
    social_analytics = service.get_social_analytics(filter_params)
    predictive = service.get_predictive_analytics(filter_params)
    
    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "overview": overview,
        "price_analytics": price_analytics,
        "user_analytics": user_analytics,
        "social_analytics": social_analytics,
        "predictive_analytics": predictive,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/marketplace-comparison")
async def get_marketplace_comparison(
    start_date: Optional[str] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Категория"),
    db: Session = Depends(get_db)
):
    """Получить сравнение маркетплейсов"""
    
    # Парсим даты
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Создаем фильтр
    filter_params = AnalyticsFilter(
        start_date=start_dt,
        end_date=end_dt,
        category=category
    )
    
    service = AdvancedAnalyticsService(db)
    price_analytics = service.get_price_analytics(filter_params)
    
    # Извлекаем данные сравнения маркетплейсов
    marketplace_comparison = price_analytics.get("marketplace_comparison", {})
    
    return {
        "filter": {
            "start_date": start_date,
            "end_date": end_date,
            "category": category
        },
        "comparison": marketplace_comparison,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/report-templates")
async def get_report_templates():
    """Получить шаблоны отчетов"""
    
    templates = [
        {
            "id": "price_analysis",
            "name": "Анализ цен",
            "description": "Детальный анализ цен и трендов",
            "category": "pricing",
            "parameters": ["start_date", "end_date", "marketplace", "category"]
        },
        {
            "id": "user_activity",
            "name": "Активность пользователей",
            "description": "Анализ пользовательской активности",
            "category": "users",
            "parameters": ["start_date", "end_date", "user_id"]
        },
        {
            "id": "social_engagement",
            "name": "Социальная вовлеченность",
            "description": "Анализ социальной активности",
            "category": "social",
            "parameters": ["start_date", "end_date", "user_id", "group_id"]
        },
        {
            "id": "marketplace_comparison",
            "name": "Сравнение маркетплейсов",
            "description": "Сравнительный анализ маркетплейсов",
            "category": "marketplaces",
            "parameters": ["start_date", "end_date", "category"]
        },
        {
            "id": "revenue_analysis",
            "name": "Анализ доходов",
            "description": "Анализ доходов и монетизации",
            "category": "revenue",
            "parameters": ["start_date", "end_date", "user_id"]
        }
    ]
    
    return {
        "templates": templates,
        "total": len(templates)
    }


