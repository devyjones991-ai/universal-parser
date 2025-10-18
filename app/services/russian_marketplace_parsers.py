"""Специализированные парсеры для российских маркетплейсов"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote
import re
from datetime import datetime

from app.services.parsing_service import ParsingService
from app.core.cache import cache_service


class RussianMarketplaceParser:
    """Базовый класс для российских маркетплейсов"""
    
    def __init__(self):
        self.session = None
        self.cache_ttl = 3600  # 1 час кэширования
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_headers(self, marketplace: str) -> Dict[str, str]:
        """Получить заголовки для конкретного маркетплейса"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Upgrade-Insecure-Requests": "1"
        }
        
        if marketplace == "wildberries":
            headers.update({
                "Referer": "https://www.wildberries.ru/",
                "Origin": "https://www.wildberries.ru"
            })
        elif marketplace == "ozon":
            headers.update({
                "Referer": "https://www.ozon.ru/",
                "Origin": "https://www.ozon.ru"
            })
        elif marketplace == "yandex_market":
            headers.update({
                "Referer": "https://market.yandex.ru/",
                "Origin": "https://market.yandex.ru"
            })
        elif marketplace == "avito":
            headers.update({
                "Referer": "https://www.avito.ru/",
                "Origin": "https://www.avito.ru"
            })
        
        return headers


class WildberriesParser(RussianMarketplaceParser):
    """Парсер Wildberries"""
    
    async def search_products(self, query: str, page: int = 1, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск товаров на Wildberries"""
        cache_key = f"wildberries_search:{query}:{page}:{json.dumps(filters or {}, sort_keys=True)}"
        
        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": "-1257786",
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "spp": "27",
            "suppressSpellcheck": "false",
            "page": page,
            "limit": "100"
        }
        
        # Добавляем фильтры
        if filters:
            if "price_min" in filters:
                params["priceU"] = f"{filters['price_min']}00"
            if "price_max" in filters:
                params["priceU"] = f"{filters['price_max']}00"
            if "brand" in filters:
                params["brand"] = filters["brand"]
            if "discount" in filters and filters["discount"]:
                params["sale"] = "1"
        
        url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
        headers = await self.get_headers("wildberries")
        
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                products = data.get("data", {}).get("products", [])
                
                # Обрабатываем товары
                processed_products = []
                for product in products:
                    processed_product = {
                        "id": str(product.get("id", "")),
                        "title": product.get("name", ""),
                        "price": product.get("priceU", 0) / 100,  # Цена в копейках
                        "old_price": product.get("priceU", 0) / 100,
                        "rating": product.get("reviewRating", 0),
                        "reviews_count": product.get("feedbacks", 0),
                        "stock": product.get("totalQuantity", 0),
                        "images": [f"https://images.wb.ru/images/{pic}" for pic in product.get("pics", [])],
                        "brand": product.get("brand", ""),
                        "category": product.get("subj_name", ""),
                        "seller": product.get("supplier", ""),
                        "seller_rating": product.get("supplierRating", 0),
                        "discount": product.get("sale", 0),
                        "colors": product.get("colors", []),
                        "sizes": product.get("sizes", []),
                        "url": f"https://www.wildberries.ru/catalog/{product.get('id', '')}/detail.aspx",
                        "marketplace": "wildberries"
                    }
                    processed_products.append(processed_product)
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(processed_products), self.cache_ttl)
                return processed_products
        
        return []
    
    async def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию о товаре"""
        cache_key = f"wildberries_product:{product_id}"
        
        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
        headers = await self.get_headers("wildberries")
        
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Извлекаем данные
                product_data = {
                    "id": product_id,
                    "title": self._extract_text(soup, "h1"),
                    "price": self._extract_price(soup, ".price-block__final-price"),
                    "old_price": self._extract_price(soup, ".price-block__old-price"),
                    "rating": self._extract_rating(soup, ".rating"),
                    "reviews_count": self._extract_number(soup, ".rating__count"),
                    "description": self._extract_text(soup, ".product-page__description"),
                    "characteristics": self._extract_characteristics(soup),
                    "images": self._extract_images(soup),
                    "brand": self._extract_text(soup, ".product-page__brand-name"),
                    "category": self._extract_breadcrumbs(soup),
                    "seller": self._extract_text(soup, ".seller-info__name"),
                    "delivery": self._extract_delivery_info(soup),
                    "warranty": self._extract_text(soup, ".warranty"),
                    "url": url,
                    "marketplace": "wildberries"
                }
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(product_data), self.cache_ttl)
                return product_data
        
        return None
    
    def _extract_text(self, soup: BeautifulSoup, selector: str) -> str:
        """Извлечь текст по селектору"""
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else ""
    
    def _extract_price(self, soup: BeautifulSoup, selector: str) -> float:
        """Извлечь цену по селектору"""
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            # Убираем все кроме цифр и точки
            price_text = re.sub(r'[^\d.,]', '', text)
            try:
                return float(price_text.replace(',', '.'))
            except ValueError:
                pass
        return 0.0
    
    def _extract_rating(self, soup: BeautifulSoup, selector: str) -> float:
        """Извлечь рейтинг по селектору"""
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            try:
                return float(text)
            except ValueError:
                pass
        return 0.0
    
    def _extract_number(self, soup: BeautifulSoup, selector: str) -> int:
        """Извлечь число по селектору"""
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        return 0
    
    def _extract_characteristics(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Извлечь характеристики товара"""
        characteristics = {}
        char_elements = soup.select(".product-page__characteristics .characteristics-item")
        for element in char_elements:
            name = element.select_one(".characteristics-item__name")
            value = element.select_one(".characteristics-item__value")
            if name and value:
                characteristics[name.get_text(strip=True)] = value.get_text(strip=True)
        return characteristics
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Извлечь изображения товара"""
        images = []
        img_elements = soup.select(".product-page__gallery img")
        for img in img_elements:
            src = img.get("src")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = "https://www.wildberries.ru" + src
                images.append(src)
        return images
    
    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> str:
        """Извлечь хлебные крошки"""
        breadcrumbs = []
        breadcrumb_elements = soup.select(".breadcrumbs a")
        for element in breadcrumb_elements:
            breadcrumbs.append(element.get_text(strip=True))
        return " > ".join(breadcrumbs)
    
    def _extract_delivery_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Извлечь информацию о доставке"""
        delivery_info = {}
        delivery_elements = soup.select(".delivery-info")
        for element in delivery_elements:
            title = element.select_one(".delivery-info__title")
            value = element.select_one(".delivery-info__value")
            if title and value:
                delivery_info[title.get_text(strip=True)] = value.get_text(strip=True)
        return delivery_info


class OzonParser(RussianMarketplaceParser):
    """Парсер Ozon"""
    
    async def search_products(self, query: str, page: int = 1, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск товаров на Ozon"""
        cache_key = f"ozon_search:{query}:{page}:{json.dumps(filters or {}, sort_keys=True)}"
        
        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        params = {
            "text": query,
            "page": page,
            "sorting": "popularity"
        }
        
        # Добавляем фильтры
        if filters:
            if "price_min" in filters:
                params["min_price"] = filters["price_min"]
            if "price_max" in filters:
                params["max_price"] = filters["price_max"]
            if "brand" in filters:
                params["brand"] = filters["brand"]
        
        url = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
        headers = await self.get_headers("ozon")
        
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Ozon API структура может отличаться
                products = data.get("catalog", {}).get("products", [])
                
                processed_products = []
                for product in products:
                    processed_product = {
                        "id": str(product.get("id", "")),
                        "title": product.get("name", ""),
                        "price": product.get("price", 0),
                        "old_price": product.get("oldPrice", 0),
                        "rating": product.get("rating", 0),
                        "reviews_count": product.get("reviewsCount", 0),
                        "stock": product.get("stock", 0),
                        "images": product.get("images", []),
                        "brand": product.get("brand", ""),
                        "category": product.get("category", ""),
                        "seller": product.get("seller", ""),
                        "discount": product.get("discount", 0),
                        "url": f"https://www.ozon.ru/product/{product.get('id', '')}",
                        "marketplace": "ozon"
                    }
                    processed_products.append(processed_product)
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(processed_products), self.cache_ttl)
                return processed_products
        
        return []


class YandexMarketParser(RussianMarketplaceParser):
    """Парсер Яндекс.Маркет"""
    
    async def search_products(self, query: str, page: int = 1, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск товаров на Яндекс.Маркет"""
        cache_key = f"yandex_market_search:{query}:{page}:{json.dumps(filters or {}, sort_keys=True)}"
        
        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        params = {
            "text": query,
            "page": page,
            "sort": "popularity"
        }
        
        url = "https://market.yandex.ru/search"
        headers = await self.get_headers("yandex_market")
        
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                products = []
                product_elements = soup.select("[data-zone-name='product']")
                
                for element in product_elements:
                    product_data = {
                        "id": element.get("data-id", ""),
                        "title": self._extract_text(element, "h3[data-zone-name='title'] a"),
                        "price": self._extract_price(element, "[data-zone-name='price'] .price"),
                        "old_price": self._extract_price(element, "[data-zone-name='price'] .price-old"),
                        "rating": self._extract_rating(element, "[data-zone-name='rating'] .rating"),
                        "reviews_count": self._extract_number(element, "[data-zone-name='reviews'] .reviews"),
                        "images": self._extract_images(element, "[data-zone-name='image'] img"),
                        "brand": self._extract_text(element, "[data-zone-name='brand']"),
                        "seller": self._extract_text(element, "[data-zone-name='seller']"),
                        "url": self._extract_href(element, "h3[data-zone-name='title'] a"),
                        "marketplace": "yandex_market"
                    }
                    products.append(product_data)
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(products), self.cache_ttl)
                return products
        
        return []
    
    def _extract_href(self, soup: BeautifulSoup, selector: str) -> str:
        """Извлечь ссылку по селектору"""
        element = soup.select_one(selector)
        if element:
            href = element.get("href")
            if href:
                if href.startswith("/"):
                    return "https://market.yandex.ru" + href
                return href
        return ""


class AvitoParser(RussianMarketplaceParser):
    """Парсер Avito"""
    
    async def search_products(self, query: str, page: int = 1, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск товаров на Avito"""
        cache_key = f"avito_search:{query}:{page}:{json.dumps(filters or {}, sort_keys=True)}"
        
        # Проверяем кэш
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        region = filters.get("region", "moskva") if filters else "moskva"
        params = {
            "q": query,
            "p": page
        }
        
        url = f"https://www.avito.ru/{region}/q/{quote(query)}"
        headers = await self.get_headers("avito")
        
        async with self.session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                products = []
                product_elements = soup.select("[data-marker='item']")
                
                for element in product_elements:
                    product_data = {
                        "id": element.get("data-item-id", ""),
                        "title": self._extract_text(element, "[data-marker='item-title'] h3"),
                        "price": self._extract_price(element, "[data-marker='item-price']"),
                        "description": self._extract_text(element, "[data-marker='item-description']"),
                        "images": self._extract_images(element, "[data-marker='image-frame'] img"),
                        "location": self._extract_text(element, "[data-marker='item-address']"),
                        "seller": self._extract_text(element, "[data-marker='seller-info']"),
                        "views": self._extract_number(element, "[data-marker='item-views']"),
                        "date": self._extract_text(element, "[data-marker='item-date']"),
                        "category": self._extract_text(element, "[data-marker='breadcrumbs']"),
                        "url": self._extract_href(element, "[data-marker='item-title'] h3 a"),
                        "marketplace": "avito"
                    }
                    products.append(product_data)
                
                # Кэшируем результат
                await cache_service.set(cache_key, json.dumps(products), self.cache_ttl)
                return products
        
        return []


class RussianMarketplaceService:
    """Сервис для работы с российскими маркетплейсами"""
    
    def __init__(self):
        self.parsers = {
            "wildberries": WildberriesParser(),
            "ozon": OzonParser(),
            "yandex_market": YandexMarketParser(),
            "avito": AvitoParser()
        }
    
    async def search_products(self, marketplace: str, query: str, page: int = 1, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск товаров на указанном маркетплейсе"""
        if marketplace not in self.parsers:
            raise ValueError(f"Unsupported marketplace: {marketplace}")
        
        async with self.parsers[marketplace] as parser:
            return await parser.search_products(query, page, filters)
    
    async def get_product_details(self, marketplace: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Получить детальную информацию о товаре"""
        if marketplace not in self.parsers:
            raise ValueError(f"Unsupported marketplace: {marketplace}")
        
        if hasattr(self.parsers[marketplace], 'get_product_details'):
            async with self.parsers[marketplace] as parser:
                return await parser.get_product_details(product_id)
        
        return None
    
    async def get_categories(self, marketplace: str) -> Dict[str, str]:
        """Получить категории маркетплейса"""
        categories = {
            "wildberries": {
                "electronics": "Электроника",
                "clothing": "Одежда",
                "shoes": "Обувь",
                "home": "Дом и сад",
                "beauty": "Красота и здоровье",
                "sports": "Спорт и отдых",
                "auto": "Автотовары",
                "kids": "Детские товары",
                "books": "Книги",
                "food": "Продукты питания"
            },
            "ozon": {
                "electronics": "Электроника",
                "clothing": "Одежда",
                "shoes": "Обувь",
                "home": "Дом и сад",
                "beauty": "Красота и здоровье",
                "sports": "Спорт и отдых",
                "auto": "Автотовары",
                "kids": "Детские товары",
                "books": "Книги",
                "food": "Продукты питания"
            },
            "yandex_market": {
                "electronics": "Электроника",
                "computers": "Компьютеры",
                "phones": "Телефоны",
                "home": "Дом и дача",
                "clothing": "Одежда",
                "shoes": "Обувь",
                "beauty": "Красота и здоровье",
                "sports": "Спорт и отдых",
                "auto": "Автотовары",
                "kids": "Детские товары",
                "books": "Книги",
                "food": "Продукты питания"
            },
            "avito": {
                "real_estate": "Недвижимость",
                "cars": "Транспорт",
                "electronics": "Электроника",
                "clothing": "Одежда и обувь",
                "home": "Дом и дача",
                "beauty": "Красота и здоровье",
                "sports": "Спорт и отдых",
                "kids": "Детские товары",
                "animals": "Животные",
                "services": "Услуги",
                "work": "Работа",
                "business": "Готовый бизнес"
            }
        }
        
        return categories.get(marketplace, {})
    
    async def get_filters(self, marketplace: str) -> Dict[str, str]:
        """Получить доступные фильтры для маркетплейса"""
        filters = {
            "wildberries": {
                "price_min": "Минимальная цена",
                "price_max": "Максимальная цена",
                "brand": "Бренд",
                "rating": "Рейтинг",
                "discount": "Скидка",
                "in_stock": "В наличии",
                "delivery": "Доставка",
                "pickup": "Самовывоз"
            },
            "ozon": {
                "price_min": "Минимальная цена",
                "price_max": "Максимальная цена",
                "brand": "Бренд",
                "rating": "Рейтинг",
                "discount": "Скидка",
                "in_stock": "В наличии",
                "delivery": "Доставка",
                "pickup": "Самовывоз"
            },
            "yandex_market": {
                "price_min": "Минимальная цена",
                "price_max": "Максимальная цена",
                "brand": "Бренд",
                "rating": "Рейтинг",
                "discount": "Скидка",
                "in_stock": "В наличии",
                "delivery": "Доставка",
                "pickup": "Самовывоз"
            },
            "avito": {
                "price_min": "Минимальная цена",
                "price_max": "Максимальная цена",
                "region": "Регион",
                "category": "Категория",
                "condition": "Состояние",
                "seller_type": "Тип продавца",
                "with_photo": "С фото",
                "urgent": "Срочно"
            }
        }
        
        return filters.get(marketplace, {})
