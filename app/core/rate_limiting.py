"""Система rate limiting для API"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from app.core.cache import cache_service

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Настройки rate limit"""
    requests: int
    window: int  # в секундах
    burst: Optional[int] = None  # максимальное количество запросов за раз


@dataclass
class RateLimitInfo:
    """Информация о rate limit"""
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None


class RateLimiter:
    """Rate limiter с использованием sliding window"""
    
    def __init__(self):
        self.limits: Dict[str, RateLimit] = {
            # Общие лимиты
            "global": RateLimit(requests=1000, window=3600),  # 1000 запросов в час
            "api": RateLimit(requests=100, window=60),  # 100 запросов в минуту
            "auth": RateLimit(requests=10, window=60),  # 10 попыток авторизации в минуту
            
            # Лимиты для конкретных эндпоинтов
            "parsing": RateLimit(requests=50, window=60),  # 50 запросов парсинга в минуту
            "analytics": RateLimit(requests=200, window=60),  # 200 запросов аналитики в минуту
            "webhook": RateLimit(requests=1000, window=60),  # 1000 webhook'ов в минуту
            "websocket": RateLimit(requests=100, window=60),  # 100 WebSocket соединений в минуту
            
            # Лимиты для пользователей
            "user": RateLimit(requests=1000, window=3600),  # 1000 запросов пользователя в час
            "user_burst": RateLimit(requests=20, window=60, burst=5),  # 20 запросов в минуту, макс 5 за раз
            
            # Лимиты для IP
            "ip": RateLimit(requests=500, window=3600),  # 500 запросов с IP в час
            "ip_burst": RateLimit(requests=50, window=60, burst=10),  # 50 запросов в минуту, макс 10 за раз
        }
    
    async def is_allowed(
        self,
        key: str,
        limit_name: str,
        identifier: Optional[str] = None
    ) -> Tuple[bool, RateLimitInfo]:
        """Проверить, разрешен ли запрос"""
        try:
            # Получаем настройки лимита
            if limit_name not in self.limits:
                logger.warning(f"Unknown rate limit: {limit_name}")
                return True, RateLimitInfo(limit=0, remaining=0, reset_time=0)
            
            rate_limit = self.limits[limit_name]
            
            # Формируем ключ для кэша
            cache_key = f"rate_limit:{limit_name}:{key}"
            if identifier:
                cache_key += f":{identifier}"
            
            # Получаем текущее время
            now = int(time.time())
            window_start = now - rate_limit.window
            
            # Получаем историю запросов из кэша
            requests = await self._get_requests(cache_key, window_start)
            
            # Фильтруем запросы в окне
            recent_requests = [req_time for req_time in requests if req_time > window_start]
            
            # Проверяем лимит
            if len(recent_requests) >= rate_limit.requests:
                # Лимит превышен
                oldest_request = min(recent_requests)
                reset_time = oldest_request + rate_limit.window
                retry_after = reset_time - now
                
                return False, RateLimitInfo(
                    limit=rate_limit.requests,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=max(0, retry_after)
                )
            
            # Проверяем burst лимит
            if rate_limit.burst:
                recent_burst = [req_time for req_time in recent_requests if req_time > now - 60]  # последняя минута
                if len(recent_burst) >= rate_limit.burst:
                    reset_time = now + 60
                    retry_after = 60
                    
                    return False, RateLimitInfo(
                        limit=rate_limit.requests,
                        remaining=rate_limit.requests - len(recent_requests),
                        reset_time=reset_time,
                        retry_after=retry_after
                    )
            
            # Записываем текущий запрос
            await self._record_request(cache_key, now)
            
            # Вычисляем оставшиеся запросы
            remaining = rate_limit.requests - len(recent_requests) - 1
            reset_time = now + rate_limit.window
            
            return True, RateLimitInfo(
                limit=rate_limit.requests,
                remaining=max(0, remaining),
                reset_time=reset_time
            )
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # В случае ошибки разрешаем запрос
            return True, RateLimitInfo(limit=0, remaining=0, reset_time=0)
    
    async def _get_requests(self, cache_key: str, window_start: int) -> list:
        """Получить историю запросов из кэша"""
        try:
            requests_data = await cache_service.get(cache_key)
            if requests_data:
                return [int(req_time) for req_time in requests_data if int(req_time) > window_start]
            return []
        except Exception as e:
            logger.error(f"Error getting requests from cache: {e}")
            return []
    
    async def _record_request(self, cache_key: str, timestamp: int):
        """Записать запрос в кэш"""
        try:
            # Получаем существующие запросы
            requests = await self._get_requests(cache_key, 0)
            
            # Добавляем новый запрос
            requests.append(timestamp)
            
            # Сохраняем в кэш на время окна + буфер
            ttl = 3600  # 1 час
            await cache_service.set(cache_key, requests, ttl=ttl)
        
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    async def get_usage(self, key: str, limit_name: str, identifier: Optional[str] = None) -> Dict[str, int]:
        """Получить информацию об использовании лимита"""
        try:
            if limit_name not in self.limits:
                return {"error": "Unknown rate limit"}
            
            rate_limit = self.limits[limit_name]
            cache_key = f"rate_limit:{limit_name}:{key}"
            if identifier:
                cache_key += f":{identifier}"
            
            now = int(time.time())
            window_start = now - rate_limit.window
            
            requests = await self._get_requests(cache_key, window_start)
            recent_requests = [req_time for req_time in requests if req_time > window_start]
            
            return {
                "used": len(recent_requests),
                "limit": rate_limit.requests,
                "remaining": max(0, rate_limit.requests - len(recent_requests)),
                "window": rate_limit.window,
                "reset_time": now + rate_limit.window
            }
        
        except Exception as e:
            logger.error(f"Error getting usage: {e}")
            return {"error": str(e)}
    
    async def reset_limit(self, key: str, limit_name: str, identifier: Optional[str] = None):
        """Сбросить лимит для ключа"""
        try:
            cache_key = f"rate_limit:{limit_name}:{key}"
            if identifier:
                cache_key += f":{identifier}"
            
            await cache_service.delete(cache_key)
            logger.info(f"Rate limit reset for {cache_key}")
        
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
    
    async def get_stats(self) -> Dict[str, any]:
        """Получить статистику rate limiting"""
        try:
            stats = {
                "limits": {},
                "total_limits": len(self.limits)
            }
            
            for limit_name, rate_limit in self.limits.items():
                stats["limits"][limit_name] = {
                    "requests": rate_limit.requests,
                    "window": rate_limit.window,
                    "burst": rate_limit.burst
                }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {"error": str(e)}


class RateLimitMiddleware:
    """Middleware для rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def check_rate_limit(
        self,
        request,
        limit_name: str,
        key: Optional[str] = None,
        identifier: Optional[str] = None
    ) -> Tuple[bool, RateLimitInfo]:
        """Проверить rate limit для запроса"""
        try:
            # Определяем ключ для rate limiting
            if key is None:
                # Используем IP адрес как ключ по умолчанию
                client_ip = request.client.host
                key = f"ip:{client_ip}"
            
            # Проверяем лимит
            is_allowed, rate_limit_info = await self.rate_limiter.is_allowed(
                key=key,
                limit_name=limit_name,
                identifier=identifier
            )
            
            return is_allowed, rate_limit_info
        
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            # В случае ошибки разрешаем запрос
            return True, RateLimitInfo(limit=0, remaining=0, reset_time=0)
    
    def get_rate_limit_headers(self, rate_limit_info: RateLimitInfo) -> Dict[str, str]:
        """Получить заголовки для rate limit"""
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info.limit),
            "X-RateLimit-Remaining": str(rate_limit_info.remaining),
            "X-RateLimit-Reset": str(rate_limit_info.reset_time)
        }
        
        if rate_limit_info.retry_after is not None:
            headers["Retry-After"] = str(rate_limit_info.retry_after)
        
        return headers


# Глобальные экземпляры
rate_limiter = RateLimiter()
rate_limit_middleware = RateLimitMiddleware(rate_limiter)


# Декораторы для удобства
def rate_limit(limit_name: str, key_func=None, identifier_func=None):
    """Декоратор для rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # В реальном приложении здесь была бы логика извлечения request
            # и применения rate limiting
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Утилиты для работы с rate limiting
async def check_api_rate_limit(request, user_id: Optional[str] = None) -> Tuple[bool, RateLimitInfo]:
    """Проверить rate limit для API запроса"""
    key = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
    return await rate_limit_middleware.check_rate_limit(
        request=request,
        limit_name="api",
        key=key,
        identifier=user_id
    )


async def check_auth_rate_limit(request, identifier: str) -> Tuple[bool, RateLimitInfo]:
    """Проверить rate limit для авторизации"""
    return await rate_limit_middleware.check_rate_limit(
        request=request,
        limit_name="auth",
        key=f"auth:{identifier}",
        identifier=identifier
    )


async def check_parsing_rate_limit(request, user_id: str) -> Tuple[bool, RateLimitInfo]:
    """Проверить rate limit для парсинга"""
    return await rate_limit_middleware.check_rate_limit(
        request=request,
        limit_name="parsing",
        key=f"user:{user_id}",
        identifier=user_id
    )


async def check_webhook_rate_limit(request, endpoint_id: str) -> Tuple[bool, RateLimitInfo]:
    """Проверить rate limit для webhook'ов"""
    return await rate_limit_middleware.check_rate_limit(
        request=request,
        limit_name="webhook",
        key=f"webhook:{endpoint_id}",
        identifier=endpoint_id
    )


