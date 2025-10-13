"""
Тесты для универсального парсера
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from parser import UniversalParser


@pytest.fixture
def parser():
    """Создание экземпляра UniversalParser"""
    return UniversalParser()


@pytest.fixture
def mock_response():
    """Создание мок-HTTP ответа"""
    response = Mock()
    response.status_code = 200
    response.headers = {"content-type": "text/html"}
    response.text = """
    <html>
        <body>
            <div class="product">
                <h3 class="title">Test Product</h3>
                <span class="price">1000</span>
                <a href="/product/123" class="link">View</a>
            </div>
            <div class="product">
                <h3 class="title">Another Product</h3>
                <span class="price">2000</span>
                <a href="/product/456" class="link">View</a>
            </div>
        </body>
    </html>
    """
    return response


@pytest.fixture
def mock_json_response():
    """Создание мок-JSON ответа"""
    response = Mock()
    response.status_code = 200
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {
        "data": {
            "products": [
                {"id": 1, "name": "Product 1", "price": 1000},
                {"id": 2, "name": "Product 2", "price": 2000}
            ]
        }
    }
    return response


@pytest.fixture
def sample_profile():
    """Создание тестового профиля парсинга"""
    return {
        "name": "Test Profile",
        "url": "https://example.com/products",
        "method": "html",
        "selectors": {
            "items": ".product",
            "name": ".title",
            "price": ".price",
            "link": ".link"
        },
        "attributes": {
            "link": "href"
        }
    }


class TestUniversalParser:
    """Тесты класса UniversalParser"""
    
    @pytest.mark.asyncio
    async def test_context_manager(self, parser):
        """Тест использования как контекстного менеджера"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_client.return_value = mock_session
            
            async with parser as p:
                assert p.session == mock_session
            
            mock_session.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_by_profile_html(self, parser, sample_profile, mock_response):
        """Тест парсинга по HTML профилю"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.return_value = mock_response
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_by_profile("test_profile", **sample_profile)
            
            assert len(results) == 2
            assert results[0]["name"] == "Test Product"
            assert results[0]["price"] == "1000"
            assert results[0]["link"] == "/product/123"
            assert results[1]["name"] == "Another Product"
            assert results[1]["price"] == "2000"
            assert results[1]["link"] == "/product/456"
    
    @pytest.mark.asyncio
    async def test_parse_by_profile_api(self, parser, mock_json_response):
        """Тест парсинга по API профилю"""
        api_profile = {
            "name": "API Test",
            "url": "https://api.example.com/products",
            "method": "api",
            "params": {"page": 1, "limit": 10},
            "data_path": "data.products",
            "fields": {
                "name": "name",
                "price": "price",
                "id": "id"
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.return_value = mock_json_response
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_by_profile("api_test", **api_profile)
            
            assert len(results) == 2
            assert results[0]["name"] == "Product 1"
            assert results[0]["price"] == 1000
            assert results[0]["id"] == 1
            assert results[1]["name"] == "Product 2"
            assert results[1]["price"] == 2000
            assert results[1]["id"] == 2
    
    @pytest.mark.asyncio
    async def test_parse_url_json(self, parser, mock_json_response):
        """Тест парсинга JSON URL"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.return_value = mock_json_response
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_url("https://api.example.com/data")
            
            assert len(results) == 1
            assert results[0]["type"] == "json_data"
            assert "data" in results[0]["content"]
    
    @pytest.mark.asyncio
    async def test_parse_url_html(self, parser, mock_response):
        """Тест парсинга HTML URL"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.return_value = mock_response
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_url("https://example.com/products")
            
            # Должны найти контакты в HTML
            assert len(results) > 0
            assert any(result["type"] == "phone" for result in results)
    
    @pytest.mark.asyncio
    async def test_parse_url_error(self, parser):
        """Тест обработки ошибки при парсинге URL"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Network error")
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_url("https://invalid-url.com")
            
            assert len(results) == 1
            assert "error" in results[0]
            assert "Network error" in results[0]["error"]
    
    @pytest.mark.asyncio
    async def test_parse_by_profile_unknown_method(self, parser):
        """Тест парсинга с неизвестным методом"""
        profile = {
            "name": "Unknown Method",
            "url": "https://example.com",
            "method": "unknown"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_client.return_value = mock_session
            
            async with parser:
                with pytest.raises(ValueError, match="Неизвестный метод"):
                    await parser.parse_by_profile("unknown", **profile)
    
    @pytest.mark.asyncio
    async def test_parse_by_profile_not_found(self, parser):
        """Тест парсинга несуществующего профиля"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_client.return_value = mock_session
            
            async with parser:
                with pytest.raises(ValueError, match="Профиль unknown не найден"):
                    await parser.parse_by_profile("unknown")
    
    @pytest.mark.asyncio
    async def test_auto_parse_html_contacts(self, parser):
        """Тест автоматического парсинга контактов"""
        html_with_contacts = """
        <html>
            <body>
                <p>Телефон: +7 (999) 123-45-67</p>
                <p>Email: test@example.com</p>
                <p>Telegram: @test_user</p>
                <p>WhatsApp: +7 999 123 45 67</p>
            </body>
        </html>
        """
        
        results = await parser._auto_parse_html(html_with_contacts, "https://example.com")
        
        # Проверяем, что найдены контакты
        contact_types = [result["type"] for result in results]
        assert "phone" in contact_types
        assert "email" in contact_types
        assert "social_telegram" in contact_types
        assert "social_whatsapp" in contact_types
        
        # Проверяем конкретные значения
        phone_result = next(r for r in results if r["type"] == "phone")
        assert "+7 (999) 123-45-67" in phone_result["value"]
        
        email_result = next(r for r in results if r["type"] == "email")
        assert email_result["value"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_parse_dynamic_content(self, parser):
        """Тест парсинга динамического контента"""
        profile = {
            "name": "Dynamic Test",
            "url": "https://example.com/dynamic",
            "method": "html_dynamic",
            "selectors": {
                "items": ".product",
                "name": ".title",
                "price": ".price"
            }
        }
        
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_element = AsyncMock()
            
            # Настраиваем моки для Playwright
            mock_playwright.return_value.__aenter__.return_value = AsyncMock()
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            mock_page.wait_for_selector = AsyncMock()
            mock_page.query_selector_all.return_value = [mock_element]
            mock_element.query_selector.return_value = mock_element
            mock_element.text_content.return_value = "Test Product"
            
            async with parser:
                results = await parser.parse_by_profile("dynamic_test", **profile)
            
            assert len(results) == 1
            assert results[0]["name"] == "Test Product"
            assert results[0]["price"] == "Test Product"  # Оба селектора возвращают одно значение


class TestParserIntegration:
    """Интеграционные тесты парсера"""
    
    @pytest.mark.asyncio
    async def test_full_parsing_workflow(self, parser):
        """Тест полного рабочего процесса парсинга"""
        # 1. Парсинг по профилю
        profile = {
            "name": "Integration Test",
            "url": "https://httpbin.org/json",
            "method": "api",
            "params": {},
            "data_path": "slideshow.slides",
            "fields": {
                "title": "title",
                "type": "type"
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {
                "slideshow": {
                    "slides": [
                        {"title": "Slide 1", "type": "all"},
                        {"title": "Slide 2", "type": "all"}
                    ]
                }
            }
            mock_session.get.return_value = mock_response
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_by_profile("integration_test", **profile)
            
            assert len(results) == 2
            assert results[0]["title"] == "Slide 1"
            assert results[0]["type"] == "all"
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, parser):
        """Тест обработки ошибок в рабочем процессе"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_session.get.side_effect = Exception("Connection timeout")
            mock_client.return_value = mock_session
            
            async with parser:
                results = await parser.parse_url("https://timeout-example.com")
            
            assert len(results) == 1
            assert "error" in results[0]
            assert "Connection timeout" in results[0]["error"]


class TestParserPerformance:
    """Тесты производительности парсера"""
    
    @pytest.mark.asyncio
    async def test_concurrent_parsing(self, parser):
        """Тест параллельного парсинга"""
        import asyncio
        
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1"
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_session = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = {"test": "data"}
            mock_response.headers = {"content-type": "application/json"}
            mock_session.get.return_value = mock_response
            mock_client.return_value = mock_session
            
            async with parser:
                start_time = asyncio.get_event_loop().time()
                
                tasks = [parser.parse_url(url) for url in urls]
                results = await asyncio.gather(*tasks)
                
                end_time = asyncio.get_event_loop().time()
                duration = end_time - start_time
                
                # Параллельное выполнение должно быть быстрее последовательного
                assert duration < 3.0  # 3 запроса по 1 секунде каждый
                assert len(results) == 3
                assert all(len(result) > 0 for result in results)
