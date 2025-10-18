"""API эндпоинты для webhook'ов"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.webhook_service import webhook_service, WebhookEventType, WebhookStatus
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


class WebhookEndpointCreate(BaseModel):
    """Создание webhook endpoint"""
    url: str = Field(..., description="URL для отправки webhook'ов")
    events: List[str] = Field(..., description="Список событий для подписки")
    secret: Optional[str] = Field(None, description="Секретный ключ для подписи")
    retry_count: int = Field(3, ge=1, le=10, description="Количество попыток повторной отправки")
    timeout: int = Field(30, ge=5, le=120, description="Таймаут запроса в секундах")


class WebhookEndpointUpdate(BaseModel):
    """Обновление webhook endpoint"""
    url: Optional[str] = Field(None, description="URL для отправки webhook'ов")
    events: Optional[List[str]] = Field(None, description="Список событий для подписки")
    secret: Optional[str] = Field(None, description="Секретный ключ для подписи")
    is_active: Optional[bool] = Field(None, description="Активен ли endpoint")
    retry_count: Optional[int] = Field(None, ge=1, le=10, description="Количество попыток повторной отправки")
    timeout: Optional[int] = Field(None, ge=5, le=120, description="Таймаут запроса в секундах")


class WebhookEndpointResponse(BaseModel):
    """Ответ с информацией о webhook endpoint"""
    id: str
    url: str
    events: List[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryResponse(BaseModel):
    """Ответ с информацией о доставке webhook"""
    id: str
    endpoint_id: str
    event_type: str
    status: str
    attempts: int
    max_attempts: int
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    response_status: Optional[int]
    error_message: Optional[str]


class WebhookTestRequest(BaseModel):
    """Запрос на тестирование webhook"""
    endpoint_id: str
    test_data: Optional[Dict[str, Any]] = Field(None, description="Тестовые данные")


@router.post("/endpoints", response_model=WebhookEndpointResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_endpoint(
    endpoint_data: WebhookEndpointCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Создать новый webhook endpoint"""
    try:
        # Преобразуем строки событий в enum'ы
        events = [WebhookEventType(event) for event in endpoint_data.events]
        
        endpoint = await webhook_service.create_endpoint(
            url=endpoint_data.url,
            events=events,
            secret=endpoint_data.secret,
            retry_count=endpoint_data.retry_count,
            timeout=endpoint_data.timeout
        )
        
        return WebhookEndpointResponse(
            id=endpoint.id,
            url=endpoint.url,
            events=[event.value for event in endpoint.events],
            is_active=endpoint.is_active,
            retry_count=endpoint.retry_count,
            timeout=endpoint.timeout,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating webhook endpoint: {e}"
        )


@router.get("/endpoints", response_model=List[WebhookEndpointResponse])
async def list_webhook_endpoints(
    current_user: User = Depends(get_current_active_user)
):
    """Получить список webhook endpoints"""
    try:
        endpoints = await webhook_service.list_endpoints()
        
        return [
            WebhookEndpointResponse(
                id=endpoint.id,
                url=endpoint.url,
                events=[event.value for event in endpoint.events],
                is_active=endpoint.is_active,
                retry_count=endpoint.retry_count,
                timeout=endpoint.timeout,
                created_at=endpoint.created_at,
                updated_at=endpoint.updated_at
            )
            for endpoint in endpoints
        ]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing webhook endpoints: {e}"
        )


@router.get("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def get_webhook_endpoint(
    endpoint_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Получить webhook endpoint по ID"""
    try:
        endpoint = await webhook_service.get_endpoint(endpoint_id)
        
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
        
        return WebhookEndpointResponse(
            id=endpoint.id,
            url=endpoint.url,
            events=[event.value for event in endpoint.events],
            is_active=endpoint.is_active,
            retry_count=endpoint.retry_count,
            timeout=endpoint.timeout,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting webhook endpoint: {e}"
        )


@router.put("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def update_webhook_endpoint(
    endpoint_id: str,
    endpoint_data: WebhookEndpointUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Обновить webhook endpoint"""
    try:
        # Преобразуем строки событий в enum'ы если они предоставлены
        events = None
        if endpoint_data.events:
            events = [WebhookEventType(event) for event in endpoint_data.events]
        
        endpoint = await webhook_service.update_endpoint(
            endpoint_id=endpoint_id,
            url=endpoint_data.url,
            events=events,
            secret=endpoint_data.secret,
            is_active=endpoint_data.is_active,
            retry_count=endpoint_data.retry_count,
            timeout=endpoint_data.timeout
        )
        
        if not endpoint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
        
        return WebhookEndpointResponse(
            id=endpoint.id,
            url=endpoint.url,
            events=[event.value for event in endpoint.events],
            is_active=endpoint.is_active,
            retry_count=endpoint.retry_count,
            timeout=endpoint.timeout,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type: {e}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating webhook endpoint: {e}"
        )


@router.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_endpoint(
    endpoint_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Удалить webhook endpoint"""
    try:
        success = await webhook_service.delete_endpoint(endpoint_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting webhook endpoint: {e}"
        )


@router.post("/endpoints/{endpoint_id}/test")
async def test_webhook_endpoint(
    endpoint_id: str,
    test_request: WebhookTestRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Протестировать webhook endpoint"""
    try:
        result = await webhook_service.test_endpoint(endpoint_id)
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing webhook endpoint: {e}"
        )


@router.get("/deliveries", response_model=List[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    endpoint_id: Optional[str] = Query(None, description="Фильтр по endpoint ID"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
    current_user: User = Depends(get_current_active_user)
):
    """Получить список доставок webhook"""
    try:
        # Преобразуем строку статуса в enum если предоставлена
        status_enum = None
        if status:
            try:
                status_enum = WebhookStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        deliveries = await webhook_service.list_deliveries(
            endpoint_id=endpoint_id,
            status=status_enum,
            limit=limit
        )
        
        return [
            WebhookDeliveryResponse(
                id=delivery.id,
                endpoint_id=delivery.endpoint_id,
                event_type=delivery.event_type,
                status=delivery.status.value,
                attempts=delivery.attempts,
                max_attempts=delivery.max_attempts,
                next_retry_at=delivery.next_retry_at,
                created_at=delivery.created_at,
                updated_at=delivery.updated_at,
                response_status=delivery.response_status,
                error_message=delivery.error_message
            )
            for delivery in deliveries
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing webhook deliveries: {e}"
        )


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery(
    delivery_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Получить доставку webhook по ID"""
    try:
        delivery = await webhook_service.get_delivery(delivery_id)
        
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook delivery not found"
            )
        
        return WebhookDeliveryResponse(
            id=delivery.id,
            endpoint_id=delivery.endpoint_id,
            event_type=delivery.event_type,
            status=delivery.status.value,
            attempts=delivery.attempts,
            max_attempts=delivery.max_attempts,
            next_retry_at=delivery.next_retry_at,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at,
            response_status=delivery.response_status,
            error_message=delivery.error_message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting webhook delivery: {e}"
        )


@router.get("/stats")
async def get_webhook_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Получить статистику webhook'ов"""
    try:
        stats = await webhook_service.get_delivery_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting webhook stats: {e}"
        )


@router.post("/events/{event_type}")
async def trigger_webhook_event(
    event_type: str,
    payload: Dict[str, Any],
    endpoint_id: Optional[str] = Query(None, description="Отправить конкретному endpoint"),
    current_user: User = Depends(get_current_active_user)
):
    """Запустить webhook событие"""
    try:
        # Преобразуем строку события в enum
        try:
            event_enum = WebhookEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
        
        deliveries = await webhook_service.send_webhook(
            event_type=event_enum,
            payload=payload,
            endpoint_id=endpoint_id
        )
        
        return {
            "message": f"Webhook event {event_type} triggered",
            "deliveries_count": len(deliveries),
            "deliveries": [
                {
                    "id": delivery.id,
                    "endpoint_id": delivery.endpoint_id,
                    "status": delivery.status.value
                }
                for delivery in deliveries
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering webhook event: {e}"
        )


@router.post("/retry-failed")
async def retry_failed_deliveries(
    current_user: User = Depends(get_current_active_user)
):
    """Повторить неудачные доставки"""
    try:
        await webhook_service.retry_failed_deliveries()
        return {"message": "Failed deliveries retry initiated"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying failed deliveries: {e}"
        )


@router.post("/cleanup")
async def cleanup_old_deliveries(
    days: int = Query(30, ge=1, le=365, description="Количество дней для очистки"),
    current_user: User = Depends(get_current_active_user)
):
    """Очистить старые доставки"""
    try:
        cleaned_count = await webhook_service.cleanup_old_deliveries(days)
        return {
            "message": f"Cleaned up {cleaned_count} old deliveries",
            "cleaned_count": cleaned_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up old deliveries: {e}"
        )


@router.get("/events")
async def list_webhook_events(
    current_user: User = Depends(get_current_active_user)
):
    """Получить список доступных событий webhook"""
    try:
        events = [
            {
                "type": event.value,
                "description": event.value.replace(".", " ").title(),
                "category": event.value.split(".")[0]
            }
            for event in WebhookEventType
        ]
        
        return {
            "events": events,
            "total": len(events)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing webhook events: {e}"
        )


@router.post("/verify")
async def verify_webhook_signature(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Проверить подпись входящего webhook"""
    try:
        # Получаем заголовки
        signature = request.headers.get("X-Webhook-Signature")
        timestamp = request.headers.get("X-Webhook-Timestamp")
        
        if not signature or not timestamp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature or timestamp headers"
            )
        
        # Получаем тело запроса
        body = await request.body()
        payload = body.decode("utf-8")
        
        # Получаем секретный ключ (в реальном приложении из настроек)
        secret = "your-webhook-secret"  # Это должно быть из конфигурации
        
        # Проверяем подпись
        is_valid = webhook_service.verify_signature(
            payload=payload,
            signature=signature,
            secret=secret,
            timestamp=timestamp
        )
        
        return {
            "valid": is_valid,
            "message": "Webhook signature verified" if is_valid else "Invalid webhook signature"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying webhook signature: {e}"
        )
