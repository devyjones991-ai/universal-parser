"""Универсальный парсер контента."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from core.clients import create_http_client
from core.config import get_settings
from profiles import load_profiles


class UniversalParser:
    """Класс для универсального парсинга страниц и API."""

    def __init__(self) -> None:
        self.session = None
        self.browser = None
        self._settings = get_settings()

    async def __aenter__(self) -> "UniversalParser":
        self.session = create_http_client(timeout=self._settings.default_timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.aclose()
        if self.browser:
            await self.browser.close()

    async def parse_by_profile(self, profile_name: str, **kwargs: Any) -> List[Dict]:
        profiles = load_profiles()
        if profile_name not in profiles:
            raise ValueError(f"Профиль {profile_name} не найден")

        profile = profiles[profile_name]
        method = profile.get("method")

        if method == "html":
            return await self._parse_html(profile, **kwargs)
        if method == "api":
            return await self._parse_api(profile, **kwargs)
        if method == "html_dynamic":
            return await self._parse_dynamic(profile, **kwargs)
        raise ValueError(f"Неизвестный метод: {method}")

    async def parse_url(self, url: str, auto_detect: bool = True) -> List[Dict]:
        try:
            response = await self.session.get(url)
            response.raise_for_status()

            if "application/json" in response.headers.get("content-type", ""):
                return [{"type": "json_data", "content": response.json()}]

            return await self._auto_parse_html(response.text, url)
        except Exception as exc:  # noqa: BLE001 - оборачиваем ошибки для ответа в боте
            return [{"error": str(exc), "url": url}]

    async def _parse_html(self, profile: Dict, **kwargs: Any) -> List[Dict]:
        url = profile["url"].format(**kwargs)
        response = await self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        results: List[Dict[str, Any]] = []
        items = soup.select(profile["selectors"]["items"])

        for item in items:
            result: Dict[str, Any] = {}
            for field, selector in profile["selectors"].items():
                if field == "items":
                    continue
                element = item.select_one(selector)
                if not element:
                    continue
                if field in profile.get("attributes", {}):
                    result[field] = element.get(profile["attributes"][field])
                else:
                    result[field] = element.get_text(strip=True)
            if result:
                results.append(result)

        return results

    async def _parse_api(self, profile: Dict, **kwargs: Any) -> List[Dict]:
        url = profile["url"]
        params: Dict[str, Any] = {}
        for key, value in profile.get("params", {}).items():
            if isinstance(value, str) and "{" in value:
                params[key] = value.format(**kwargs)
            else:
                params[key] = value

        response = await self.session.get(url, params=params)
        response.raise_for_status()
        data: Any = response.json()

        data_path = profile.get("data_path")
        if data_path:
            for part in data_path.split("."):
                data = data[part]

        results: List[Dict[str, Any]] = []
        for item in data:
            result: Dict[str, Any] = {}
            for field, api_field in profile["fields"].items():
                result[field] = item.get(api_field)
            results.append(result)
        return results

    async def _parse_dynamic(self, profile: Dict, **kwargs: Any) -> List[Dict]:
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        page = await self.browser.new_page()

        url = profile["url"].format(**kwargs)
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector(profile["selectors"]["items"], timeout=10000)

        items = await page.query_selector_all(profile["selectors"]["items"])
        results: List[Dict[str, Any]] = []
        for item in items:
            result: Dict[str, Any] = {}
            for field, selector in profile["selectors"].items():
                if field == "items":
                    continue
                element = await item.query_selector(selector)
                if element:
                    result[field] = (await element.text_content()) or ""
            if result:
                results.append(result)

        await self.browser.close()
        await playwright.stop()
        self.browser = None

        return results

    async def _auto_parse_html(self, html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        results: List[Dict[str, Any]] = []

        contact_patterns = [
            r"\+7\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}",
            r"\+7\s*\d{10}",
            r"8\s*\(\d{3}\)\s*\d{3}-\d{2}-\d{2}",
            r"\b\d{3}-\d{3}-\d{4}\b",
        ]
        for pattern in contact_patterns:
            for phone in re.findall(pattern, html):
                results.append({"type": "phone", "value": phone, "source": url})

        emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", html)
        for email in emails:
            results.append({"type": "email", "value": email, "source": url})

        social_patterns = {
            "telegram": r"t\.me/[\w\d_]+",
            "whatsapp": r"wa\.me/[\d+]+",
            "vk": r"vk\.com/[\w\d_]+",
            "instagram": r"instagram\.com/[\w\d_.]+",
        }
        for platform, pattern in social_patterns.items():
            for link in re.findall(pattern, html):
                results.append({"type": f"social_{platform}", "value": link, "source": url})

        if not results:
            # Попытка выделить основные теги, если ничего не найдено
            titles = [tag.get_text(strip=True) for tag in soup.select("h1, h2, h3")]
            for title in titles:
                if title:
                    results.append({"type": "title", "value": title, "source": url})

        return results


parser_instance = UniversalParser()

__all__ = ["UniversalParser", "parser_instance"]
