"""API эндпоинты для планировщика отчетов"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.report_scheduler_service import ReportSchedulerService
from app.services.advanced_analytics_service import ReportType, ExportFormat

router = APIRouter()

# Глобальный экземпляр планировщика
scheduler_service = None

def get_scheduler_service(db: Session = Depends(get_db)) -> ReportSchedulerService:
    """Получить экземпляр сервиса планировщика"""
    global scheduler_service
    if scheduler_service is None:
        scheduler_service = ReportSchedulerService(db)
    return scheduler_service


class ScheduleCreateRequest(BaseModel):
    """Запрос на создание расписания"""
    report_type: str
    schedule_type: str  # daily, weekly, monthly
    time: str  # HH:MM format
    email: str
    filters: Dict[str, Any]
    export_format: str = "pdf"


class ScheduleUpdateRequest(BaseModel):
    """Запрос на обновление расписания"""
    schedule_type: Optional[str] = None
    time: Optional[str] = None
    email: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    export_format: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/schedules")
async def create_schedule(
    request: ScheduleCreateRequest,
    user_id: str = Query(..., description="ID пользователя"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Создать расписание отчета"""
    
    # Валидация времени
    try:
        hour, minute = map(int, request.time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time format")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    
    # Валидация типа расписания
    if request.schedule_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid schedule_type. Use: daily, weekly, monthly"
        )
    
    # Валидация типа отчета
    try:
        ReportType(request.report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type"
        )
    
    # Валидация формата экспорта
    try:
        ExportFormat(request.export_format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export_format"
        )
    
    success = scheduler.create_schedule(
        user_id=user_id,
        report_type=request.report_type,
        schedule_type=request.schedule_type,
        time=request.time,
        email=request.email,
        filters=request.filters,
        export_format=request.export_format
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule"
        )
    
    return {
        "message": "Schedule created successfully",
        "user_id": user_id,
        "report_type": request.report_type,
        "schedule_type": request.schedule_type,
        "time": request.time,
        "email": request.email
    }


@router.get("/schedules")
async def get_user_schedules(
    user_id: str = Query(..., description="ID пользователя"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Получить расписания пользователя"""
    
    status = scheduler.get_schedule_status(user_id)
    return status


@router.put("/schedules/{report_type}")
async def update_schedule(
    report_type: str,
    request: ScheduleUpdateRequest,
    user_id: str = Query(..., description="ID пользователя"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Обновить расписание отчета"""
    
    # Валидация типа отчета
    try:
        ReportType(report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type"
        )
    
    # Получаем существующее расписание
    user_schedules = scheduler.get_user_schedules(user_id)
    existing_schedule = None
    
    for schedule in user_schedules:
        if schedule.report_type.value == report_type:
            existing_schedule = schedule
            break
    
    if not existing_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Обновляем параметры
    if request.schedule_type is not None:
        if request.schedule_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid schedule_type. Use: daily, weekly, monthly"
            )
        existing_schedule.schedule_type = request.schedule_type
    
    if request.time is not None:
        try:
            hour, minute = map(int, request.time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time format")
            existing_schedule.time = request.time
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time format. Use HH:MM"
            )
    
    if request.email is not None:
        existing_schedule.email = request.email
    
    if request.filters is not None:
        existing_schedule.filters = request.filters
    
    if request.export_format is not None:
        try:
            ExportFormat(request.export_format)
            existing_schedule.export_format = ExportFormat(request.export_format)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export_format"
            )
    
    if request.is_active is not None:
        existing_schedule.is_active = request.is_active
    
    # Пересчитываем следующее время запуска
    existing_schedule.next_run = existing_schedule._calculate_next_run()
    
    # Сохраняем изменения
    scheduler.update_schedule(user_id, existing_schedule.report_type, existing_schedule)
    
    return {
        "message": "Schedule updated successfully",
        "user_id": user_id,
        "report_type": report_type,
        "schedule_type": existing_schedule.schedule_type,
        "time": existing_schedule.time,
        "email": existing_schedule.email,
        "is_active": existing_schedule.is_active
    }


@router.delete("/schedules/{report_type}")
async def delete_schedule(
    report_type: str,
    user_id: str = Query(..., description="ID пользователя"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Удалить расписание отчета"""
    
    # Валидация типа отчета
    try:
        ReportType(report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type"
        )
    
    scheduler.remove_schedule(user_id, ReportType(report_type))
    
    return {
        "message": "Schedule deleted successfully",
        "user_id": user_id,
        "report_type": report_type
    }


@router.post("/schedules/{report_type}/toggle")
async def toggle_schedule(
    report_type: str,
    is_active: bool = Query(..., description="Активно ли расписание"),
    user_id: str = Query(..., description="ID пользователя"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Включить/выключить расписание"""
    
    # Валидация типа отчета
    try:
        ReportType(report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type"
        )
    
    success = scheduler.toggle_schedule(user_id, report_type, is_active)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return {
        "message": f"Schedule {'activated' if is_active else 'deactivated'} successfully",
        "user_id": user_id,
        "report_type": report_type,
        "is_active": is_active
    }


@router.post("/schedules/{report_type}/run-now")
async def run_schedule_now(
    report_type: str,
    user_id: str = Query(..., description="ID пользователя"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Запустить расписание немедленно"""
    
    # Валидация типа отчета
    try:
        ReportType(report_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report_type"
        )
    
    # Находим расписание
    user_schedules = scheduler.get_user_schedules(user_id)
    target_schedule = None
    
    for schedule in user_schedules:
        if schedule.report_type.value == report_type:
            target_schedule = schedule
            break
    
    if not target_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Запускаем генерацию отчета в фоне
    background_tasks.add_task(scheduler._generate_and_send_report, target_schedule)
    
    return {
        "message": "Report generation started",
        "user_id": user_id,
        "report_type": report_type,
        "status": "processing"
    }


@router.get("/schedules/status")
async def get_scheduler_status(
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Получить статус планировщика"""
    
    return {
        "is_running": scheduler.is_running,
        "total_schedules": len(scheduler.schedules),
        "active_schedules": len([s for s in scheduler.schedules if s.is_active]),
        "last_check": datetime.utcnow().isoformat()
    }


@router.post("/schedules/start")
async def start_scheduler(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Запустить планировщик"""
    
    if scheduler.is_running:
        return {
            "message": "Scheduler is already running",
            "status": "running"
        }
    
    background_tasks.add_task(scheduler.start_scheduler)
    
    return {
        "message": "Scheduler started",
        "status": "starting"
    }


@router.post("/schedules/stop")
async def stop_scheduler(
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Остановить планировщик"""
    
    scheduler.stop_scheduler()
    
    return {
        "message": "Scheduler stopped",
        "status": "stopped"
    }


@router.get("/templates")
async def get_report_templates():
    """Получить шаблоны отчетов для планировщика"""
    
    templates = [
        {
            "id": "price_analysis",
            "name": "Анализ цен",
            "description": "Еженедельный отчет по анализу цен и трендов",
            "category": "pricing",
            "default_schedule": "weekly",
            "default_time": "09:00",
            "parameters": ["start_date", "end_date", "marketplace", "category"]
        },
        {
            "id": "user_activity",
            "name": "Активность пользователей",
            "description": "Ежедневный отчет по активности пользователей",
            "category": "users",
            "default_schedule": "daily",
            "default_time": "08:00",
            "parameters": ["start_date", "end_date", "user_id"]
        },
        {
            "id": "social_engagement",
            "name": "Социальная вовлеченность",
            "description": "Еженедельный отчет по социальной активности",
            "category": "social",
            "default_schedule": "weekly",
            "default_time": "10:00",
            "parameters": ["start_date", "end_date", "user_id", "group_id"]
        },
        {
            "id": "marketplace_comparison",
            "name": "Сравнение маркетплейсов",
            "description": "Ежемесячный отчет по сравнению маркетплейсов",
            "category": "marketplaces",
            "default_schedule": "monthly",
            "default_time": "09:00",
            "parameters": ["start_date", "end_date", "category"]
        },
        {
            "id": "revenue_analysis",
            "name": "Анализ доходов",
            "description": "Ежемесячный отчет по доходам и монетизации",
            "category": "revenue",
            "default_schedule": "monthly",
            "default_time": "11:00",
            "parameters": ["start_date", "end_date", "user_id"]
        }
    ]
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/history")
async def get_report_history(
    user_id: str = Query(..., description="ID пользователя"),
    limit: int = Query(50, ge=1, le=100, description="Количество записей"),
    scheduler: ReportSchedulerService = Depends(get_scheduler_service)
):
    """Получить историю отчетов пользователя"""
    
    user_schedules = scheduler.get_user_schedules(user_id)
    
    history = []
    for schedule in user_schedules:
        if schedule.last_run:
            history.append({
                "report_type": schedule.report_type.value,
                "last_run": schedule.last_run.isoformat(),
                "next_run": schedule.next_run.isoformat(),
                "email": schedule.email,
                "status": "completed" if schedule.last_run else "pending"
            })
    
    # Сортируем по дате последнего запуска
    history.sort(key=lambda x: x["last_run"], reverse=True)
    
    return {
        "user_id": user_id,
        "history": history[:limit],
        "total": len(history)
    }
