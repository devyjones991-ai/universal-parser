"""
Specialized parsers for different marketplaces
"""
import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketplaceParser:
    """Base class for marketplace parsers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 15)
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Clean and extract price from text"""
        if not price_text:
            return None
        
        # Remove common currency symbols and text
        price_text = re.sub(r'[^\d.,]', '', str(price_text))
        
        # Handle different decimal separators
        if ',' in price_text and '.' in price_text:
            # Both present, assume comma is thousands separator
            price_text = price_text.replace(',', '')
        elif ',' in price_text:
            # Only comma, could be decimal separator
            if len(price_text.split(',')[-1]) <= 2:
                price_text = price_text.replace(',', '.')
            else:
                price_text = price_text.replace(',', '')
        
        try:
            return float(price_text)
        except (ValueError, TypeError):
            return None
    
    def clean_rating(self, rating_text: str) -> Optional[float]:
        """Clean and extract rating from text"""
        if not rating_text:
            return None
        
        # Extract number from rating text
        rating_match = re.search(r'(\d+\.?\d*)', str(rating_text))
        if rating_match:
            try:
                rating = float(rating_match.group(1))
                # Normalize to 0-5 scale if needed
                if rating > 5:
                    rating = rating / 2  # Assume 10-point scale
                return rating
            except (ValueError, TypeError):
                pass
        
        return None
    
    def clean_stock(self, stock_text: str) -> Optional[int]:
        """Clean and extract stock quantity from text"""
        if not stock_text:
            return None
        
        # Extract number from stock text
        stock_match = re.search(r'(\d+)', str(stock_text))
        if stock_match:
            try:
                return int(stock_match.group(1))
            except (ValueError, TypeError):
                pass
        
        return None


class AliExpressParser(MarketplaceParser):
    """AliExpress specific parser"""
    
    def parse_item(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse AliExpress item page"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic info
        title = self._extract_text(soup, self.config['selectors']['title'])
        price = self._extract_price(soup, self.config['selectors']['price'])
        old_price = self._extract_price(soup, self.config['selectors']['old_price'])
        rating = self._extract_rating(soup, self.config['selectors']['rating'])
        reviews_count = self._extract_number(soup, self.config['selectors']['reviews_count'])
        stock = self._extract_stock(soup, self.config['selectors']['stock'])
        
        # Extract images
        images = self._extract_images(soup, self.config['selectors']['images'])
        
        # Extract additional info
        seller = self._extract_text(soup, self.config['selectors']['seller'])
        shipping = self._extract_text(soup, self.config['selectors']['shipping'])
        description = self._extract_text(soup, self.config['selectors']['description'])
        
        return {
            'marketplace': 'aliexpress',
            'title': title,
            'price': price,
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'stock': stock,
            'images': images,
            'seller': seller,
            'shipping': shipping,
            'description': description,
            'url': url,
            'parsed_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return None
    
    def _extract_price(self, soup, selector: str) -> Optional[float]:
        """Extract price using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_price(text)
    
    def _extract_rating(self, soup, selector: str) -> Optional[float]:
        """Extract rating using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_rating(text)
    
    def _extract_number(self, soup, selector: str) -> Optional[int]:
        """Extract number using CSS selector"""
        text = self._extract_text(soup, selector)
        if text:
            match = re.search(r'(\d+)', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _extract_stock(self, soup, selector: str) -> Optional[int]:
        """Extract stock using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_stock(text)
    
    def _extract_images(self, soup, selector: str) -> List[str]:
        """Extract image URLs using CSS selector"""
        try:
            elements = soup.select(selector)
            images = []
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []


class AmazonParser(MarketplaceParser):
    """Amazon specific parser"""
    
    def parse_item(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse Amazon item page"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic info
        title = self._extract_text(soup, self.config['selectors']['title'])
        price = self._extract_price(soup, self.config['selectors']['price'])
        old_price = self._extract_price(soup, self.config['selectors']['old_price'])
        rating = self._extract_rating(soup, self.config['selectors']['rating'])
        reviews_count = self._extract_number(soup, self.config['selectors']['reviews_count'])
        stock = self._extract_stock(soup, self.config['selectors']['stock'])
        
        # Extract images
        images = self._extract_images(soup, self.config['selectors']['images'])
        
        # Extract additional info
        seller = self._extract_text(soup, self.config['selectors']['seller'])
        shipping = self._extract_text(soup, self.config['selectors']['shipping'])
        description = self._extract_text(soup, self.config['selectors']['description'])
        
        return {
            'marketplace': 'amazon',
            'title': title,
            'price': price,
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'stock': stock,
            'images': images,
            'seller': seller,
            'shipping': shipping,
            'description': description,
            'url': url,
            'parsed_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return None
    
    def _extract_price(self, soup, selector: str) -> Optional[float]:
        """Extract price using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_price(text)
    
    def _extract_rating(self, soup, selector: str) -> Optional[float]:
        """Extract rating using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_rating(text)
    
    def _extract_number(self, soup, selector: str) -> Optional[int]:
        """Extract number using CSS selector"""
        text = self._extract_text(soup, selector)
        if text:
            match = re.search(r'(\d+)', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _extract_stock(self, soup, selector: str) -> Optional[int]:
        """Extract stock using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_stock(text)
    
    def _extract_images(self, soup, selector: str) -> List[str]:
        """Extract image URLs using CSS selector"""
        try:
            elements = soup.select(selector)
            images = []
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []


class eBayParser(MarketplaceParser):
    """eBay specific parser"""
    
    def parse_item(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse eBay item page"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic info
        title = self._extract_text(soup, self.config['selectors']['title'])
        price = self._extract_price(soup, self.config['selectors']['price'])
        old_price = self._extract_price(soup, self.config['selectors']['old_price'])
        rating = self._extract_rating(soup, self.config['selectors']['rating'])
        reviews_count = self._extract_number(soup, self.config['selectors']['reviews_count'])
        stock = self._extract_stock(soup, self.config['selectors']['stock'])
        
        # Extract images
        images = self._extract_images(soup, self.config['selectors']['images'])
        
        # Extract additional info
        seller = self._extract_text(soup, self.config['selectors']['seller'])
        shipping = self._extract_text(soup, self.config['selectors']['shipping'])
        description = self._extract_text(soup, self.config['selectors']['description'])
        
        return {
            'marketplace': 'ebay',
            'title': title,
            'price': price,
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'stock': stock,
            'images': images,
            'seller': seller,
            'shipping': shipping,
            'description': description,
            'url': url,
            'parsed_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return None
    
    def _extract_price(self, soup, selector: str) -> Optional[float]:
        """Extract price using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_price(text)
    
    def _extract_rating(self, soup, selector: str) -> Optional[float]:
        """Extract rating using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_rating(text)
    
    def _extract_number(self, soup, selector: str) -> Optional[int]:
        """Extract number using CSS selector"""
        text = self._extract_text(soup, selector)
        if text:
            match = re.search(r'(\d+)', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _extract_stock(self, soup, selector: str) -> Optional[int]:
        """Extract stock using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_stock(text)
    
    def _extract_images(self, soup, selector: str) -> List[str]:
        """Extract image URLs using CSS selector"""
        try:
            elements = soup.select(selector)
            images = []
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []


class LamodaParser(MarketplaceParser):
    """Lamoda specific parser"""
    
    def parse_item(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse Lamoda item page"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic info
        title = self._extract_text(soup, self.config['selectors']['title'])
        price = self._extract_price(soup, self.config['selectors']['price'])
        old_price = self._extract_price(soup, self.config['selectors']['old_price'])
        rating = self._extract_rating(soup, self.config['selectors']['rating'])
        reviews_count = self._extract_number(soup, self.config['selectors']['reviews_count'])
        stock = self._extract_stock(soup, self.config['selectors']['stock'])
        
        # Extract images
        images = self._extract_images(soup, self.config['selectors']['images'])
        
        # Extract additional info
        brand = self._extract_text(soup, self.config['selectors']['brand'])
        category = self._extract_text(soup, self.config['selectors']['category'])
        description = self._extract_text(soup, self.config['selectors']['description'])
        
        return {
            'marketplace': 'lamoda',
            'title': title,
            'price': price,
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'stock': stock,
            'images': images,
            'brand': brand,
            'category': category,
            'description': description,
            'url': url,
            'parsed_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return None
    
    def _extract_price(self, soup, selector: str) -> Optional[float]:
        """Extract price using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_price(text)
    
    def _extract_rating(self, soup, selector: str) -> Optional[float]:
        """Extract rating using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_rating(text)
    
    def _extract_number(self, soup, selector: str) -> Optional[int]:
        """Extract number using CSS selector"""
        text = self._extract_text(soup, selector)
        if text:
            match = re.search(r'(\d+)', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _extract_stock(self, soup, selector: str) -> Optional[int]:
        """Extract stock using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_stock(text)
    
    def _extract_images(self, soup, selector: str) -> List[str]:
        """Extract image URLs using CSS selector"""
        try:
            elements = soup.select(selector)
            images = []
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []


class DNSParser(MarketplaceParser):
    """DNS specific parser"""
    
    def parse_item(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse DNS item page"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic info
        title = self._extract_text(soup, self.config['selectors']['title'])
        price = self._extract_price(soup, self.config['selectors']['price'])
        old_price = self._extract_price(soup, self.config['selectors']['old_price'])
        rating = self._extract_rating(soup, self.config['selectors']['rating'])
        reviews_count = self._extract_number(soup, self.config['selectors']['reviews_count'])
        stock = self._extract_stock(soup, self.config['selectors']['stock'])
        
        # Extract images
        images = self._extract_images(soup, self.config['selectors']['images'])
        
        # Extract additional info
        brand = self._extract_text(soup, self.config['selectors']['brand'])
        category = self._extract_text(soup, self.config['selectors']['category'])
        description = self._extract_text(soup, self.config['selectors']['description'])
        
        return {
            'marketplace': 'dns',
            'title': title,
            'price': price,
            'old_price': old_price,
            'rating': rating,
            'reviews_count': reviews_count,
            'stock': stock,
            'images': images,
            'brand': brand,
            'category': category,
            'description': description,
            'url': url,
            'parsed_at': datetime.utcnow().isoformat()
        }
    
    def _extract_text(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else None
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return None
    
    def _extract_price(self, soup, selector: str) -> Optional[float]:
        """Extract price using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_price(text)
    
    def _extract_rating(self, soup, selector: str) -> Optional[float]:
        """Extract rating using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_rating(text)
    
    def _extract_number(self, soup, selector: str) -> Optional[int]:
        """Extract number using CSS selector"""
        text = self._extract_text(soup, selector)
        if text:
            match = re.search(r'(\d+)', text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
    
    def _extract_stock(self, soup, selector: str) -> Optional[int]:
        """Extract stock using CSS selector"""
        text = self._extract_text(soup, selector)
        return self.clean_stock(text)
    
    def _extract_images(self, soup, selector: str) -> List[str]:
        """Extract image URLs using CSS selector"""
        try:
            elements = soup.select(selector)
            images = []
            for element in elements:
                src = element.get('src') or element.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            return images
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []


def get_parser(marketplace: str, config: Dict[str, Any]) -> MarketplaceParser:
    """Factory function to get appropriate parser for marketplace"""
    parsers = {
        'aliexpress': AliExpressParser,
        'amazon': AmazonParser,
        'ebay': eBayParser,
        'lamoda': LamodaParser,
        'dns': DNSParser,
    }
    
    parser_class = parsers.get(marketplace.lower())
    if not parser_class:
        raise ValueError(f"Unsupported marketplace: {marketplace}")
    
    return parser_class(config)
