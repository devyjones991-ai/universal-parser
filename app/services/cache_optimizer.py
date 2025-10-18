"""Сервис оптимизации кэширования и CDN"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import pickle
import gzip
import base64

from app.core.cache import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Стратегии кэширования"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"


class CacheLevel(Enum):
    """Уровни кэширования"""
    L1_MEMORY = "l1_memory"  # In-memory cache
    L2_REDIS = "l2_redis"    # Redis cache
    L3_CDN = "l3_cdn"        # CDN cache
    L4_DATABASE = "l4_database"  # Database cache


@dataclass
class CacheConfig:
    """Конфигурация кэша"""
    key: str
    ttl: int  # секунды
    strategy: CacheStrategy
    level: CacheLevel
    compress: bool = False
    serialize: bool = True
    tags: List[str] = None
    priority: int = 0  # 0 = lowest, 10 = highest
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CacheStats:
    """Статистика кэша"""
    hits: int
    misses: int
    hit_rate: float
    total_requests: int
    memory_usage_mb: float
    redis_usage_mb: float
    cdn_usage_mb: float
    evictions: int
    errors: int


@dataclass
class CacheEntry:
    """Запись кэша"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    ttl: int
    size_bytes: int
    tags: List[str]
    level: CacheLevel


class CacheOptimizer:
    """Оптимизатор кэширования"""
    
    def __init__(self):
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "errors": 0
        }
        self.cache_configs: Dict[str, CacheConfig] = {}
        self.compression_threshold = 1024  # bytes
        self.max_memory_cache_size = 100 * 1024 * 1024  # 100MB
        self.current_memory_usage = 0
        
        # Запускаем фоновые задачи
        asyncio.create_task(self._cleanup_expired_entries())
        asyncio.create_task(self._memory_usage_monitor())
    
    async def get(
        self,
        key: str,
        default: Any = None,
        config: Optional[CacheConfig] = None
    ) -> Any:
        """Получить значение из кэша"""
        try:
            # Увеличиваем счетчик запросов
            self.cache_stats["total_requests"] = self.cache_stats.get("total_requests", 0) + 1
            
            # Пробуем получить из памяти
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not self._is_expired(entry):
                    entry.accessed_at = datetime.utcnow()
                    entry.access_count += 1
                    self.cache_stats["hits"] += 1
                    return self._deserialize_value(entry.value, config)
                else:
                    # Удаляем истекшую запись
                    del self.memory_cache[key]
                    self.current_memory_usage -= entry.size_bytes
            
            # Пробуем получить из Redis
            redis_value = await self._get_from_redis(key)
            if redis_value is not None:
                # Сохраняем в память для быстрого доступа
                await self._store_in_memory(key, redis_value, config)
                self.cache_stats["hits"] += 1
                return redis_value
            
            # Пробуем получить из CDN (если это статический контент)
            if config and config.level == CacheLevel.L3_CDN:
                cdn_value = await self._get_from_cdn(key)
                if cdn_value is not None:
                    # Сохраняем в Redis и память
                    await self._store_in_redis(key, cdn_value, config)
                    await self._store_in_memory(key, cdn_value, config)
                    self.cache_stats["hits"] += 1
                    return cdn_value
            
            # Кэш-промах
            self.cache_stats["misses"] += 1
            return default
        
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            self.cache_stats["errors"] += 1
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        config: Optional[CacheConfig] = None
    ) -> bool:
        """Сохранить значение в кэш"""
        try:
            if config is None:
                config = CacheConfig(
                    key=key,
                    ttl=3600,  # 1 час по умолчанию
                    strategy=CacheStrategy.TTL,
                    level=CacheLevel.L2_REDIS
                )
            
            # Сериализуем значение
            serialized_value = self._serialize_value(value, config)
            
            # Сохраняем в зависимости от уровня
            if config.level in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
                await self._store_in_memory(key, serialized_value, config)
                await self._store_in_redis(key, serialized_value, config)
            
            if config.level == CacheLevel.L3_CDN:
                await self._store_in_cdn(key, serialized_value, config)
            
            return True
        
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            self.cache_stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Удалить значение из кэша"""
        try:
            # Удаляем из памяти
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                del self.memory_cache[key]
                self.current_memory_usage -= entry.size_bytes
            
            # Удаляем из Redis
            await cache_service.delete(key)
            
            # Удаляем из CDN
            await self._delete_from_cdn(key)
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> bool:
        """Очистить кэш"""
        try:
            if pattern:
                # Очищаем по паттерну
                keys_to_delete = []
                for key in self.memory_cache.keys():
                    if pattern in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    await self.delete(key)
            else:
                # Очищаем все
                self.memory_cache.clear()
                self.current_memory_usage = 0
                await cache_service.clear()
            
            return True
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def _store_in_memory(self, key: str, value: Any, config: CacheConfig):
        """Сохранить в память"""
        try:
            # Проверяем размер
            serialized_value = self._serialize_value(value, config)
            size_bytes = len(str(serialized_value).encode('utf-8'))
            
            # Если превышаем лимит памяти, освобождаем место
            if self.current_memory_usage + size_bytes > self.max_memory_cache_size:
                await self._evict_from_memory()
            
            # Создаем запись
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=1,
                ttl=config.ttl,
                size_bytes=size_bytes,
                tags=config.tags,
                level=CacheLevel.L1_MEMORY
            )
            
            self.memory_cache[key] = entry
            self.current_memory_usage += size_bytes
        
        except Exception as e:
            logger.error(f"Error storing in memory: {e}")
    
    async def _store_in_redis(self, key: str, value: Any, config: CacheConfig):
        """Сохранить в Redis"""
        try:
            await cache_service.set(key, value, ttl=config.ttl)
        except Exception as e:
            logger.error(f"Error storing in Redis: {e}")
    
    async def _store_in_cdn(self, key: str, value: Any, config: CacheConfig):
        """Сохранить в CDN"""
        try:
            # В реальном приложении здесь была бы загрузка в CDN (CloudFlare, AWS CloudFront, etc.)
            logger.info(f"Storing {key} in CDN (simulated)")
        except Exception as e:
            logger.error(f"Error storing in CDN: {e}")
    
    async def _get_from_redis(self, key: str) -> Any:
        """Получить из Redis"""
        try:
            return await cache_service.get(key)
        except Exception as e:
            logger.error(f"Error getting from Redis: {e}")
            return None
    
    async def _get_from_cdn(self, key: str) -> Any:
        """Получить из CDN"""
        try:
            # В реальном приложении здесь был бы запрос к CDN
            return None
        except Exception as e:
            logger.error(f"Error getting from CDN: {e}")
            return None
    
    async def _delete_from_cdn(self, key: str):
        """Удалить из CDN"""
        try:
            # В реальном приложении здесь было бы удаление из CDN
            logger.info(f"Deleting {key} from CDN (simulated)")
        except Exception as e:
            logger.error(f"Error deleting from CDN: {e}")
    
    def _serialize_value(self, value: Any, config: CacheConfig) -> Any:
        """Сериализовать значение"""
        if not config.serialize:
            return value
        
        try:
            if config.compress and len(str(value).encode('utf-8')) > self.compression_threshold:
                # Сжимаем большие значения
                serialized = json.dumps(value, default=str).encode('utf-8')
                compressed = gzip.compress(serialized)
                return base64.b64encode(compressed).decode('utf-8')
            else:
                return json.dumps(value, default=str)
        except Exception:
            # Fallback к pickle
            return base64.b64encode(pickle.dumps(value)).decode('utf-8')
    
    def _deserialize_value(self, value: Any, config: Optional[CacheConfig]) -> Any:
        """Десериализовать значение"""
        if not config or not config.serialize:
            return value
        
        try:
            if isinstance(value, str):
                if config.compress and len(value) > self.compression_threshold:
                    # Распаковываем сжатые значения
                    compressed = base64.b64decode(value.encode('utf-8'))
                    serialized = gzip.decompress(compressed)
                    return json.loads(serialized.decode('utf-8'))
                else:
                    return json.loads(value)
            else:
                return value
        except Exception:
            # Fallback к pickle
            try:
                return pickle.loads(base64.b64decode(value.encode('utf-8')))
            except Exception:
                return value
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Проверить, истекла ли запись"""
        if entry.ttl <= 0:
            return False
        
        return (datetime.utcnow() - entry.created_at).total_seconds() > entry.ttl
    
    async def _evict_from_memory(self):
        """Освободить место в памяти"""
        try:
            # Сортируем по стратегии
            if len(self.memory_cache) == 0:
                return
            
            # LRU - удаляем наименее недавно использованные
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].accessed_at
            )
            
            # Удаляем 20% самых старых записей
            evict_count = max(1, len(sorted_entries) // 5)
            
            for i in range(evict_count):
                key, entry = sorted_entries[i]
                del self.memory_cache[key]
                self.current_memory_usage -= entry.size_bytes
                self.cache_stats["evictions"] += 1
        
        except Exception as e:
            logger.error(f"Error evicting from memory: {e}")
    
    async def _cleanup_expired_entries(self):
        """Очистка истекших записей"""
        while True:
            try:
                await asyncio.sleep(60)  # Каждую минуту
                
                expired_keys = []
                for key, entry in self.memory_cache.items():
                    if self._is_expired(entry):
                        expired_keys.append(key)
                
                for key in expired_keys:
                    entry = self.memory_cache[key]
                    del self.memory_cache[key]
                    self.current_memory_usage -= entry.size_bytes
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _memory_usage_monitor(self):
        """Мониторинг использования памяти"""
        while True:
            try:
                await asyncio.sleep(300)  # Каждые 5 минут
                
                usage_mb = self.current_memory_usage / 1024 / 1024
                max_mb = self.max_memory_cache_size / 1024 / 1024
                usage_percent = (usage_mb / max_mb) * 100
                
                if usage_percent > 80:
                    logger.warning(f"Memory cache usage is {usage_percent:.1f}% ({usage_mb:.1f}MB/{max_mb:.1f}MB)")
                    await self._evict_from_memory()
            
            except Exception as e:
                logger.error(f"Error in memory monitor: {e}")
    
    async def get_stats(self) -> CacheStats:
        """Получить статистику кэша"""
        try:
            total_requests = self.cache_stats.get("total_requests", 0)
            hits = self.cache_stats.get("hits", 0)
            misses = self.cache_stats.get("misses", 0)
            
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            
            return CacheStats(
                hits=hits,
                misses=misses,
                hit_rate=hit_rate,
                total_requests=total_requests,
                memory_usage_mb=self.current_memory_usage / 1024 / 1024,
                redis_usage_mb=0,  # В реальном приложении получали бы из Redis
                cdn_usage_mb=0,    # В реальном приложении получали бы из CDN
                evictions=self.cache_stats.get("evictions", 0),
                errors=self.cache_stats.get("errors", 0)
            )
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return CacheStats(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    async def warm_up_cache(self, warm_up_functions: List[Callable]) -> Dict[str, Any]:
        """Прогрев кэша"""
        try:
            results = {
                "warmed_up": 0,
                "failed": 0,
                "errors": []
            }
            
            for func in warm_up_functions:
                try:
                    await func()
                    results["warmed_up"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    logger.error(f"Error warming up cache with {func.__name__}: {e}")
            
            return results
        
        except Exception as e:
            logger.error(f"Error warming up cache: {e}")
            return {"error": str(e)}
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Сгенерировать ключ кэша"""
        try:
            # Создаем строку из аргументов
            key_parts = [prefix]
            
            # Добавляем позиционные аргументы
            for arg in args:
                key_parts.append(str(arg))
            
            # Добавляем именованные аргументы
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
            
            # Создаем хэш
            key_string = ":".join(key_parts)
            key_hash = hashlib.md5(key_string.encode('utf-8')).hexdigest()
            
            return f"{prefix}:{key_hash}"
        
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"{prefix}:{uuid.uuid4().hex}"


# Глобальный экземпляр оптимизатора кэша
cache_optimizer = CacheOptimizer()
