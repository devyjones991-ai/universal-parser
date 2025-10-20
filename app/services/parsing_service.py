"""
Enhanced parsing service with caching and anti-detection
"""
import random
import time
from typing import Dict, List, Optional, Any
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page
from app.core.cache import cache_service, cached
from app.core.config import settings
from app.services.marketplace_parsers import get_parser
import logging

logger = logging.getLogger(__name__)

class AntiDetectionService:
    """Service for anti-detection measures"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        self.proxy_list = []  # Will be loaded from config or external service
        self.current_proxy_index = 0

    def get_random_user_agent(self) -> str:
        """Get random user agent"""
        return random.choice(self.user_agents)

    def get_random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0) -> float  # noqa  # noqa: E501 E501
        """Get random delay between requests"""
        return random.uniform(min_delay, max_delay)

    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers"""
        return {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    async def get_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxy_list:
            return None

        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

class EnhancedParsingService:
    """Enhanced parsing service with caching and anti-detection"""

    def __init__(self):
        self.anti_detection = AntiDetectionService()
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry"""
        await cache_service.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        await cache_service.disconnect()

    async def init_browser(self):
        """Initialize Playwright browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()

        # Browser options for stealth
        browser_options = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        }

        # Add proxy if configured
        if settings.use_proxy and settings.proxy_url:
            browser_options["proxy"] = {"server": settings.proxy_url}

        self.browser = await self.playwright.chromium.launch(**browser_options)

    @cached(expire=300)  # Cache for 5 minutes
    async def parse_url(self, url: str, method: str = "http") -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse URL with caching and anti-detection"""
        cache_key = f"parse:{method}:{url}"

        # Check cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result is not None:
            logger.info("Cache hit for URL: {url}")
            return cached_result

        # Parse based on method
        if method == "http":
            result = await self._parse_with_http(url)
        elif method == "browser":
            result = await self._parse_with_browser(url)
        else:
            raise ValueError(f"Unknown parsing method: {method}")

        # Cache result
        await cache_service.set(cache_key, result, expire=300)

        return result

    async def _parse_with_http(self, url: str) -> List[Dict[str, Any]]:
        """Parse URL using HTTP requests"""
        headers = self.anti_detection.get_headers()

        async with httpx.AsyncClient(
            timeout=settings.default_timeout,
            headers=headers,
            follow_redirects=True
        ) as client:
            try:
                # Add random delay
                await asyncio.sleep(self.anti_detection.get_random_delay(0.5, 1.5))

                response = await client.get(url)
                response.raise_for_status()

                # Parse based on content type
                content_type = response.headers.get("content-type", "").lower()

                if "application/json" in content_type:
                    return [{"type": "json", "data": response.json()}]
                else:
                    return await self._parse_html_content(response.text, url)

            except httpx.HTTPError as e:
                logger.error("HTTP error parsing {url}: {e}")
                return []
            except Exception as e:
                logger.error("Unexpected error parsing {url}: {e}")
                return []

    async def _parse_with_browser(self, url: str) -> List[Dict[str, Any]]:
        """Parse URL using browser automation"""
        if not self.browser:
            await self.init_browser()

        page = await self.browser.new_page()

        try:
            # Set stealth settings
            await page.set_extra_http_headers(self.anti_detection.get_headers())

            # Navigate to page
            await page.goto(url, wait_until="networkidle")

            # Add random delay
            await asyncio.sleep(self.anti_detection.get_random_delay(1.0, 2.0))

            # Get page content
            content = await page.content()

            # Parse HTML content
            result = await self._parse_html_content(content, url)

            return result

        except Exception as e:
            logger.error("Browser error parsing {url}: {e}")
            return []
        finally:
            await page.close()

    async def _parse_html_content(self, html: str, url: str) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse HTML content and extract data"""
        soup = BeautifulSoup(html, "lxml")

        # Basic data extraction
        data = {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "meta_description": "",
            "links": [],
            "images": [],
            "text_content": ""
        }

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            data["meta_description"] = meta_desc.get("content", "")

        # Extract links
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if href:
                data["links"].append({
                    "url": href,
                    "text": link.get_text(strip=True)
                })

        # Extract images
        for img in soup.find_all("img", src=True):
            src = img.get("src")
            if src:
                data["images"].append({
                    "src": src,
                    "alt": img.get("alt", ""),
                    "title": img.get("title", "")
                })

        # Extract text content
        data["text_content"] = soup.get_text(strip=True)

        return [data]

    async def parse_marketplace_item(self, marketplace: str, item_id: str) -> Optional[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse specific marketplace item"""
        cache_key = f"marketplace:{marketplace}:{item_id}"

        # Check cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Parse based on marketplace
        if marketplace == "wildberries":
            result = await self._parse_wildberries_item(item_id)
        elif marketplace == "ozon":
            result = await self._parse_ozon_item(item_id)
        elif marketplace == "yandex":
            result = await self._parse_yandex_item(item_id)
        elif marketplace in ["aliexpress", "amazon", "ebay", "lamoda", "dns"]:
            result = await self._parse_new_marketplace_item(marketplace, item_id)
        else:
            logger.warning("Unknown marketplace: {marketplace}")
            return None

        # Cache result for 10 minutes
        if result:
            await cache_service.set(cache_key, result, expire=600)

        return result

    async def _parse_wildberries_item(self, item_id: str) -> Optional[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse Wildberries item"""
        url = f"https://www.wildberries.ru/catalog/{item_id}/detail.aspx"

        try:
            result = await self.parse_url(url, method="browser")
            if result and len(result) > 0:
                return {
                    "marketplace": "wildberries",
                    "item_id": item_id,
                    "url": url,
                    "data": result[0]
                }
        except Exception as e:
            logger.error("Error parsing Wildberries item {item_id}: {e}")

        return None

    async def _parse_ozon_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Parse Ozon item"""
        url = f"https://www.ozon.ru/product/{item_id}"

        try:
            result = await self.parse_url(url, method="browser")
            if result and len(result) > 0:
                return {
                    "marketplace": "ozon",
                    "item_id": item_id,
                    "url": url,
                    "data": result[0]
                }
        except Exception as e:
            logger.error("Error parsing Ozon item {item_id}: {e}")

        return None

    async def _parse_yandex_item(self, item_id: str) -> Optional[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse Yandex Market item"""
        url = f"https://market.yandex.ru/product/{item_id}"

        try:
            result = await self.parse_url(url, method="browser")
            if result and len(result) > 0:
                return {
                    "marketplace": "yandex",
                    "item_id": item_id,
                    "url": url,
                    "data": result[0]
                }
        except Exception as e:
            logger.error("Error parsing Yandex item {item_id}: {e}")

        return None

    async def _parse_new_marketplace_item(self, marketplace: str, item_id: str) -> Optional[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Parse new marketplace item using specialized parsers"""
        try:
            # Load parsing profiles
            from app.core.config import parsing_profiles

            if marketplace not in parsing_profiles:
                logger.error("No parsing profile found for marketplace: {marketplace}")
                return None

            config = parsing_profiles[marketplace]

            # Build URL
            if 'item_url' in config:
                url = config['item_url'].format(item_id=item_id)
            else:
                logger.error("No item_url template found for marketplace: {marketplace}")
                return None

            # Parse using appropriate method
            if config.get('method') == 'html_dynamic' or config.get('use_browser', False)  # noqa  # noqa: E501 E501
                # Use browser for dynamic content
                result = await self._parse_with_browser(url)
            else:
                # Use HTTP requests
                result = await self._parse_with_http(url)

            if not result or len(result) == 0:
                return None

            # Use specialized parser for the marketplace
            parser = get_parser(marketplace, config)
            parsed_data = parser.parse_item(result[0].get('data', ''), url)

            return {
                "marketplace": marketplace,
                "item_id": item_id,
                "url": url,
                "data": parsed_data
            }

        except Exception as e:
            logger.error("Error parsing {marketplace} item {item_id}: {e}")
            return None

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get parsing cache statistics"""
        return await cache_service.get_stats()
