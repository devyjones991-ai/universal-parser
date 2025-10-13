"""
Тесты производительности системы
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from db import init_db, get_or_create_user, add_tracked_item, create_alert
from parser import UniversalParser
from alert_system import MonitoringService
from analytics import AnalyticsService
from subscription import SubscriptionService


@pytest.mark.slow
class TestPerformance:
    """Тесты производительности"""
    
    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Тест производительности базы данных"""
        # Инициализируем тестовую БД
        init_db()
        
        # Создаем пользователя
        user = get_or_create_user(
            telegram_id=123456789,
            username="perf_test",
            first_name="Performance",
            last_name="Test"
        )
        
        # Тест массового добавления товаров
        start_time = time.time()
        
        for i in range(100):
            add_tracked_item(
                user_id=user.id,
                item_id=f"item_{i}",
                marketplace="wb",
                name=f"Product {i}",
                url=f"https://example.com/product/{i}"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 100 товаров должны добавляться менее чем за 5 секунд
        assert duration < 5.0
        print(f"Added 100 items in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_parser_performance(self):
        """Тест производительности парсера"""
        parser = UniversalParser()
        
        # Тест параллельного парсинга
        urls = [
            "https://httpbin.org/json",
            "https://httpbin.org/json",
            "https://httpbin.org/json",
            "https://httpbin.org/json",
            "https://httpbin.org/json"
        ]
        
        start_time = time.time()
        
        async with parser:
            tasks = [parser.parse_url(url) for url in urls]
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 5 параллельных запросов должны выполняться менее чем за 10 секунд
        assert duration < 10.0
        assert len(results) == 5
        print(f"Parsed 5 URLs in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_alert_system_performance(self):
        """Тест производительности системы алертов"""
        # Создаем тестовые данные
        init_db()
        user = get_or_create_user(123456789, "alert_test", "Alert", "Test")
        
        # Добавляем товары
        for i in range(50):
            add_tracked_item(
                user_id=user.id,
                item_id=f"alert_item_{i}",
                marketplace="wb",
                name=f"Alert Product {i}"
            )
        
        # Создаем алерты
        for i in range(20):
            create_alert(
                user_id=user.id,
                alert_type="price_drop",
                conditions={"min_drop_percent": 10}
            )
        
        # Тест проверки алертов
        monitoring_service = MonitoringService()
        
        start_time = time.time()
        
        with patch.object(monitoring_service, '_get_item_current_data', return_value={
            "price": 900.0, "stock": 5, "rating": 4.0
        }):
            triggered_alerts = await monitoring_service.check_user_alerts(user.id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверка 20 алертов должна выполняться менее чем за 5 секунд
        assert duration < 5.0
        print(f"Checked 20 alerts in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_analytics_performance(self):
        """Тест производительности аналитики"""
        # Создаем тестовые данные
        init_db()
        user = get_or_create_user(123456789, "analytics_test", "Analytics", "Test")
        
        # Добавляем товары с историей цен
        for i in range(10):
            item = add_tracked_item(
                user_id=user.id,
                item_id=f"analytics_item_{i}",
                marketplace="wb",
                name=f"Analytics Product {i}"
            )
            
            # Добавляем историю цен
            from db import update_tracked_item_price
            for day in range(30):
                price = 1000.0 - day * 10 + i * 5
                update_tracked_item_price(
                    item.id,
                    price=price,
                    stock=10 - day,
                    rating=4.5 - day * 0.01
                )
        
        # Тест генерации аналитики
        analytics_service = AnalyticsService()
        
        start_time = time.time()
        
        report = analytics_service.generate_analytics_report(user.id, days=30)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Генерация отчета должна выполняться менее чем за 3 секунды
        assert duration < 3.0
        assert report["total_items"] == 10
        print(f"Generated analytics report in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_subscription_performance(self):
        """Тест производительности системы подписок"""
        subscription_service = SubscriptionService()
        
        # Тест массовой проверки лимитов
        start_time = time.time()
        
        for i in range(1000):
            can_add, _ = subscription_service.can_add_tracked_item(i)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 1000 проверок должны выполняться менее чем за 1 секунду
        assert duration < 1.0
        print(f"Checked 1000 subscription limits in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Тест использования памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Выполняем операции
        init_db()
        user = get_or_create_user(123456789, "memory_test", "Memory", "Test")
        
        for i in range(100):
            add_tracked_item(
                user_id=user.id,
                item_id=f"memory_item_{i}",
                marketplace="wb",
                name=f"Memory Product {i}"
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Увеличение памяти не должно превышать 50 MB
        assert memory_increase < 50.0
        print(f"Memory usage increased by {memory_increase:.2f} MB")


@pytest.mark.slow
class TestLoadTesting:
    """Тесты нагрузки"""
    
    @pytest.mark.asyncio
    async def test_concurrent_users(self):
        """Тест одновременной работы множества пользователей"""
        init_db()
        
        # Создаем 100 пользователей
        users = []
        for i in range(100):
            user = get_or_create_user(
                telegram_id=1000000 + i,
                username=f"load_user_{i}",
                first_name=f"Load{i}",
                last_name="Test"
            )
            users.append(user)
        
        # Каждый пользователь добавляет 5 товаров
        start_time = time.time()
        
        tasks = []
        for user in users:
            for j in range(5):
                task = add_tracked_item(
                    user_id=user.id,
                    item_id=f"load_item_{user.id}_{j}",
                    marketplace="wb",
                    name=f"Load Product {user.id}_{j}"
                )
                tasks.append(task)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 500 товаров должны добавляться менее чем за 10 секунд
        assert duration < 10.0
        print(f"Added 500 items for 100 users in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_concurrent_parsing(self):
        """Тест параллельного парсинга"""
        parser = UniversalParser()
        
        # Создаем 20 задач парсинга
        urls = [f"https://httpbin.org/json?i={i}" for i in range(20)]
        
        start_time = time.time()
        
        async with parser:
            tasks = [parser.parse_url(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 20 параллельных запросов должны выполняться менее чем за 30 секунд
        assert duration < 30.0
        
        # Проверяем, что большинство запросов успешны
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 15  # 75% успешных запросов
        
        print(f"Parsed 20 URLs in {duration:.2f} seconds, {len(successful_results)} successful")


@pytest.mark.slow
class TestStressTesting:
    """Стресс-тесты"""
    
    @pytest.mark.asyncio
    async def test_database_stress(self):
        """Стресс-тест базы данных"""
        init_db()
        user = get_or_create_user(123456789, "stress_test", "Stress", "Test")
        
        # Добавляем максимальное количество товаров
        start_time = time.time()
        
        for i in range(1000):
            add_tracked_item(
                user_id=user.id,
                item_id=f"stress_item_{i}",
                marketplace="wb",
                name=f"Stress Product {i}"
            )
            
            # Каждые 100 товаров проверяем производительность
            if i % 100 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                print(f"Added {i} items in {elapsed:.2f} seconds")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 1000 товаров должны добавляться менее чем за 60 секунд
        assert total_duration < 60.0
        print(f"Added 1000 items in {total_duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_memory_stress(self):
        """Стресс-тест памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Создаем много объектов в памяти
        objects = []
        for i in range(10000):
            obj = {
                "id": i,
                "data": "x" * 1000,  # 1KB данных
                "timestamp": datetime.utcnow()
            }
            objects.append(obj)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Увеличение памяти должно быть разумным
        assert memory_increase < 200.0  # Не более 200 MB
        print(f"Memory increased by {memory_increase:.2f} MB for 10000 objects")
        
        # Очищаем память
        del objects
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_after_cleanup = final_memory - initial_memory
        
        print(f"Memory after cleanup: {memory_after_cleanup:.2f} MB increase")
