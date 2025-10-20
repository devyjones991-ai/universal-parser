"""Сервис для работы с webhook'ами"""

import httpx
import hmac
import hashlib
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
from sqlalchemy import desc, and_

logger = logging.getLogger(__name__)

class WebhookEventType(Enum):
    """Типы событий webhook"""
    ITEM_CREATED = "item.created"
    ITEM_UPDATED = "item.updated"
    ITEM_DELETED = "item.deleted"
    PRICE_CHANGED = "price.changed"
    USER_REGISTERED = "user.registered"
    USER_SUBSCRIBED = "user.subscribed"
    PAYMENT_RECEIVED = "payment.received"
    PARSING_STARTED = "parsing.started"
    PARSING_COMPLETED = "parsing.completed"
    PARSING_FAILED = "parsing.failed"
    ANALYTICS_GENERATED = "analytics.generated"
    REPORT_SCHEDULED = "report.scheduled"
    SOCIAL_POST_CREATED = "social.post_created"
    ACHIEVEMENT_UNLOCKED = "achievement.unlocked"

class WebhookStatus(Enum):
    """Статусы webhook"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    DISABLED = "disabled"

@dataclass
class WebhookEndpoint:
    """Конечная точка webhook"""
    id: str
    url: str
    secret: str
    events: List[WebhookEventType]
    is_active: bool = True
    retry_count: int = 3
    timeout: int = 30
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class WebhookDelivery:
    """Доставка webhook"""
    id: str
    endpoint_id: str
    event_type: str
    payload: Dict[str, Any]
    status: WebhookStatus
    attempts: int = 0
    max_attempts: int = 3
    next_retry_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class WebhookService:
    """Сервис для работы с webhook'ами"""

    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.event_handlers: Dict[WebhookEventType, List[Callable]] = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Загружаем существующие webhook'и из кэша
        asyncio.create_task(self._load_webhooks())

    async def _load_webhooks(self):
        """Загрузить webhook'и из кэша"""
        try:
            cached_endpoints = await cache_service.get("webhook_endpoints")
            if cached_endpoints:
                self.endpoints = {
                    endpoint_id: WebhookEndpoint(**endpoint_data)
                    for endpoint_id, endpoint_data in cached_endpoints.items()
                }
        except Exception as e:
            logger.error("Error loading webhooks: {e}")

    async def _save_webhooks(self):
        """Сохранить webhook'и в кэш"""
        try:
            endpoints_data = {
                endpoint_id: asdict(endpoint)
                for endpoint_id, endpoint in self.endpoints.items()
            }
            await cache_service.set("webhook_endpoints", endpoints_data)
        except Exception as e:
            logger.error("Error saving webhooks: {e}")

    async def create_endpoint(
        self,
        url: str,
        events: List[WebhookEventType],
        secret: Optional[str] = None,
        retry_count: int = 3,
        timeout: int = 30
    ) -> WebhookEndpoint:
        """Создать новый webhook endpoint"""
        endpoint_id = str(uuid.uuid4())
        if secret is None:
            secret = self._generate_secret()

        endpoint = WebhookEndpoint(
            id=endpoint_id,
            url=url,
            secret=secret,
            events=events,
            retry_count=retry_count,
            timeout=timeout
        )

        self.endpoints[endpoint_id] = endpoint
        await self._save_webhooks()

        logger.info("Created webhook endpoint: {endpoint_id} for {url}")
        return endpoint

    async def update_endpoint(
        self,
        endpoint_id: str,
        url: Optional[str] = None,
        events: Optional[List[WebhookEventType]] = None,
        secret: Optional[str] = None,
        is_active: Optional[bool] = None,
        retry_count: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> Optional[WebhookEndpoint]:
        """Обновить webhook endpoint"""
        if endpoint_id not in self.endpoints:
            return None

        endpoint = self.endpoints[endpoint_id]

        if url is not None:
            endpoint.url = url
        if events is not None:
            endpoint.events = events
        if secret is not None:
            endpoint.secret = secret
        if is_active is not None:
            endpoint.is_active = is_active
        if retry_count is not None:
            endpoint.retry_count = retry_count
        if timeout is not None:
            endpoint.timeout = timeout

        endpoint.updated_at = datetime.utcnow()
        await self._save_webhooks()

        logger.info("Updated webhook endpoint: {endpoint_id}")
        return endpoint

    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """Удалить webhook endpoint"""
        if endpoint_id not in self.endpoints:
            return False

        del self.endpoints[endpoint_id]
        await self._save_webhooks()

        logger.info("Deleted webhook endpoint: {endpoint_id}")
        return True

    async def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]  # noqa  # noqa: E501 E501
        """Получить webhook endpoint"""
        return self.endpoints.get(endpoint_id)

    async def list_endpoints(self) -> List[WebhookEndpoint]:
        """Получить список всех webhook endpoints"""
        return list(self.endpoints.values())

    async def get_endpoints_for_event(self, event_type: WebhookEventType) -> List[WebhookEndpoint]  # noqa  # noqa: E501 E501
        """Получить endpoints для конкретного события"""
        return [
            endpoint for endpoint in self.endpoints.values()
            if endpoint.is_active and event_type in endpoint.events
        ]

    async def send_webhook(
        self,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        endpoint_id: Optional[str] = None
    ) -> List[WebhookDelivery]:
        """Отправить webhook"""
        deliveries = []

        if endpoint_id:
            # Отправить конкретному endpoint
            endpoint = await self.get_endpoint(endpoint_id)
            if endpoint and endpoint.is_active:
                delivery = await self._create_delivery(endpoint, event_type, payload)
                deliveries.append(delivery)
                await self._send_delivery(delivery)
        else:
            # Отправить всем подходящим endpoints
            endpoints = await self.get_endpoints_for_event(event_type)
            for endpoint in endpoints:
                delivery = await self._create_delivery(endpoint, event_type, payload)
                deliveries.append(delivery)
                await self._send_delivery(delivery)

        return deliveries

    async def _create_delivery(
        self,
        endpoint: WebhookEndpoint,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Создать delivery для webhook"""
        delivery_id = str(uuid.uuid4())

        delivery = WebhookDelivery(
            id=delivery_id,
            endpoint_id=endpoint.id,
            event_type=event_type.value,
            payload=payload,
            status=WebhookStatus.PENDING,
            max_attempts=endpoint.retry_count
        )

        self.deliveries[delivery_id] = delivery
        return delivery

    async def _send_delivery(self, delivery: WebhookDelivery):
        """Отправить delivery"""
        endpoint = await self.get_endpoint(delivery.endpoint_id)
        if not endpoint:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Endpoint not found"
            return

        try:
            # Подготовка заголовков
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Universal-Parser-Webhook/1.0",
                "X-Webhook-Event": delivery.event_type,
                "X-Webhook-Delivery": delivery.id,
                "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp()))
            }

            # Добавляем подпись
            signature = self._create_signature(
                delivery.payload,
                endpoint.secret,
                headers["X-Webhook-Timestamp"]
            )
            headers["X-Webhook-Signature"] = f"sha256={signature}"

            # Отправка запроса
            response = await self.http_client.post(
                endpoint.url,
                json=delivery.payload,
                headers=headers,
                timeout=endpoint.timeout
            )

            delivery.attempts += 1
            delivery.response_status = response.status_code
            delivery.response_body = response.text
            delivery.updated_at = datetime.utcnow()

            if 200 <= response.status_code < 300:
                delivery.status = WebhookStatus.SENT
                logger.info("Webhook delivered successfully: {delivery.id}")
            else:
                delivery.status = WebhookStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text}"
                logger.warning("Webhook delivery failed: {delivery.id} - {delivery.error_message}")

                # Планируем повторную попытку
                if delivery.attempts < delivery.max_attempts:
                    await self._schedule_retry(delivery)

        except httpx.TimeoutException:
            delivery.attempts += 1
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Request timeout"
            delivery.updated_at = datetime.utcnow()

            if delivery.attempts < delivery.max_attempts:
                await self._schedule_retry(delivery)

            logger.error("Webhook delivery timeout: {delivery.id}")

        except Exception as e:
            delivery.attempts += 1
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            delivery.updated_at = datetime.utcnow()

            if delivery.attempts < delivery.max_attempts:
                await self._schedule_retry(delivery)

            logger.error("Webhook delivery error: {delivery.id} - {e}")

    async def _schedule_retry(self, delivery: WebhookDelivery):
        """Запланировать повторную попытку"""
        # Экспоненциальная задержка: 1, 2, 4, 8 минут
        delay_minutes = 2 ** (delivery.attempts - 1)
        delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        delivery.status = WebhookStatus.RETRYING

        logger.info("Scheduled retry for webhook {delivery.id} in {delay_minutes} minutes")

    async def retry_failed_deliveries(self):
        """Повторить неудачные доставки"""
        now = datetime.utcnow()
        retry_deliveries = [
            delivery for delivery in self.deliveries.values()
            if delivery.status == WebhookStatus.RETRYING
            and delivery.next_retry_at
            and delivery.next_retry_at <= now
        ]

        for delivery in retry_deliveries:
            await self._send_delivery(delivery)

    def _create_signature(self, payload: Dict[str, Any], secret: str, timestamp: str) -> str  # noqa  # noqa: E501 E501
        """Создать подпись для webhook"""
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        message = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _generate_secret(self) -> str:
        """Сгенерировать секретный ключ"""
        import secrets
        return secrets.token_urlsafe(32)

    def verify_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
        timestamp: str
    ) -> bool:
        """Проверить подпись webhook"""
        try:
            expected_signature = self._create_signature(
                json.loads(payload),
                secret,
                timestamp
            )
            return hmac.compare_digest(signature, f"sha256={expected_signature}")
        except Exception:
            return False

    async def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]  # noqa  # noqa: E501 E501
        """Получить delivery по ID"""
        return self.deliveries.get(delivery_id)

    async def list_deliveries(
        self,
        endpoint_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Получить список deliveries"""
        deliveries = list(self.deliveries.values())

        if endpoint_id:
            deliveries = [d for d in deliveries if d.endpoint_id == endpoint_id]

        if status:
            deliveries = [d for d in deliveries if d.status == status]

        # Сортируем по дате создания (новые сначала)
        deliveries.sort(key=lambda x: x.created_at, reverse=True)

        return deliveries[:limit]

    async def get_delivery_stats(self) -> Dict[str, Any]:
        """Получить статистику deliveries"""
        total_deliveries = len(self.deliveries)

        status_counts = {}
        for delivery in self.deliveries.values():
            status = delivery.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Статистика по событиям
        event_counts = {}
        for delivery in self.deliveries.values():
            event = delivery.event_type
            event_counts[event] = event_counts.get(event, 0) + 1

        # Статистика по endpoints
        endpoint_counts = {}
        for delivery in self.deliveries.values():
            endpoint = delivery.endpoint_id
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

        return {
            "total_deliveries": total_deliveries,
            "status_counts": status_counts,
            "event_counts": event_counts,
            "endpoint_counts": endpoint_counts,
            "active_endpoints": len([e for e in self.endpoints.values() if e.is_active]),
            "total_endpoints": len(self.endpoints)
        }

    async def register_event_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable
    ):
        """Зарегистрировать обработчик события"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.info("Registered event handler for {event_type.value}")

    async def trigger_event(
        self,
        event_type: WebhookEventType,
        payload: Dict[str, Any]
    ):
        """Запустить событие"""
        # Вызываем локальные обработчики
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(payload)
                except Exception as e:
                    logger.error("Error in event handler for {event_type.value}  # noqa  # noqa: E501 E501 {e}")

        # Отправляем webhook'и
        await self.send_webhook(event_type, payload)

    async def cleanup_old_deliveries(self, days: int = 30):
        """Очистить старые deliveries"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_deliveries = [
            delivery_id for delivery_id, delivery in self.deliveries.items()
            if delivery.created_at < cutoff_date
        ]

        for delivery_id in old_deliveries:
            del self.deliveries[delivery_id]

        logger.info("Cleaned up {len(old_deliveries)} old deliveries")
        return len(old_deliveries)

    async def test_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """Протестировать webhook endpoint"""
        endpoint = await self.get_endpoint(endpoint_id)
        if not endpoint:
            return {"success": False, "error": "Endpoint not found"}

        test_payload = {
            "event": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "This is a test webhook"}
        }

        try:
            delivery = await self._create_delivery(
                endpoint,
                WebhookEventType.ITEM_CREATED,
                test_payload
            )
            await self._send_delivery(delivery)

            return {
                "success": True,
                "delivery_id": delivery.id,
                "status": delivery.status.value,
                "response_status": delivery.response_status,
                "error_message": delivery.error_message
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Глобальный экземпляр сервиса webhook
webhook_service = WebhookService()
