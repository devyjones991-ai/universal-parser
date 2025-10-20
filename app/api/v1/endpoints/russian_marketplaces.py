"""API эндпоинты для российских маркетплейсов"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.russian_marketplace_parsers import RussianMarketplaceService
from app.schemas.parsing import ParsingResponse, ParsingRequest

router = APIRouter()


@router.get("/marketplaces")
async def get_russian_marketplaces():
    """Получить список поддерживаемых российских маркетплейсов"""
    marketplaces = [
        {
            "id": "wildberries",
            "name": "Wildberries",
            "description": "Крупнейший российский маркетплейс",
            "url": "https://www.wildberries.ru",
            "categories": ["electronics", "clothing", "shoes", "home", "beauty", "sports", "auto", "kids", "books", "food"],
            "features": ["api", "filters", "categories", "reviews", "ratings", "stock", "delivery"]
        },
        {
            "id": "ozon",
            "name": "Ozon",
            "description": "Один из крупнейших российских маркетплейсов",
            "url": "https://www.ozon.ru",
            "categories": ["electronics", "clothing", "shoes", "home", "beauty", "sports", "auto", "kids", "books", "food"],
            "features": ["api", "filters", "categories", "reviews", "ratings", "stock", "delivery"]
        },
        {
            "id": "yandex_market",
            "name": "Яндекс.Маркет",
            "description": "Сравнительный сервис товаров",
            "url": "https://market.yandex.ru",
            "categories": ["electronics", "computers", "phones", "home", "clothing", "shoes", "beauty", "sports", "auto", "kids", "books", "food"],
            "features": ["html", "filters", "categories", "reviews", "ratings", "comparison", "delivery"]
        },
        {
            "id": "avito",
            "name": "Avito",
            "description": "Крупнейшая площадка объявлений в России",
            "url": "https://www.avito.ru",
            "categories": ["real_estate", "cars", "electronics", "clothing", "home", "beauty", "sports", "kids", "animals", "services", "work", "business"],
            "features": ["html", "filters", "categories", "location", "seller_info", "views", "date"]
        },
        {
            "id": "mvideo",
            "name": "М.Видео",
            "description": "Сеть магазинов электроники и бытовой техники",
            "url": "https://www.mvideo.ru",
            "categories": ["smartphones", "laptops", "tablets", "tv", "audio", "gaming", "home_appliances", "computers", "accessories", "smart_home"],
            "features": ["api", "filters", "categories", "reviews", "ratings", "stock", "delivery", "pickup"]
        },
        {
            "id": "eldorado",
            "name": "Эльдорадо",
            "description": "Сеть магазинов электроники и бытовой техники",
            "url": "https://www.eldorado.ru",
            "categories": ["smartphones", "laptops", "tablets", "tv", "audio", "gaming", "home_appliances", "computers", "accessories", "smart_home"],
            "features": ["api", "filters", "categories", "reviews", "ratings", "stock", "delivery", "pickup"]
        }
    ]
    
    return {
        "marketplaces": marketplaces,
        "total": len(marketplaces)
    }


@router.get("/{marketplace}/categories")
async def get_marketplace_categories(marketplace: str):
    """Получить категории для конкретного маркетплейса"""
    service = RussianMarketplaceService()
    categories = await service.get_categories(marketplace)
    
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categories not found for marketplace: {marketplace}"
        )
    
    return {
        "marketplace": marketplace,
        "categories": categories
    }


@router.get("/{marketplace}/filters")
async def get_marketplace_filters(marketplace: str):
    """Получить доступные фильтры для маркетплейса"""
    service = RussianMarketplaceService()
    filters = await service.get_filters(marketplace)
    
    if not filters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filters not found for marketplace: {marketplace}"
        )
    
    return {
        "marketplace": marketplace,
        "filters": filters
    }


@router.get("/{marketplace}/search")
async def search_products(
    marketplace: str,
    query: str = Query(..., description="Поисковый запрос"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    price_min: Optional[float] = Query(None, description="Минимальная цена"),
    price_max: Optional[float] = Query(None, description="Максимальная цена"),
    brand: Optional[str] = Query(None, description="Бренд"),
    rating: Optional[float] = Query(None, ge=0, le=5, description="Минимальный рейтинг"),
    discount: Optional[bool] = Query(None, description="Только со скидкой"),
    in_stock: Optional[bool] = Query(None, description="Только в наличии"),
    region: Optional[str] = Query(None, description="Регион (для Avito)"),
    category: Optional[str] = Query(None, description="Категория"),
    condition: Optional[str] = Query(None, description="Состояние (для Avito)"),
    seller_type: Optional[str] = Query(None, description="Тип продавца (для Avito)"),
    with_photo: Optional[bool] = Query(None, description="Только с фото (для Avito)"),
    urgent: Optional[bool] = Query(None, description="Срочно (для Avito)")
):
    """Поиск товаров на российском маркетплейсе"""
    
    # Формируем фильтры
    filters = {}
    if price_min is not None:
        filters["price_min"] = price_min
    if price_max is not None:
        filters["price_max"] = price_max
    if brand:
        filters["brand"] = brand
    if rating is not None:
        filters["rating"] = rating
    if discount is not None:
        filters["discount"] = discount
    if in_stock is not None:
        filters["in_stock"] = in_stock
    if region:
        filters["region"] = region
    if category:
        filters["category"] = category
    if condition:
        filters["condition"] = condition
    if seller_type:
        filters["seller_type"] = seller_type
    if with_photo is not None:
        filters["with_photo"] = with_photo
    if urgent is not None:
        filters["urgent"] = urgent
    
    try:
        service = RussianMarketplaceService()
        products = await service.search_products(marketplace, query, page, filters)
        
        return {
            "marketplace": marketplace,
            "query": query,
            "page": page,
            "filters": filters,
            "products": products,
            "total": len(products)
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/{marketplace}/product/{product_id}")
async def get_product_details(marketplace: str, product_id: str):
    """Получить детальную информацию о товаре"""
    
    try:
        service = RussianMarketplaceService()
        product = await service.get_product_details(marketplace, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found on {marketplace}"
            )
        
        return {
            "marketplace": marketplace,
            "product_id": product_id,
            "product": product
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product details: {str(e)}"
        )


@router.post("/{marketplace}/parse")
async def parse_marketplace(
    marketplace: str,
    request: ParsingRequest,
    db: Session = Depends(get_db)
):
    """Парсинг товаров с российского маркетплейса"""
    
    try:
        service = RussianMarketplaceService()
        
        # Формируем фильтры из запроса
        filters = {}
        if hasattr(request, 'filters') and request.filters:
            filters = request.filters
        
        # Выполняем поиск
        products = await service.search_products(
            marketplace=marketplace,
            query=request.query,
            page=request.page or 1,
            filters=filters
        )
        
        # Обрабатываем результаты
        results = []
        for product in products:
            result = {
                "marketplace": marketplace,
                "query": request.query,
                "product_id": product.get("id", ""),
                "title": product.get("title", ""),
                "price": product.get("price", 0),
                "old_price": product.get("old_price", 0),
                "rating": product.get("rating", 0),
                "reviews_count": product.get("reviews_count", 0),
                "stock": product.get("stock", 0),
                "images": product.get("images", []),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "seller": product.get("seller", ""),
                "discount": product.get("discount", 0),
                "url": product.get("url", ""),
                "parsed_at": "2024-01-15T10:00:00Z"  # В реальном приложении использовать datetime.utcnow()
            }
            results.append(result)
        
        return {
            "marketplace": marketplace,
            "query": request.query,
            "page": request.page or 1,
            "filters": filters,
            "results": results,
            "total": len(results),
            "success": True
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}"
        )


@router.get("/{marketplace}/stats")
async def get_marketplace_stats(marketplace: str):
    """Получить статистику по маркетплейсу"""
    
    # Заглушка для демонстрации
    stats = {
        "wildberries": {
            "total_products": 15000000,
            "categories": 10,
            "avg_price": 2500,
            "popular_brands": ["Apple", "Samsung", "Xiaomi", "Huawei", "Sony"],
            "last_updated": "2024-01-15T10:00:00Z"
        },
        "ozon": {
            "total_products": 8000000,
            "categories": 10,
            "avg_price": 3200,
            "popular_brands": ["Apple", "Samsung", "Xiaomi", "Huawei", "Sony"],
            "last_updated": "2024-01-15T10:00:00Z"
        },
        "yandex_market": {
            "total_products": 5000000,
            "categories": 12,
            "avg_price": 2800,
            "popular_brands": ["Apple", "Samsung", "Xiaomi", "Huawei", "Sony"],
            "last_updated": "2024-01-15T10:00:00Z"
        },
        "avito": {
            "total_products": 20000000,
            "categories": 12,
            "avg_price": 1500,
            "popular_brands": ["Apple", "Samsung", "Xiaomi", "Huawei", "Sony"],
            "last_updated": "2024-01-15T10:00:00Z"
        },
        "mvideo": {
            "total_products": 500000,
            "categories": 10,
            "avg_price": 15000,
            "popular_brands": ["Apple", "Samsung", "Sony", "LG", "Samsung"],
            "last_updated": "2024-01-15T10:00:00Z"
        },
        "eldorado": {
            "total_products": 400000,
            "categories": 10,
            "avg_price": 12000,
            "popular_brands": ["Apple", "Samsung", "Sony", "LG", "Samsung"],
            "last_updated": "2024-01-15T10:00:00Z"
        }
    }
    
    if marketplace not in stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stats not found for marketplace: {marketplace}"
        )
    
    return {
        "marketplace": marketplace,
        "stats": stats[marketplace]
    }


