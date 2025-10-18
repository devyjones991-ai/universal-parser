"""Сервис оптимизации базы данных"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid

from app.core.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text, func, desc, and_
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Типы оптимизации БД"""
    INDEX_CREATION = "index_creation"
    INDEX_DROPPING = "index_dropping"
    VACUUM = "vacuum"
    ANALYZE = "analyze"
    REINDEX = "reindex"
    CLUSTER = "cluster"
    PARTITION = "partition"
    STATISTICS_UPDATE = "statistics_update"
    CACHE_CLEAR = "cache_clear"
    CONNECTION_POOL_OPTIMIZATION = "connection_pool_optimization"


@dataclass
class DatabaseStats:
    """Статистика базы данных"""
    total_size_mb: float
    table_count: int
    index_count: int
    connection_count: int
    max_connections: int
    cache_hit_ratio: float
    index_usage_ratio: float
    slow_queries_count: int
    dead_tuples_count: int
    last_vacuum: Optional[datetime]
    last_analyze: Optional[datetime]


@dataclass
class TableStats:
    """Статистика таблицы"""
    table_name: str
    row_count: int
    size_mb: float
    index_count: int
    last_vacuum: Optional[datetime]
    last_analyze: Optional[datetime]
    dead_tuples: int
    live_tuples: int


@dataclass
class IndexStats:
    """Статистика индекса"""
    index_name: str
    table_name: str
    size_mb: float
    usage_count: int
    is_used: bool
    is_unique: bool
    columns: List[str]


@dataclass
class QueryStats:
    """Статистика запроса"""
    query: str
    calls: int
    total_time: float
    mean_time: float
    max_time: float
    min_time: float
    stddev_time: float
    rows: int
    shared_blks_hit: int
    shared_blks_read: int


class DatabaseOptimizer:
    """Оптимизатор базы данных"""
    
    def __init__(self):
        self.optimization_history: List[Dict[str, Any]] = []
        self.auto_optimization_enabled = True
        self.optimization_interval = 3600  # 1 час
        self.optimization_task = None
        
        # Пороговые значения для автоматической оптимизации
        self.thresholds = {
            "cache_hit_ratio": 0.95,  # 95%
            "index_usage_ratio": 0.8,  # 80%
            "table_size_mb": 1000,  # 1GB
            "dead_tuples_ratio": 0.1,  # 10%
            "slow_query_time": 1000,  # 1 секунда
        }
        
        # Запускаем автоматическую оптимизацию
        if self.auto_optimization_enabled:
            self.optimization_task = asyncio.create_task(self._auto_optimization_loop())
    
    async def _auto_optimization_loop(self):
        """Цикл автоматической оптимизации"""
        while True:
            try:
                await asyncio.sleep(self.optimization_interval)
                await self.run_auto_optimization()
            except Exception as e:
                logger.error(f"Error in auto optimization loop: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    async def get_database_stats(self) -> DatabaseStats:
        """Получить статистику базы данных"""
        try:
            async with get_async_session() as session:
                # Размер базы данных
                size_result = await session.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """))
                size_row = size_result.fetchone()
                total_size_mb = (size_row[1] / 1024 / 1024) if size_row else 0
                
                # Количество таблиц
                tables_result = await session.execute(text("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = tables_result.scalar() or 0
                
                # Количество индексов
                indexes_result = await session.execute(text("""
                    SELECT count(*) FROM pg_indexes 
                    WHERE schemaname = 'public'
                """))
                index_count = indexes_result.scalar() or 0
                
                # Подключения
                connections_result = await session.execute(text("""
                    SELECT count(*) as current_connections,
                           (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity
                """))
                conn_row = connections_result.fetchone()
                connection_count = conn_row[0] if conn_row else 0
                max_connections = conn_row[1] if conn_row else 0
                
                # Cache hit ratio
                cache_result = await session.execute(text("""
                    SELECT 
                        round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2) as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """))
                cache_hit_ratio = cache_result.scalar() or 0
                
                # Index usage ratio
                index_usage_result = await session.execute(text("""
                    SELECT 
                        round(100.0 * sum(idx_tup_read) / (sum(idx_tup_read) + sum(seq_tup_read)), 2) as index_usage_ratio
                    FROM pg_stat_user_tables
                """))
                index_usage_ratio = index_usage_result.scalar() or 0
                
                # Медленные запросы
                slow_queries_result = await session.execute(text("""
                    SELECT count(*) FROM pg_stat_statements 
                    WHERE mean_time > 1000
                """))
                slow_queries_count = slow_queries_result.scalar() or 0
                
                # Dead tuples
                dead_tuples_result = await session.execute(text("""
                    SELECT sum(n_dead_tup) FROM pg_stat_user_tables
                """))
                dead_tuples_count = dead_tuples_result.scalar() or 0
                
                # Последние операции
                last_vacuum_result = await session.execute(text("""
                    SELECT max(last_vacuum) FROM pg_stat_user_tables
                """))
                last_vacuum = last_vacuum_result.scalar()
                
                last_analyze_result = await session.execute(text("""
                    SELECT max(last_analyze) FROM pg_stat_user_tables
                """))
                last_analyze = last_analyze_result.scalar()
                
                return DatabaseStats(
                    total_size_mb=total_size_mb,
                    table_count=table_count,
                    index_count=index_count,
                    connection_count=connection_count,
                    max_connections=max_connections,
                    cache_hit_ratio=cache_hit_ratio,
                    index_usage_ratio=index_usage_ratio,
                    slow_queries_count=slow_queries_count,
                    dead_tuples_count=dead_tuples_count,
                    last_vacuum=last_vacuum,
                    last_analyze=last_analyze
                )
        
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return DatabaseStats(0, 0, 0, 0, 0, 0, 0, 0, 0, None, None)
    
    async def get_table_stats(self) -> List[TableStats]:
        """Получить статистику таблиц"""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins + n_tup_upd + n_tup_del as row_count,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                        (SELECT count(*) FROM pg_indexes WHERE tablename = t.tablename) as index_count,
                        last_vacuum,
                        last_analyze,
                        n_dead_tup,
                        n_live_tup
                    FROM pg_stat_user_tables t
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """))
                
                tables = []
                for row in result:
                    tables.append(TableStats(
                        table_name=f"{row[0]}.{row[1]}",
                        row_count=row[2] or 0,
                        size_mb=(row[4] / 1024 / 1024) if row[4] else 0,
                        index_count=row[5] or 0,
                        last_vacuum=row[6],
                        last_analyze=row[7],
                        dead_tuples=row[8] or 0,
                        live_tuples=row[9] or 0
                    ))
                
                return tables
        
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return []
    
    async def get_index_stats(self) -> List[IndexStats]:
        """Получить статистику индексов"""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        i.indexname,
                        i.tablename,
                        pg_size_pretty(pg_relation_size(i.indexname)) as size_pretty,
                        pg_relation_size(i.indexname) as size_bytes,
                        s.idx_tup_read as usage_count,
                        s.idx_tup_read > 0 as is_used,
                        i.indexdef LIKE '%UNIQUE%' as is_unique,
                        array_agg(a.attname ORDER BY a.attnum) as columns
                    FROM pg_indexes i
                    LEFT JOIN pg_stat_user_indexes s ON s.indexrelname = i.indexname
                    LEFT JOIN pg_class c ON c.relname = i.indexname
                    LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0
                    WHERE i.schemaname = 'public'
                    GROUP BY i.indexname, i.tablename, s.idx_tup_read, i.indexdef
                    ORDER BY pg_relation_size(i.indexname) DESC
                """))
                
                indexes = []
                for row in result:
                    indexes.append(IndexStats(
                        index_name=row[0],
                        table_name=row[1],
                        size_mb=(row[3] / 1024 / 1024) if row[3] else 0,
                        usage_count=row[4] or 0,
                        is_used=row[5] or False,
                        is_unique=row[6] or False,
                        columns=row[7] or []
                    ))
                
                return indexes
        
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return []
    
    async def get_slow_queries(self, limit: int = 10) -> List[QueryStats]:
        """Получить медленные запросы"""
        try:
            async with get_async_session() as session:
                result = await session.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        max_time,
                        min_time,
                        stddev_time,
                        rows,
                        shared_blks_hit,
                        shared_blks_read
                    FROM pg_stat_statements
                    WHERE mean_time > 100
                    ORDER BY mean_time DESC
                    LIMIT :limit
                """), {"limit": limit})
                
                queries = []
                for row in result:
                    queries.append(QueryStats(
                        query=row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                        calls=row[1] or 0,
                        total_time=row[2] or 0,
                        mean_time=row[3] or 0,
                        max_time=row[4] or 0,
                        min_time=row[5] or 0,
                        stddev_time=row[6] or 0,
                        rows=row[7] or 0,
                        shared_blks_hit=row[8] or 0,
                        shared_blks_read=row[9] or 0
                    ))
                
                return queries
        
        except Exception as e:
            logger.error(f"Error getting slow queries: {e}")
            return []
    
    async def create_index(self, table_name: str, columns: List[str], index_name: Optional[str] = None) -> bool:
        """Создать индекс"""
        try:
            if not index_name:
                index_name = f"idx_{table_name}_{'_'.join(columns)}"
            
            columns_str = ", ".join(columns)
            query = f"CREATE INDEX CONCURRENTLY {index_name} ON {table_name} ({columns_str})"
            
            async with get_async_session() as session:
                await session.execute(text(query))
                await session.commit()
            
            self._log_optimization(OptimizationType.INDEX_CREATION, f"Created index {index_name} on {table_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    async def drop_index(self, index_name: str) -> bool:
        """Удалить индекс"""
        try:
            async with get_async_session() as session:
                await session.execute(text(f"DROP INDEX CONCURRENTLY {index_name}"))
                await session.commit()
            
            self._log_optimization(OptimizationType.INDEX_DROPPING, f"Dropped index {index_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error dropping index: {e}")
            return False
    
    async def vacuum_table(self, table_name: str, full: bool = False) -> bool:
        """Выполнить VACUUM для таблицы"""
        try:
            vacuum_type = "VACUUM FULL" if full else "VACUUM"
            query = f"{vacuum_type} {table_name}"
            
            async with get_async_session() as session:
                await session.execute(text(query))
                await session.commit()
            
            self._log_optimization(OptimizationType.VACUUM, f"Vacuumed table {table_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error vacuuming table: {e}")
            return False
    
    async def analyze_table(self, table_name: str) -> bool:
        """Выполнить ANALYZE для таблицы"""
        try:
            async with get_async_session() as session:
                await session.execute(text(f"ANALYZE {table_name}"))
                await session.commit()
            
            self._log_optimization(OptimizationType.ANALYZE, f"Analyzed table {table_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error analyzing table: {e}")
            return False
    
    async def reindex_table(self, table_name: str) -> bool:
        """Выполнить REINDEX для таблицы"""
        try:
            async with get_async_session() as session:
                await session.execute(text(f"REINDEX TABLE {table_name}"))
                await session.commit()
            
            self._log_optimization(OptimizationType.REINDEX, f"Reindexed table {table_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error reindexing table: {e}")
            return False
    
    async def run_auto_optimization(self) -> Dict[str, Any]:
        """Запустить автоматическую оптимизацию"""
        try:
            optimizations = []
            stats = await self.get_database_stats()
            
            # VACUUM если нужно
            if stats.last_vacuum is None or (datetime.utcnow() - stats.last_vacuum).days > 7:
                tables = await self.get_table_stats()
                for table in tables:
                    if table.dead_tuples > table.live_tuples * 0.1:  # 10% dead tuples
                        success = await self.vacuum_table(table.table_name)
                        if success:
                            optimizations.append(f"Vacuumed {table.table_name}")
            
            # ANALYZE если нужно
            if stats.last_analyze is None or (datetime.utcnow() - stats.last_analyze).days > 1:
                tables = await self.get_table_stats()
                for table in tables:
                    success = await self.analyze_table(table.table_name)
                    if success:
                        optimizations.append(f"Analyzed {table.table_name}")
            
            # Удаление неиспользуемых индексов
            indexes = await self.get_index_stats()
            for index in indexes:
                if not index.is_used and index.size_mb > 10:  # Больше 10MB и не используется
                    success = await self.drop_index(index.index_name)
                    if success:
                        optimizations.append(f"Dropped unused index {index.index_name}")
            
            # Создание индексов для медленных запросов
            slow_queries = await self.get_slow_queries(5)
            for query in slow_queries:
                # В реальном приложении здесь был бы анализ запроса и создание индексов
                pass
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "optimizations": optimizations,
                "optimization_count": len(optimizations)
            }
        
        except Exception as e:
            logger.error(f"Error in auto optimization: {e}")
            return {"error": str(e)}
    
    def _log_optimization(self, optimization_type: OptimizationType, description: str):
        """Записать оптимизацию в историю"""
        self.optimization_history.append({
            "id": str(uuid.uuid4()),
            "type": optimization_type.value,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Ограничиваем историю последними 1000 записями
        if len(self.optimization_history) > 1000:
            self.optimization_history = self.optimization_history[-1000:]
    
    async def get_optimization_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить историю оптимизаций"""
        return self.optimization_history[-limit:]
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Получить рекомендации по оптимизации"""
        try:
            recommendations = []
            stats = await self.get_database_stats()
            
            # Рекомендации по кэшу
            if stats.cache_hit_ratio < self.thresholds["cache_hit_ratio"] * 100:
                recommendations.append({
                    "type": "cache",
                    "priority": "high",
                    "message": f"Cache hit ratio is {stats.cache_hit_ratio:.2f}%, should be > {self.thresholds['cache_hit_ratio'] * 100}%",
                    "action": "Increase shared_buffers or check query patterns"
                })
            
            # Рекомендации по индексам
            if stats.index_usage_ratio < self.thresholds["index_usage_ratio"] * 100:
                recommendations.append({
                    "type": "indexes",
                    "priority": "medium",
                    "message": f"Index usage ratio is {stats.index_usage_ratio:.2f}%, should be > {self.thresholds['index_usage_ratio'] * 100}%",
                    "action": "Review and optimize indexes"
                })
            
            # Рекомендации по медленным запросам
            if stats.slow_queries_count > 0:
                recommendations.append({
                    "type": "queries",
                    "priority": "high",
                    "message": f"Found {stats.slow_queries_count} slow queries",
                    "action": "Optimize slow queries or add indexes"
                })
            
            # Рекомендации по VACUUM
            if stats.last_vacuum is None or (datetime.utcnow() - stats.last_vacuum).days > 7:
                recommendations.append({
                    "type": "maintenance",
                    "priority": "medium",
                    "message": "Last VACUUM was more than 7 days ago",
                    "action": "Run VACUUM on tables with high dead tuple ratio"
                })
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return []


# Глобальный экземпляр оптимизатора БД
database_optimizer = DatabaseOptimizer()
