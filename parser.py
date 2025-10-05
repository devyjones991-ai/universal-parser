import asyncio
import httpx
import json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright
from config import settings, parsing_profiles
import re

class UniversalParser:
    def __init__(self):
        self.session = None
        self.browser = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=settings.DEFAULT_TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
        if self.browser:
            await self.browser.close()
    
    async def parse_by_profile(self, profile_name: str, **kwargs) -> List[Dict]:
        """Парсинг по заранее настроенному профилю"""
        if profile_name not in parsing_profiles:
            raise ValueError(f"Профиль {profile_name} не найден")
            
        profile = parsing_profiles[profile_name]
        
        if profile["method"] == "html":
            return await self._parse_html(profile, **kwargs)
        elif profile["method"] == "api":
            return await self._parse_api(profile, **kwargs)
        elif profile["method"] == "html_dynamic":
            return await self._parse_dynamic(profile, **kwargs)
        else:
            raise ValueError(f"Неизвестный метод: {profile['method']}")
    
    async def parse_url(self, url: str, auto_detect: bool = True) -> List[Dict]:
        """Автоматический парсинг URL с попыткой определения структуры"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            if 'application/json' in response.headers.get('content-type', ''):
                return [{"type": "json_data", "content": response.json()}]
            
            return await self._auto_parse_html(response.text, url)
            
        except Exception as e:
            return [{"error": str(e), "url": url}]
    
    async def _parse_html(self, profile: Dict, **kwargs) -> List[Dict]:
        """Парсинг статичного HTML"""
        url = profile["url"].format(**kwargs)
        response = await self.session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        results = []
        
        items = soup.select(profile["selectors"]["items"])
        
        for item in items:
            result = {}
            for field, selector in profile["selectors"].items():
                if field == "items":
                    continue
                    
                element = item.select_one(selector)
                if element:
                    if field in profile.get("attributes", {}):
                        result[field] = element.get(profile["attributes"][field])
                    else:
                        result[field] = element.get_text(strip=True)
            
            if result:
                results.append(result)
        
        return results
    
    async def _parse_api(self, profile: Dict, **kwargs) -> List[Dict]:
        """Парсинг API эндпоинтов"""
        url = profile["url"]
        params = {}
        
        # Подставляем параметры
        for key, value in profile["params"].items():
            if isinstance(value, str) and "{" in value:
                params[key] = value.format(**kwargs)
            else:
                params[key] = value
        
        response = await self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Извлекаем данные по пути
        if "data_path" in profile:
            for path_part in profile["data_path"].split("."):
                data = data[path_part]
        
        # Маппим поля
        results = []
        for item in data:
            result = {}
            for field, api_field in profile["fields"].items():
                result[field] = item.get(api_field)
            results.append(result)
        
        return results
    
    async def _parse_dynamic(self, profile: Dict, **kwargs) -> List[Dict]:
        """Парсинг динамического контента через браузер"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = profile["url"].format(**kwargs)
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        
        # Ждём появления контента
        await page.wait_for_selector(profile["selectors"]["items"], timeout=10000)
        
        items = await page.query_selector_all(profile["selectors"]["items"])
        results = []
        
        for item in items:
            result = {}
            for field, selector in profile["selectors"].items():
                if field == "items":
                    continue
                    
                element = await item.query_selector(selector)
                if element:
                    result[field] = await element.text_content()
            
            if result:
                results.append(result)
        
        await browser.close()
        await playwright.stop()
        
        return results
    
    async def _auto_parse_html(self, html: str, url: str) -> List[Dict]:
        """Автоматическое определение структуры и парсинг"""
        soup = BeautifulSoup(html, "lxml")
        results = []
        
        # Ищем потенциальные контейнеры с контактами
        contact_patterns = [
            r'\+7\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}',
            r'\+7\s*\d{10}',
            r'8\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}',
            r'\b\d{3}-\d{3}-\d{4}\b'
        ]
        
        # Поиск телефонов
        for pattern in contact_patterns:
            phones = re.findall(pattern, html)
            for phone in phones:
                results.append({"type": "phone", "value": phone, "source": url})
        
        # Поиск email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', html)
        for email in emails:
            results.append({"type": "email", "value": email, "source": url})
        
        # Поиск ссылок на соцсети
        social_patterns = {
            "telegram": r't\.me/[\w\d_]+',
            "whatsapp": r'wa\.me/[\d+]+',
            "vk": r'vk\.com/[\w\d_]+',
            "instagram": r'instagram\.com/[\w\d_.]+',
        }
        
        for platform, pattern in social_patterns.items():
            links = re.findall(pattern, html)
            for link in links:
                results.append({"type": f"social_{platform}", "value": link, "source": url})
        
        return results

# Глобальный экземпляр для использования в боте
parser_instance = UniversalParser()
