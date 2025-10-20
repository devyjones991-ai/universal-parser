"""
Niche Analysis Service for beginners in e-commerce
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum

from app.core.cache import cache_service, cached
from app.services.parsing_service import EnhancedParsingService
from app.services.ai_service import PricePredictionService

logger = logging.getLogger(__name__)


class NicheDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class SupplierType(Enum):
    MANUFACTURER = "manufacturer"
    WHOLESALER = "wholesaler"
    DROPSHIPPER = "dropshipper"
    DISTRIBUTOR = "distributor"


@dataclass
class NicheMetrics:
    """Metrics for niche analysis"""
    competition_level: float  # 0-1, higher = more competitive
    market_size: float  # Estimated market size
    average_price: float  # Average product price
    price_range: Tuple[float, float]  # Min and max prices
    demand_trend: str  # "growing", "stable", "declining"
    seasonality: float  # 0-1, higher = more seasonal
    profit_margin: float  # Average profit margin
    difficulty: NicheDifficulty
    growth_potential: float  # 0-1, growth potential score


@dataclass
class ProductAnalysis:
    """Analysis of a specific product"""
    name: str
    category: str
    average_price: float
    price_range: Tuple[float, float]
    competition_count: int
    demand_score: float
    profit_potential: float
    marketplaces: List[str]
    trends: Dict[str, Any]
    suppliers: List[Dict[str, Any]]


@dataclass
class SupplierInfo:
    """Information about a supplier"""
    name: str
    type: SupplierType
    country: str
    min_order_quantity: int
    price_per_unit: float
    shipping_cost: float
    delivery_time_days: int
    quality_rating: float
    reliability_score: float
    contact_info: Dict[str, str]


@dataclass
class PricingRecommendation:
    """Pricing recommendation for a product"""
    product_name: str
    recommended_price: float
    min_price: float
    max_price: float
    competitor_analysis: Dict[str, float]
    profit_margin: float
    market_position: str  # "budget", "mid-range", "premium"
    pricing_strategy: str


class NicheAnalysisService:
    """Service for analyzing e-commerce niches and providing recommendations"""
    
    def __init__(self):
        self.parsing_service = EnhancedParsingService()
        self.ai_service = PricePredictionService()
        
        # Popular niches for analysis
        self.popular_niches = [
            "electronics", "fashion", "home_garden", "beauty_health",
            "sports_outdoors", "toys_games", "automotive", "books_media",
            "food_beverages", "jewelry_watches", "pet_supplies", "office_supplies"
        ]
        
        # Supplier databases (in real app, this would be from external APIs)
        self.supplier_database = self._initialize_supplier_database()
    
    def _initialize_supplier_database(self) -> Dict[str, List[SupplierInfo]]:
        """Initialize supplier database with sample data"""
        return {
            "electronics": [
                SupplierInfo(
                    name="TechGlobal Manufacturing",
                    type=SupplierType.MANUFACTURER,
                    country="China",
                    min_order_quantity=100,
                    price_per_unit=25.0,
                    shipping_cost=5.0,
                    delivery_time_days=14,
                    quality_rating=4.2,
                    reliability_score=0.85,
                    contact_info={"email": "sales@techglobal.com", "phone": "+86-123-456-7890"}
                ),
                SupplierInfo(
                    name="ElectroWholesale",
                    type=SupplierType.WHOLESALER,
                    country="USA",
                    min_order_quantity=50,
                    price_per_unit=35.0,
                    shipping_cost=8.0,
                    delivery_time_days=7,
                    quality_rating=4.0,
                    reliability_score=0.90,
                    contact_info={"email": "orders@electro.com", "phone": "+1-555-0123"}
                )
            ],
            "fashion": [
                SupplierInfo(
                    name="Fashion Forward Ltd",
                    type=SupplierType.MANUFACTURER,
                    country="Bangladesh",
                    min_order_quantity=200,
                    price_per_unit=12.0,
                    shipping_cost=3.0,
                    delivery_time_days=21,
                    quality_rating=4.1,
                    reliability_score=0.80,
                    contact_info={"email": "info@fashionforward.com", "phone": "+880-123-456-789"}
                )
            ]
        }
    
    @cached(expire=3600)  # Cache for 1 hour
    async def analyze_niche(self, niche: str, keywords: List[str]) -> NicheMetrics:
        """Analyze a specific niche for e-commerce opportunities"""
        try:
            # Search for products in the niche across marketplaces
            search_results = await self._search_niche_products(niche, keywords)
            
            if not search_results:
                return self._create_empty_metrics()
            
            # Calculate niche metrics
            prices = [item.get('price', 0) for item in search_results if item.get('price')]
            competition_count = len(search_results)
            
            # Competition level (based on number of products and price variance)
            competition_level = min(competition_count / 1000, 1.0)  # Normalize to 0-1
            
            # Market size estimation (based on search results and average prices)
            market_size = len(search_results) * np.mean(prices) if prices else 0
            
            # Price analysis
            average_price = np.mean(prices) if prices else 0
            price_range = (min(prices), max(prices)) if prices else (0, 0)
            
            # Demand trend analysis (simplified)
            demand_trend = self._analyze_demand_trend(search_results)
            
            # Seasonality analysis
            seasonality = self._analyze_seasonality(niche)
            
            # Profit margin estimation
            profit_margin = self._estimate_profit_margin(niche, average_price)
            
            # Difficulty assessment
            difficulty = self._assess_difficulty(competition_level, profit_margin, seasonality)
            
            # Growth potential
            growth_potential = self._calculate_growth_potential(niche, demand_trend, competition_level)
            
            return NicheMetrics(
                competition_level=competition_level,
                market_size=market_size,
                average_price=average_price,
                price_range=price_range,
                demand_trend=demand_trend,
                seasonality=seasonality,
                profit_margin=profit_margin,
                difficulty=difficulty,
                growth_potential=growth_potential
            )
            
        except Exception as e:
            logger.error(f"Error analyzing niche {niche}: {e}")
            return self._create_empty_metrics()
    
    async def _search_niche_products(self, niche: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search for products in a specific niche"""
        all_results = []
        
        # Search across different marketplaces
        marketplaces = ["wildberries", "ozon", "aliexpress", "amazon"]
        
        for marketplace in marketplaces:
            try:
                for keyword in keywords:
                    # Simulate search results (in real app, this would call parsing service)
                    results = await self._simulate_search(marketplace, keyword, niche)
                    all_results.extend(results)
            except Exception as e:
                logger.warning(f"Error searching {marketplace} for {keyword}: {e}")
                continue
        
        return all_results
    
    async def _simulate_search(self, marketplace: str, keyword: str, niche: str) -> List[Dict[str, Any]]:
        """Simulate search results (replace with real API calls)"""
        # This is a simulation - in real app, you'd call the parsing service
        import random
        
        results = []
        for i in range(random.randint(5, 20)):
            base_price = random.uniform(10, 500)
            results.append({
                "name": f"{keyword} {niche} product {i+1}",
                "price": base_price * random.uniform(0.8, 1.2),
                "marketplace": marketplace,
                "category": niche,
                "rating": random.uniform(3.0, 5.0),
                "reviews_count": random.randint(10, 1000),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return results
    
    def _analyze_demand_trend(self, products: List[Dict[str, Any]]) -> str:
        """Analyze demand trend based on product data"""
        # Simplified trend analysis
        if len(products) > 50:
            return "growing"
        elif len(products) > 20:
            return "stable"
        else:
            return "declining"
    
    def _analyze_seasonality(self, niche: str) -> float:
        """Analyze seasonality of a niche"""
        seasonal_niches = {
            "fashion": 0.8,
            "home_garden": 0.7,
            "sports_outdoors": 0.6,
            "beauty_health": 0.3,
            "electronics": 0.2,
            "books_media": 0.1
        }
        return seasonal_niches.get(niche, 0.4)
    
    def _estimate_profit_margin(self, niche: str, average_price: float) -> float:
        """Estimate average profit margin for a niche"""
        # Simplified margin estimation based on niche and price
        base_margins = {
            "electronics": 0.15,
            "fashion": 0.40,
            "beauty_health": 0.50,
            "home_garden": 0.35,
            "sports_outdoors": 0.30,
            "toys_games": 0.45
        }
        
        base_margin = base_margins.get(niche, 0.25)
        
        # Adjust based on price (higher prices often have lower margins)
        if average_price > 200:
            base_margin *= 0.8
        elif average_price < 50:
            base_margin *= 1.2
        
        return min(base_margin, 0.8)  # Cap at 80%
    
    def _assess_difficulty(self, competition: float, profit_margin: float, seasonality: float) -> NicheDifficulty:
        """Assess difficulty level of entering a niche"""
        score = (competition * 0.4) + ((1 - profit_margin) * 0.3) + (seasonality * 0.3)
        
        if score < 0.3:
            return NicheDifficulty.EASY
        elif score < 0.5:
            return NicheDifficulty.MEDIUM
        elif score < 0.7:
            return NicheDifficulty.HARD
        else:
            return NicheDifficulty.EXPERT
    
    def _calculate_growth_potential(self, niche: str, demand_trend: str, competition: float) -> float:
        """Calculate growth potential for a niche"""
        growth_scores = {
            "growing": 0.8,
            "stable": 0.5,
            "declining": 0.2
        }
        
        base_growth = growth_scores.get(demand_trend, 0.5)
        
        # Adjust based on competition (less competition = more growth potential)
        competition_factor = 1 - (competition * 0.5)
        
        return min(base_growth * competition_factor, 1.0)
    
    def _create_empty_metrics(self) -> NicheMetrics:
        """Create empty metrics when no data is available"""
        return NicheMetrics(
            competition_level=0.0,
            market_size=0.0,
            average_price=0.0,
            price_range=(0.0, 0.0),
            demand_trend="unknown",
            seasonality=0.0,
            profit_margin=0.0,
            difficulty=NicheDifficulty.EXPERT,
            growth_potential=0.0
        )
    
    async def find_suppliers(self, product_name: str, category: str, budget: float) -> List[SupplierInfo]:
        """Find suppliers for a specific product"""
        try:
            # Get suppliers from database
            suppliers = self.supplier_database.get(category, [])
            
            # Filter suppliers based on budget and requirements
            suitable_suppliers = []
            for supplier in suppliers:
                total_cost = supplier.price_per_unit + supplier.shipping_cost
                if total_cost <= budget * 1.2:  # Allow 20% buffer
                    suitable_suppliers.append(supplier)
            
            # Sort by quality rating and reliability
            suitable_suppliers.sort(
                key=lambda x: (x.quality_rating * x.reliability_score), 
                reverse=True
            )
            
            return suitable_suppliers[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error finding suppliers for {product_name}: {e}")
            return []
    
    async def calculate_pricing(self, product_name: str, category: str, 
                              supplier_cost: float, target_margin: float) -> PricingRecommendation:
        """Calculate optimal pricing for a product"""
        try:
            # Get market data for the product
            market_data = await self._get_market_data(product_name, category)
            
            if not market_data:
                return self._create_default_pricing(product_name, supplier_cost, target_margin)
            
            # Analyze competitor prices
            competitor_prices = [item['price'] for item in market_data if item.get('price')]
            
            if not competitor_prices:
                return self._create_default_pricing(product_name, supplier_cost, target_margin)
            
            # Calculate recommended pricing
            avg_competitor_price = np.mean(competitor_prices)
            min_competitor_price = min(competitor_prices)
            max_competitor_price = max(competitor_prices)
            
            # Calculate target price based on margin
            target_price = supplier_cost / (1 - target_margin)
            
            # Adjust based on market position
            if target_price < min_competitor_price * 0.8:
                recommended_price = min_competitor_price * 0.9
                market_position = "budget"
            elif target_price > max_competitor_price * 1.2:
                recommended_price = max_competitor_price * 1.1
                market_position = "premium"
            else:
                recommended_price = target_price
                market_position = "mid-range"
            
            # Calculate actual profit margin
            actual_margin = (recommended_price - supplier_cost) / recommended_price
            
            # Determine pricing strategy
            if market_position == "budget":
                strategy = "Penetration pricing - compete on price"
            elif market_position == "premium":
                strategy = "Premium pricing - compete on quality/features"
            else:
                strategy = "Competitive pricing - match market rates"
            
            return PricingRecommendation(
                product_name=product_name,
                recommended_price=round(recommended_price, 2),
                min_price=round(min_competitor_price * 0.8, 2),
                max_price=round(max_competitor_price * 1.2, 2),
                competitor_analysis={
                    "average": round(avg_competitor_price, 2),
                    "min": round(min_competitor_price, 2),
                    "max": round(max_competitor_price, 2)
                },
                profit_margin=round(actual_margin, 3),
                market_position=market_position,
                pricing_strategy=strategy
            )
            
        except Exception as e:
            logger.error(f"Error calculating pricing for {product_name}: {e}")
            return self._create_default_pricing(product_name, supplier_cost, target_margin)
    
    async def _get_market_data(self, product_name: str, category: str) -> List[Dict[str, Any]]:
        """Get market data for pricing analysis"""
        # This would typically search across marketplaces
        # For now, return simulated data
        return await self._simulate_search("wildberries", product_name, category)
    
    def _create_default_pricing(self, product_name: str, supplier_cost: float, target_margin: float) -> PricingRecommendation:
        """Create default pricing when no market data is available"""
        recommended_price = supplier_cost / (1 - target_margin)
        
        return PricingRecommendation(
            product_name=product_name,
            recommended_price=round(recommended_price, 2),
            min_price=round(recommended_price * 0.8, 2),
            max_price=round(recommended_price * 1.5, 2),
            competitor_analysis={},
            profit_margin=target_margin,
            market_position="unknown",
            pricing_strategy="Cost-plus pricing - no market data available"
        )
    
    async def get_beginner_recommendations(self, budget: float, experience_level: str) -> Dict[str, Any]:
        """Get personalized recommendations for beginners"""
        try:
            # Filter niches based on experience level
            if experience_level == "complete_beginner":
                recommended_niches = ["fashion", "beauty_health", "home_garden"]
            elif experience_level == "some_experience":
                recommended_niches = ["electronics", "sports_outdoors", "toys_games"]
            else:
                recommended_niches = self.popular_niches
            
            # Analyze each recommended niche
            niche_analyses = {}
            for niche in recommended_niches:
                keywords = self._get_niche_keywords(niche)
                analysis = await self.analyze_niche(niche, keywords)
                niche_analyses[niche] = analysis
            
            # Sort by growth potential and difficulty
            sorted_niches = sorted(
                niche_analyses.items(),
                key=lambda x: (x[1].growth_potential, -x[1].competition_level),
                reverse=True
            )
            
            # Get top 3 recommendations
            top_recommendations = []
            for niche, metrics in sorted_niches[:3]:
                # Get sample products for this niche
                keywords = self._get_niche_keywords(niche)
                products = await self._search_niche_products(niche, keywords[:3])
                
                # Get suppliers
                suppliers = await self.find_suppliers(
                    f"{niche} product", niche, budget
                )
                
                top_recommendations.append({
                    "niche": niche,
                    "metrics": metrics,
                    "sample_products": products[:5],
                    "suppliers": suppliers[:3],
                    "difficulty": metrics.difficulty.value,
                    "growth_potential": metrics.growth_potential,
                    "profit_margin": metrics.profit_margin
                })
            
            return {
                "budget": budget,
                "experience_level": experience_level,
                "recommendations": top_recommendations,
                "general_tips": self._get_beginner_tips(experience_level),
                "next_steps": self._get_next_steps(experience_level)
            }
            
        except Exception as e:
            logger.error(f"Error getting beginner recommendations: {e}")
            return {"error": str(e)}
    
    def _get_niche_keywords(self, niche: str) -> List[str]:
        """Get relevant keywords for a niche"""
        keywords_map = {
            "electronics": ["smartphone", "headphones", "laptop", "tablet", "camera"],
            "fashion": ["dress", "shirt", "jeans", "shoes", "jacket"],
            "beauty_health": ["skincare", "makeup", "vitamins", "supplements", "cosmetics"],
            "home_garden": ["decor", "furniture", "plants", "kitchen", "bathroom"],
            "sports_outdoors": ["fitness", "running", "yoga", "camping", "hiking"],
            "toys_games": ["toys", "games", "puzzles", "educational", "collectibles"]
        }
        return keywords_map.get(niche, [niche])
    
    def _get_beginner_tips(self, experience_level: str) -> List[str]:
        """Get tips for beginners based on experience level"""
        tips = {
            "complete_beginner": [
                "Начните с малого - выберите 1-2 товара для тестирования",
                "Изучите конкурентов и их цены перед запуском",
                "Найдите надежного поставщика с хорошими отзывами",
                "Рассчитайте все расходы: закупка, доставка, комиссии маркетплейсов",
                "Начните с одного маркетплейса, не распыляйтесь"
            ],
            "some_experience": [
                "Анализируйте тренды и сезонность товаров",
                "Используйте AI-прогнозы для планирования закупок",
                "Тестируйте разные ценовые стратегии",
                "Автоматизируйте процессы мониторинга цен",
                "Развивайте бренд и лояльность клиентов"
            ]
        }
        return tips.get(experience_level, tips["complete_beginner"])
    
    def _get_next_steps(self, experience_level: str) -> List[str]:
        """Get next steps for beginners"""
        steps = {
            "complete_beginner": [
                "Выберите нишу из рекомендаций",
                "Найдите 3-5 товаров для анализа",
                "Сравните цены на разных маркетплейсах",
                "Найдите поставщиков и рассчитайте себестоимость",
                "Создайте тестовый заказ"
            ],
            "some_experience": [
                "Проанализируйте выбранную нишу с помощью AI",
                "Настройте мониторинг цен конкурентов",
                "Создайте стратегию ценообразования",
                "Настройте автоматические уведомления",
                "Планируйте масштабирование бизнеса"
            ]
        }
        return steps.get(experience_level, steps["complete_beginner"])


