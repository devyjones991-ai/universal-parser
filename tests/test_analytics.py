"""
Тесты для модуля аналитики
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd

from analytics import AnalyticsService
from db import PriceHistory, TrackedItem


@pytest.fixture
def analytics_service():
    """Создание экземпляра AnalyticsService"""
    return AnalyticsService()


@pytest.fixture
def sample_price_history():
    """Создание тестовой истории цен"""
    base_date = datetime.utcnow()
    history = []
    
    for i in range(10):
        ph = Mock()
        ph.timestamp = base_date - timedelta(days=i)
        ph.price = 1000.0 - i * 50  # Цена падает на 50 каждый день
        ph.stock = 10 - i
        ph.rating = 4.5 - i * 0.1
        ph.tracked_item_id = 1
        history.append(ph)
    
    return history


@pytest.fixture
def sample_tracked_items():
    """Создание тестовых отслеживаемых товаров"""
    items = []
    
    for i in range(3):
        item = Mock()
        item.id = i + 1
        item.name = f"Product {i + 1}"
        item.marketplace = "wb"
        item.current_price = 1000.0 - i * 100
        item.current_stock = 10 - i
        item.current_rating = 4.5 - i * 0.2
        items.append(item)
    
    return items


class TestAnalyticsService:
    """Тесты класса AnalyticsService"""
    
    def test_get_price_trends_no_data(self, analytics_service):
        """Тест получения трендов без данных"""
        with patch('analytics.get_user_tracked_items', return_value=[]):
            trends = analytics_service.get_price_trends(123, days=30)
            assert trends == {}
    
    def test_get_price_trends_with_data(self, analytics_service, sample_tracked_items, sample_price_history):
        """Тест получения трендов с данными"""
        with patch('analytics.get_user_tracked_items', return_value=sample_tracked_items), \
             patch('analytics.get_price_history', return_value=sample_price_history):
            
            trends = analytics_service.get_price_trends(123, days=30)
            
            assert len(trends) == 3
            assert "Product 1" in trends
            assert "Product 2" in trends
            assert "Product 3" in trends
            
            # Проверяем структуру тренда
            trend = trends["Product 1"]
            assert "current_price" in trend
            assert "min_price" in trend
            assert "max_price" in trend
            assert "avg_price" in trend
            assert "price_change_percent" in trend
            assert "trend" in trend
            assert "data_points" in trend
    
    def test_get_price_trends_trend_detection(self, analytics_service, sample_tracked_items, sample_price_history):
        """Тест определения тренда"""
        with patch('analytics.get_user_tracked_items', return_value=sample_tracked_items), \
             patch('analytics.get_price_history', return_value=sample_price_history):
            
            trends = analytics_service.get_price_trends(123, days=30)
            
            # Цена падает, поэтому тренд должен быть "down"
            trend = trends["Product 1"]
            assert trend["trend"] == "down"
            assert trend["price_change_percent"] < 0
    
    def test_create_price_chart_no_data(self, analytics_service):
        """Тест создания графика без данных"""
        with patch('analytics.get_price_history', return_value=[]):
            chart_data = analytics_service.create_price_chart(123, 1, days=30)
            assert chart_data is None
    
    def test_create_price_chart_with_data(self, analytics_service, sample_price_history):
        """Тест создания графика с данными"""
        with patch('analytics.get_price_history', return_value=sample_price_history):
            chart_data = analytics_service.create_price_chart(123, 1, days=30)
            
            assert chart_data is not None
            assert isinstance(chart_data, bytes)
            assert len(chart_data) > 0
    
    def test_generate_analytics_report_no_data(self, analytics_service):
        """Тест генерации отчета без данных"""
        with patch.object(analytics_service, 'get_price_trends', return_value={}):
            report = analytics_service.generate_analytics_report(123, days=30)
            
            assert report == {}
    
    def test_generate_analytics_report_with_data(self, analytics_service, sample_tracked_items):
        """Тест генерации отчета с данными"""
        trends_data = {
            "Product 1": {
                "item_id": 1,
                "marketplace": "wb",
                "current_price": 1000.0,
                "min_price": 800.0,
                "max_price": 1200.0,
                "avg_price": 1000.0,
                "price_change": -100.0,
                "price_change_percent": -10.0,
                "data_points": 10,
                "trend": "down"
            },
            "Product 2": {
                "item_id": 2,
                "marketplace": "ozon",
                "current_price": 1500.0,
                "min_price": 1400.0,
                "max_price": 1600.0,
                "avg_price": 1500.0,
                "price_change": 100.0,
                "price_change_percent": 7.1,
                "data_points": 8,
                "trend": "up"
            }
        }
        
        with patch('analytics.get_user_tracked_items', return_value=sample_tracked_items), \
             patch.object(analytics_service, 'get_price_trends', return_value=trends_data):
            
            report = analytics_service.generate_analytics_report(123, days=30)
            
            assert report["period_days"] == 30
            assert report["total_items"] == 3
            assert report["active_trends"] == 2
            assert report["trends_summary"]["up"] == 1
            assert report["trends_summary"]["down"] == 1
            assert report["trends_summary"]["stable"] == 0
            assert len(report["top_changes"]) == 2
            assert "recommendations" in report
            assert "generated_at" in report
    
    def test_generate_recommendations(self, analytics_service):
        """Тест генерации рекомендаций"""
        trends = {
            "Product 1": {
                "price_change_percent": 25.0,
                "trend": "up"
            },
            "Product 2": {
                "price_change_percent": -30.0,
                "trend": "down"
            },
            "Product 3": {
                "price_change_percent": 5.0,
                "trend": "up"
            }
        }
        
        recommendations = analytics_service._generate_recommendations(trends)
        
        assert len(recommendations) > 0
        assert any("растут в цене" in rec for rec in recommendations)
        assert any("падают в цене" in rec for rec in recommendations)
        assert any("25%" in rec for rec in recommendations)
        assert any("30%" in rec for rec in recommendations)
    
    def test_export_to_excel_no_data(self, analytics_service):
        """Тест экспорта в Excel без данных"""
        with patch('analytics.get_user_tracked_items', return_value=[]):
            excel_data = analytics_service.export_to_excel(123, days=30)
            assert excel_data is None
    
    def test_export_to_excel_with_data(self, analytics_service, sample_tracked_items, sample_price_history):
        """Тест экспорта в Excel с данными"""
        with patch('analytics.get_user_tracked_items', return_value=sample_tracked_items), \
             patch('analytics.get_price_history', return_value=sample_price_history), \
             patch.object(analytics_service, 'get_price_trends', return_value={
                 "Product 1": {
                     "item_id": 1,
                     "marketplace": "wb",
                     "current_price": 1000.0,
                     "min_price": 800.0,
                     "max_price": 1200.0,
                     "avg_price": 1000.0,
                     "price_change_percent": -10.0,
                     "trend": "down"
                 }
             }):
            
            excel_data = analytics_service.export_to_excel(123, days=30)
            
            assert excel_data is not None
            assert isinstance(excel_data, bytes)
            assert len(excel_data) > 0


class TestAnalyticsIntegration:
    """Интеграционные тесты аналитики"""
    
    def test_full_analytics_workflow(self, analytics_service, sample_tracked_items, sample_price_history):
        """Тест полного рабочего процесса аналитики"""
        with patch('analytics.get_user_tracked_items', return_value=sample_tracked_items), \
             patch('analytics.get_price_history', return_value=sample_price_history):
            
            # 1. Получаем тренды
            trends = analytics_service.get_price_trends(123, days=30)
            assert len(trends) > 0
            
            # 2. Создаем график
            chart_data = analytics_service.create_price_chart(123, 1, days=30)
            assert chart_data is not None
            
            # 3. Генерируем отчет
            report = analytics_service.generate_analytics_report(123, days=30)
            assert report["total_items"] > 0
            
            # 4. Экспортируем в Excel
            excel_data = analytics_service.export_to_excel(123, days=30)
            assert excel_data is not None
