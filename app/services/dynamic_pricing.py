"""
Dynamic pricing service for automated price optimization
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

from app.core.cache import cache_service, cached
from app.services.parsing_service import EnhancedParsingService
from app.services.trend_detector import TrendDetectorService

logger = logging.getLogger(__name__)


class PricingStrategy(Enum):
    COMPETITIVE = "competitive"
    PREMIUM = "premium"
    PENETRATION = "penetration"
    SKIMMING = "skimming"
    DYNAMIC = "dynamic"
    BALANCED = "balanced"


class PriceChangeReason(Enum):
    COMPETITOR_PRICE_CHANGE = "competitor_price_change"
    DEMAND_INCREASE = "demand_increase"
    DEMAND_DECREASE = "demand_decrease"
    INVENTORY_LOW = "inventory_low"
    INVENTORY_HIGH = "inventory_high"
    SEASONAL_ADJUSTMENT = "seasonal_adjustment"
    TREND_ALIGNMENT = "trend_alignment"


@dataclass
class PricingOpportunity:
    """Pricing opportunity for an item"""
    item_id: str
    current_price: float
    recommended_price: float
    price_change: float
    price_change_percent: float
    reason: PriceChangeReason
    confidence: float
    expected_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    strategy: PricingStrategy
    valid_until: datetime


@dataclass
class CompetitorAnalysis:
    """Analysis of competitor pricing"""
    item_id: str
    marketplace: str
    competitor_count: int
    min_competitor_price: float
    max_competitor_price: float
    avg_competitor_price: float
    median_competitor_price: float
    price_volatility: float
    market_position: str
    price_gaps: List[Dict[str, Any]]


@dataclass
class PriceOptimizationResult:
    """Result of price optimization"""
    item_id: str
    original_price: float
    optimized_price: float
    price_change: float
    price_change_percent: float
    strategy_used: PricingStrategy
    confidence: float
    expected_revenue_change: float
    expected_profit_change: float
    expected_demand_change: float
    risk_score: float
    recommendations: List[str]
    competitor_analysis: Optional[CompetitorAnalysis] = None


class DynamicPricingService:
    """Service for dynamic pricing optimization"""
    
    def __init__(self):
        self.parsing_service = EnhancedParsingService()
        self.trend_service = TrendDetectorService()
        
        # ML models
        self.demand_model = None
        self.price_elasticity_model = None
        self.competitor_model = None
        self.scaler = StandardScaler()
        
        # Pricing rules and constraints
        self.min_margin = 0.15  # 15% minimum margin
        self.max_price_change = 0.3  # 30% maximum price change
        self.price_change_cooldown = 24  # 24 hours between changes
        
        # Historical pricing data cache
        self.pricing_history = {}
        
    async def analyze_pricing_opportunities(self, item_ids: List[str]) -> List[PricingOpportunity]:
        """Analyze pricing opportunities for specific items"""
        try:
            logger.info(f"Analyzing pricing opportunities for {len(item_ids)} items")
            
            opportunities = []
            
            for item_id in item_ids:
                try:
                    opportunity = await self._analyze_item_pricing(item_id)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    logger.warning(f"Error analyzing pricing for item {item_id}: {e}")
                    continue
            
            # Sort by confidence and potential impact
            opportunities.sort(key=lambda x: x.confidence * abs(x.price_change_percent), reverse=True)
            
            logger.info(f"Found {len(opportunities)} pricing opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error analyzing pricing opportunities: {e}")
            return []
    
    async def _analyze_item_pricing(self, item_id: str) -> Optional[PricingOpportunity]:
        """Analyze pricing for a single item"""
        try:
            # Get current item data
            item_data = await self._get_item_data(item_id)
            if not item_data:
                return None
            
            # Get competitor analysis
            competitor_analysis = await self._analyze_competitors(item_id, item_data)
            
            # Get demand analysis
            demand_analysis = await self._analyze_demand(item_id, item_data)
            
            # Get trend analysis
            trend_analysis = await self._analyze_trends(item_id, item_data)
            
            # Calculate recommended price
            recommended_price, reason, confidence = await self._calculate_optimal_price(
                item_data, competitor_analysis, demand_analysis, trend_analysis
            )
            
            if not recommended_price or recommended_price == item_data["current_price"]:
                return None
            
            # Calculate price change
            price_change = recommended_price - item_data["current_price"]
            price_change_percent = price_change / item_data["current_price"]
            
            # Check if change is significant enough
            if abs(price_change_percent) < 0.02:  # Less than 2% change
                return None
            
            # Check constraints
            if not self._validate_price_change(item_data, recommended_price):
                return None
            
            # Calculate expected impact
            expected_impact = await self._calculate_expected_impact(
                item_data, recommended_price, demand_analysis
            )
            
            # Assess risks
            risk_assessment = await self._assess_pricing_risks(
                item_data, recommended_price, competitor_analysis
            )
            
            # Determine strategy
            strategy = self._determine_pricing_strategy(
                item_data, competitor_analysis, demand_analysis
            )
            
            return PricingOpportunity(
                item_id=item_id,
                current_price=item_data["current_price"],
                recommended_price=recommended_price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                reason=reason,
                confidence=confidence,
                expected_impact=expected_impact,
                risk_assessment=risk_assessment,
                strategy=strategy,
                valid_until=datetime.now() + timedelta(hours=24)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing item pricing for {item_id}: {e}")
            return None
    
    async def _get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get current item data"""
        try:
            # In a real implementation, this would query the database
            # For now, generate mock data
            mock_data = {
                "item_id": item_id,
                "current_price": np.random.uniform(50, 500),
                "cost": np.random.uniform(20, 200),
                "marketplace": np.random.choice(["wildberries", "ozon", "aliexpress", "amazon"]),
                "category": np.random.choice(["electronics", "fashion", "beauty_health", "home_garden"]),
                "inventory": np.random.randint(0, 100),
                "sales_velocity": np.random.uniform(0.1, 5.0),
                "rating": np.random.uniform(3.0, 5.0),
                "review_count": np.random.randint(10, 1000),
                "last_price_change": datetime.now() - timedelta(days=np.random.randint(1, 30))
            }
            
            return mock_data
            
        except Exception as e:
            logger.error(f"Error getting item data for {item_id}: {e}")
            return None
    
    async def _analyze_competitors(self, item_id: str, item_data: Dict[str, Any]) -> CompetitorAnalysis:
        """Analyze competitor pricing"""
        try:
            # Generate mock competitor data
            competitor_count = np.random.randint(5, 50)
            base_price = item_data["current_price"]
            
            # Generate competitor prices around the base price
            competitor_prices = []
            for _ in range(competitor_count):
                # Competitor prices with some variation
                variation = np.random.normal(0, 0.2)  # 20% standard deviation
                competitor_price = base_price * (1 + variation)
                competitor_prices.append(max(competitor_price, 1))  # Ensure positive
            
            competitor_prices = np.array(competitor_prices)
            
            # Calculate statistics
            min_price = np.min(competitor_prices)
            max_price = np.max(competitor_prices)
            avg_price = np.mean(competitor_prices)
            median_price = np.median(competitor_prices)
            volatility = np.std(competitor_prices) / avg_price if avg_price > 0 else 0
            
            # Determine market position
            current_price = item_data["current_price"]
            if current_price < min_price * 1.1:
                market_position = "budget"
            elif current_price > max_price * 0.9:
                market_position = "premium"
            else:
                market_position = "mid-range"
            
            # Find price gaps
            price_gaps = []
            sorted_prices = np.sort(competitor_prices)
            for i in range(len(sorted_prices) - 1):
                gap = sorted_prices[i + 1] - sorted_prices[i]
                if gap > avg_price * 0.1:  # Significant gap
                    price_gaps.append({
                        "lower_price": sorted_prices[i],
                        "upper_price": sorted_prices[i + 1],
                        "gap_size": gap,
                        "gap_percent": gap / sorted_prices[i]
                    })
            
            return CompetitorAnalysis(
                item_id=item_id,
                marketplace=item_data["marketplace"],
                competitor_count=competitor_count,
                min_competitor_price=min_price,
                max_competitor_price=max_price,
                avg_competitor_price=avg_price,
                median_competitor_price=median_price,
                price_volatility=volatility,
                market_position=market_position,
                price_gaps=price_gaps
            )
            
        except Exception as e:
            logger.error(f"Error analyzing competitors for {item_id}: {e}")
            # Return default analysis
            return CompetitorAnalysis(
                item_id=item_id,
                marketplace=item_data["marketplace"],
                competitor_count=0,
                min_competitor_price=0,
                max_competitor_price=0,
                avg_competitor_price=0,
                median_competitor_price=0,
                price_volatility=0,
                market_position="unknown",
                price_gaps=[]
            )
    
    async def _analyze_demand(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze demand patterns for the item"""
        try:
            # Generate mock demand analysis
            base_demand = item_data["sales_velocity"]
            
            # Add seasonal factors
            month = datetime.now().month
            seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * month / 12)
            
            # Add trend factors
            trend_factor = np.random.uniform(0.8, 1.2)
            
            # Add price sensitivity
            price_elasticity = np.random.uniform(-1.5, -0.5)  # Negative elasticity
            
            # Calculate demand metrics
            current_demand = base_demand * seasonal_factor * trend_factor
            demand_trend = "increasing" if trend_factor > 1.05 else "decreasing" if trend_factor < 0.95 else "stable"
            
            # Calculate price sensitivity
            price_sensitivity = abs(price_elasticity)
            
            return {
                "current_demand": current_demand,
                "demand_trend": demand_trend,
                "price_elasticity": price_elasticity,
                "price_sensitivity": price_sensitivity,
                "seasonal_factor": seasonal_factor,
                "trend_factor": trend_factor,
                "demand_volatility": np.random.uniform(0.1, 0.3)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing demand for {item_id}: {e}")
            return {
                "current_demand": 1.0,
                "demand_trend": "stable",
                "price_elasticity": -1.0,
                "price_sensitivity": 1.0,
                "seasonal_factor": 1.0,
                "trend_factor": 1.0,
                "demand_volatility": 0.2
            }
    
    async def _analyze_trends(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market trends for the item"""
        try:
            # Get trend data from trend detector
            trends = await self.trend_service.detect_trends(
                marketplaces=[item_data["marketplace"]],
                categories=[item_data["category"]],
                time_window_hours=24
            )
            
            # Analyze trends relevant to this item
            relevant_trends = [t for t in trends if item_id in t.affected_items]
            
            # Calculate trend impact
            trend_impact = 0
            trend_direction = "neutral"
            
            for trend in relevant_trends:
                if trend.trend_type.value in ["price_spike", "price_drop"]:
                    trend_impact += trend.impact_score
                    if trend.trend_type.value == "price_spike":
                        trend_direction = "upward"
                    elif trend.trend_type.value == "price_drop":
                        trend_direction = "downward"
            
            return {
                "trend_impact": trend_impact,
                "trend_direction": trend_direction,
                "relevant_trends": len(relevant_trends),
                "trend_confidence": np.mean([t.confidence for t in relevant_trends]) if relevant_trends else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends for {item_id}: {e}")
            return {
                "trend_impact": 0,
                "trend_direction": "neutral",
                "relevant_trends": 0,
                "trend_confidence": 0.5
            }
    
    async def _calculate_optimal_price(self, 
                                     item_data: Dict[str, Any],
                                     competitor_analysis: CompetitorAnalysis,
                                     demand_analysis: Dict[str, Any],
                                     trend_analysis: Dict[str, Any]) -> Tuple[Optional[float], PriceChangeReason, float]:
        """Calculate optimal price for the item"""
        try:
            current_price = item_data["current_price"]
            cost = item_data["cost"]
            
            # Calculate base optimal price using different strategies
            strategies = {}
            
            # 1. Competitive pricing
            if competitor_analysis.competitor_count > 0:
                competitive_price = competitor_analysis.avg_competitor_price
                strategies["competitive"] = competitive_price
            
            # 2. Cost-plus pricing
            target_margin = 0.3  # 30% margin
            cost_plus_price = cost / (1 - target_margin)
            strategies["cost_plus"] = cost_plus_price
            
            # 3. Demand-based pricing
            if demand_analysis["price_elasticity"] != 0:
                # Simple demand-based pricing
                elasticity = demand_analysis["price_elasticity"]
                optimal_demand_price = current_price * (1 + 1 / abs(elasticity))
                strategies["demand_based"] = optimal_demand_price
            
            # 4. Trend-based pricing
            if trend_analysis["trend_direction"] == "upward":
                trend_price = current_price * 1.05  # 5% increase
                strategies["trend_up"] = trend_price
            elif trend_analysis["trend_direction"] == "downward":
                trend_price = current_price * 0.95  # 5% decrease
                strategies["trend_down"] = trend_price
            
            # Select best strategy based on confidence and constraints
            best_price = None
            best_reason = PriceChangeReason.COMPETITOR_PRICE_CHANGE
            best_confidence = 0.5
            
            for strategy_name, price in strategies.items():
                if price <= 0:
                    continue
                
                # Check constraints
                if not self._validate_price_constraints(item_data, price):
                    continue
                
                # Calculate confidence for this strategy
                confidence = self._calculate_strategy_confidence(
                    strategy_name, price, item_data, competitor_analysis, demand_analysis, trend_analysis
                )
                
                if confidence > best_confidence:
                    best_price = price
                    best_confidence = confidence
                    best_reason = self._get_reason_for_strategy(strategy_name)
            
            return best_price, best_reason, best_confidence
            
        except Exception as e:
            logger.error(f"Error calculating optimal price: {e}")
            return None, PriceChangeReason.COMPETITOR_PRICE_CHANGE, 0.0
    
    def _validate_price_change(self, item_data: Dict[str, Any], new_price: float) -> bool:
        """Validate if price change is allowed"""
        try:
            current_price = item_data["current_price"]
            cost = item_data["cost"]
            
            # Check minimum margin
            if new_price <= cost * (1 + self.min_margin):
                return False
            
            # Check maximum price change
            price_change_percent = abs(new_price - current_price) / current_price
            if price_change_percent > self.max_price_change:
                return False
            
            # Check cooldown period
            last_change = item_data.get("last_price_change")
            if last_change:
                hours_since_change = (datetime.now() - last_change).total_seconds() / 3600
                if hours_since_change < self.price_change_cooldown:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating price change: {e}")
            return False
    
    def _validate_price_constraints(self, item_data: Dict[str, Any], price: float) -> bool:
        """Validate price against basic constraints"""
        try:
            cost = item_data["cost"]
            
            # Must be above cost
            if price <= cost:
                return False
            
            # Must have minimum margin
            if price <= cost * (1 + self.min_margin):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating price constraints: {e}")
            return False
    
    def _calculate_strategy_confidence(self, 
                                     strategy_name: str,
                                     price: float,
                                     item_data: Dict[str, Any],
                                     competitor_analysis: CompetitorAnalysis,
                                     demand_analysis: Dict[str, Any],
                                     trend_analysis: Dict[str, Any]) -> float:
        """Calculate confidence for a pricing strategy"""
        try:
            confidence = 0.5  # Base confidence
            
            if strategy_name == "competitive":
                # Higher confidence if we have good competitor data
                if competitor_analysis.competitor_count >= 10:
                    confidence += 0.3
                if competitor_analysis.price_volatility < 0.2:
                    confidence += 0.2
                    
            elif strategy_name == "cost_plus":
                # Higher confidence if margins are reasonable
                margin = (price - item_data["cost"]) / price
                if 0.2 <= margin <= 0.5:
                    confidence += 0.3
                    
            elif strategy_name in ["demand_based"]:
                # Higher confidence if we have good demand data
                if demand_analysis["price_sensitivity"] > 0.5:
                    confidence += 0.2
                if demand_analysis["demand_trend"] != "stable":
                    confidence += 0.1
                    
            elif strategy_name in ["trend_up", "trend_down"]:
                # Higher confidence if trend is strong
                if trend_analysis["trend_confidence"] > 0.7:
                    confidence += 0.2
                if trend_analysis["trend_impact"] > 0.5:
                    confidence += 0.1
            
            return max(0, min(1, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating strategy confidence: {e}")
            return 0.5
    
    def _get_reason_for_strategy(self, strategy_name: str) -> PriceChangeReason:
        """Get reason code for pricing strategy"""
        strategy_reasons = {
            "competitive": PriceChangeReason.COMPETITOR_PRICE_CHANGE,
            "cost_plus": PriceChangeReason.DEMAND_INCREASE,
            "demand_based": PriceChangeReason.DEMAND_INCREASE,
            "trend_up": PriceChangeReason.TREND_ALIGNMENT,
            "trend_down": PriceChangeReason.TREND_ALIGNMENT
        }
        return strategy_reasons.get(strategy_name, PriceChangeReason.COMPETITOR_PRICE_CHANGE)
    
    async def _calculate_expected_impact(self, 
                                       item_data: Dict[str, Any],
                                       new_price: float,
                                       demand_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate expected impact of price change"""
        try:
            current_price = item_data["current_price"]
            current_demand = demand_analysis["current_demand"]
            price_elasticity = demand_analysis["price_elasticity"]
            
            # Calculate expected demand change
            price_change_percent = (new_price - current_price) / current_price
            demand_change_percent = price_elasticity * price_change_percent
            expected_demand = current_demand * (1 + demand_change_percent)
            
            # Calculate revenue change
            current_revenue = current_price * current_demand
            expected_revenue = new_price * expected_demand
            revenue_change = expected_revenue - current_revenue
            revenue_change_percent = revenue_change / current_revenue if current_revenue > 0 else 0
            
            # Calculate profit change
            cost = item_data["cost"]
            current_profit = (current_price - cost) * current_demand
            expected_profit = (new_price - cost) * expected_demand
            profit_change = expected_profit - current_profit
            profit_change_percent = profit_change / current_profit if current_profit > 0 else 0
            
            return {
                "expected_demand": expected_demand,
                "demand_change_percent": demand_change_percent,
                "expected_revenue": expected_revenue,
                "revenue_change": revenue_change,
                "revenue_change_percent": revenue_change_percent,
                "expected_profit": expected_profit,
                "profit_change": profit_change,
                "profit_change_percent": profit_change_percent
            }
            
        except Exception as e:
            logger.error(f"Error calculating expected impact: {e}")
            return {
                "expected_demand": current_demand,
                "demand_change_percent": 0,
                "expected_revenue": current_price * current_demand,
                "revenue_change": 0,
                "revenue_change_percent": 0,
                "expected_profit": (current_price - item_data["cost"]) * current_demand,
                "profit_change": 0,
                "profit_change_percent": 0
            }
    
    async def _assess_pricing_risks(self, 
                                  item_data: Dict[str, Any],
                                  new_price: float,
                                  competitor_analysis: CompetitorAnalysis) -> Dict[str, Any]:
        """Assess risks of price change"""
        try:
            risks = []
            risk_score = 0.0
            
            current_price = item_data["current_price"]
            price_change_percent = (new_price - current_price) / current_price
            
            # Risk: Price too high compared to competitors
            if competitor_analysis.competitor_count > 0:
                if new_price > competitor_analysis.max_competitor_price * 1.1:
                    risks.append("Price significantly higher than competitors")
                    risk_score += 0.3
                elif new_price < competitor_analysis.min_competitor_price * 0.9:
                    risks.append("Price significantly lower than competitors")
                    risk_score += 0.2
            
            # Risk: Large price change
            if abs(price_change_percent) > 0.2:
                risks.append("Large price change may confuse customers")
                risk_score += 0.2
            
            # Risk: Low inventory
            if item_data["inventory"] < 10:
                risks.append("Low inventory may limit demand response")
                risk_score += 0.1
            
            # Risk: Low rating
            if item_data["rating"] < 4.0:
                risks.append("Low rating may reduce price sensitivity")
                risk_score += 0.1
            
            return {
                "risk_score": min(risk_score, 1.0),
                "risks": risks,
                "risk_level": "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error assessing pricing risks: {e}")
            return {
                "risk_score": 0.5,
                "risks": ["Unable to assess risks"],
                "risk_level": "medium"
            }
    
    def _determine_pricing_strategy(self, 
                                  item_data: Dict[str, Any],
                                  competitor_analysis: CompetitorAnalysis,
                                  demand_analysis: Dict[str, Any]) -> PricingStrategy:
        """Determine the best pricing strategy"""
        try:
            # Analyze market conditions
            is_high_competition = competitor_analysis.competitor_count > 20
            is_high_demand = demand_analysis["current_demand"] > 2.0
            is_price_sensitive = demand_analysis["price_sensitivity"] > 1.0
            
            # Determine strategy based on conditions
            if is_high_competition and is_price_sensitive:
                return PricingStrategy.COMPETITIVE
            elif not is_high_competition and not is_price_sensitive:
                return PricingStrategy.PREMIUM
            elif is_high_demand and not is_high_competition:
                return PricingStrategy.SKIMMING
            elif not is_high_demand and is_high_competition:
                return PricingStrategy.PENETRATION
            else:
                return PricingStrategy.BALANCED
                
        except Exception as e:
            logger.error(f"Error determining pricing strategy: {e}")
            return PricingStrategy.BALANCED
    
    async def optimize_pricing(self, 
                             item_ids: List[str], 
                             strategy: str = "balanced") -> List[PriceOptimizationResult]:
        """Optimize pricing for specific items using a strategy"""
        try:
            logger.info(f"Optimizing pricing for {len(item_ids)} items with strategy: {strategy}")
            
            results = []
            
            for item_id in item_ids:
                try:
                    result = await self._optimize_item_pricing(item_id, strategy)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error optimizing pricing for item {item_id}: {e}")
                    continue
            
            # Sort by expected profit change
            results.sort(key=lambda x: x.expected_profit_change, reverse=True)
            
            logger.info(f"Optimized pricing for {len(results)} items")
            return results
            
        except Exception as e:
            logger.error(f"Error optimizing pricing: {e}")
            return []
    
    async def _optimize_item_pricing(self, item_id: str, strategy: str) -> Optional[PriceOptimizationResult]:
        """Optimize pricing for a single item"""
        try:
            # Get item data
            item_data = await self._get_item_data(item_id)
            if not item_data:
                return None
            
            # Get analyses
            competitor_analysis = await self._analyze_competitors(item_id, item_data)
            demand_analysis = await self._analyze_demand(item_id, item_data)
            trend_analysis = await self._analyze_trends(item_id, item_data)
            
            # Calculate optimized price based on strategy
            optimized_price = await self._calculate_strategy_price(
                item_data, competitor_analysis, demand_analysis, trend_analysis, strategy
            )
            
            if not optimized_price:
                return None
            
            # Calculate metrics
            original_price = item_data["current_price"]
            price_change = optimized_price - original_price
            price_change_percent = price_change / original_price
            
            # Calculate expected impact
            expected_impact = await self._calculate_expected_impact(
                item_data, optimized_price, demand_analysis
            )
            
            # Assess risks
            risk_assessment = await self._assess_pricing_risks(
                item_data, optimized_price, competitor_analysis
            )
            
            # Generate recommendations
            recommendations = self._generate_pricing_recommendations(
                item_data, optimized_price, competitor_analysis, demand_analysis
            )
            
            return PriceOptimizationResult(
                item_id=item_id,
                original_price=original_price,
                optimized_price=optimized_price,
                price_change=price_change,
                price_change_percent=price_change_percent,
                strategy_used=PricingStrategy(strategy),
                confidence=0.8,  # Would be calculated based on data quality
                expected_revenue_change=expected_impact["revenue_change"],
                expected_profit_change=expected_impact["profit_change"],
                expected_demand_change=expected_impact["demand_change_percent"],
                risk_score=risk_assessment["risk_score"],
                recommendations=recommendations,
                competitor_analysis=competitor_analysis
            )
            
        except Exception as e:
            logger.error(f"Error optimizing item pricing for {item_id}: {e}")
            return None
    
    async def _calculate_strategy_price(self, 
                                      item_data: Dict[str, Any],
                                      competitor_analysis: CompetitorAnalysis,
                                      demand_analysis: Dict[str, Any],
                                      trend_analysis: Dict[str, Any],
                                      strategy: str) -> Optional[float]:
        """Calculate price based on specific strategy"""
        try:
            current_price = item_data["current_price"]
            cost = item_data["cost"]
            
            if strategy == "competitive":
                if competitor_analysis.competitor_count > 0:
                    return competitor_analysis.avg_competitor_price
                return None
                
            elif strategy == "premium":
                if competitor_analysis.competitor_count > 0:
                    return competitor_analysis.max_competitor_price * 1.1
                return current_price * 1.2
                
            elif strategy == "penetration":
                if competitor_analysis.competitor_count > 0:
                    return competitor_analysis.min_competitor_price * 0.9
                return current_price * 0.9
                
            elif strategy == "skimming":
                return current_price * 1.15
                
            elif strategy == "dynamic":
                # Use ML model if available
                if self.demand_model:
                    features = self._extract_pricing_features(
                        item_data, competitor_analysis, demand_analysis, trend_analysis
                    )
                    return self.demand_model.predict([features])[0]
                return None
                
            elif strategy == "balanced":
                # Weighted combination of strategies
                prices = []
                weights = []
                
                # Competitive price
                if competitor_analysis.competitor_count > 0:
                    prices.append(competitor_analysis.avg_competitor_price)
                    weights.append(0.4)
                
                # Cost-plus price
                cost_plus_price = cost / 0.7  # 30% margin
                prices.append(cost_plus_price)
                weights.append(0.3)
                
                # Demand-based price
                if demand_analysis["price_elasticity"] != 0:
                    demand_price = current_price * (1 + 1 / abs(demand_analysis["price_elasticity"]))
                    prices.append(demand_price)
                    weights.append(0.3)
                
                if prices:
                    # Weighted average
                    weighted_price = sum(p * w for p, w in zip(prices, weights)) / sum(weights)
                    return weighted_price
                
            return None
            
        except Exception as e:
            logger.error(f"Error calculating strategy price: {e}")
            return None
    
    def _extract_pricing_features(self, 
                                item_data: Dict[str, Any],
                                competitor_analysis: CompetitorAnalysis,
                                demand_analysis: Dict[str, Any],
                                trend_analysis: Dict[str, Any]) -> List[float]:
        """Extract features for ML pricing model"""
        features = []
        
        # Item features
        features.extend([
            item_data["current_price"],
            item_data["cost"],
            item_data["inventory"],
            item_data["sales_velocity"],
            item_data["rating"],
            item_data["review_count"]
        ])
        
        # Competitor features
        features.extend([
            competitor_analysis.competitor_count,
            competitor_analysis.avg_competitor_price,
            competitor_analysis.price_volatility,
            1 if competitor_analysis.market_position == "premium" else 0,
            1 if competitor_analysis.market_position == "budget" else 0
        ])
        
        # Demand features
        features.extend([
            demand_analysis["current_demand"],
            demand_analysis["price_elasticity"],
            demand_analysis["price_sensitivity"],
            1 if demand_analysis["demand_trend"] == "increasing" else 0,
            1 if demand_analysis["demand_trend"] == "decreasing" else 0
        ])
        
        # Trend features
        features.extend([
            trend_analysis["trend_impact"],
            trend_analysis["trend_confidence"],
            1 if trend_analysis["trend_direction"] == "upward" else 0,
            1 if trend_analysis["trend_direction"] == "downward" else 0
        ])
        
        return features
    
    def _generate_pricing_recommendations(self, 
                                        item_data: Dict[str, Any],
                                        optimized_price: float,
                                        competitor_analysis: CompetitorAnalysis,
                                        demand_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for pricing optimization"""
        recommendations = []
        
        # Price positioning recommendations
        if optimized_price > competitor_analysis.avg_competitor_price * 1.1:
            recommendations.append("Consider premium positioning with enhanced marketing")
        elif optimized_price < competitor_analysis.avg_competitor_price * 0.9:
            recommendations.append("Monitor for potential price wars with competitors")
        
        # Demand-based recommendations
        if demand_analysis["price_sensitivity"] > 1.0:
            recommendations.append("High price sensitivity - monitor demand response closely")
        
        if demand_analysis["demand_trend"] == "increasing":
            recommendations.append("Rising demand - consider gradual price increases")
        elif demand_analysis["demand_trend"] == "decreasing":
            recommendations.append("Falling demand - focus on value proposition")
        
        # Inventory recommendations
        if item_data["inventory"] < 20:
            recommendations.append("Low inventory - consider supply chain optimization")
        
        # Rating recommendations
        if item_data["rating"] < 4.0:
            recommendations.append("Low rating - improve product quality before price increases")
        
        return recommendations
    
    async def train_pricing_models(self, training_data: Optional[List[Dict[str, Any]]] = None):
        """Train ML models for pricing optimization"""
        try:
            logger.info("Training pricing models...")
            
            if not training_data:
                training_data = await self._generate_pricing_training_data()
            
            # Prepare features and targets
            X = []
            y = []
            
            for data in training_data:
                features = self._extract_pricing_features(
                    data["item_data"],
                    data["competitor_analysis"],
                    data["demand_analysis"],
                    data["trend_analysis"]
                )
                X.append(features)
                y.append(data["optimal_price"])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train demand model
            self.demand_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.demand_model.fit(X_scaled, y)
            
            logger.info("Pricing models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training pricing models: {e}")
    
    async def _generate_pricing_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for pricing models"""
        training_data = []
        
        # Generate mock training data
        for _ in range(1000):
            # Generate item data
            item_data = {
                "current_price": np.random.uniform(50, 500),
                "cost": np.random.uniform(20, 200),
                "inventory": np.random.randint(0, 100),
                "sales_velocity": np.random.uniform(0.1, 5.0),
                "rating": np.random.uniform(3.0, 5.0),
                "review_count": np.random.randint(10, 1000)
            }
            
            # Generate competitor analysis
            competitor_count = np.random.randint(5, 50)
            avg_price = item_data["current_price"] * np.random.uniform(0.8, 1.2)
            competitor_analysis = CompetitorAnalysis(
                item_id="training_item",
                marketplace="training",
                competitor_count=competitor_count,
                min_competitor_price=avg_price * 0.7,
                max_competitor_price=avg_price * 1.3,
                avg_competitor_price=avg_price,
                median_competitor_price=avg_price,
                price_volatility=np.random.uniform(0.1, 0.5),
                market_position=np.random.choice(["budget", "mid-range", "premium"]),
                price_gaps=[]
            )
            
            # Generate demand analysis
            demand_analysis = {
                "current_demand": np.random.uniform(0.5, 3.0),
                "demand_trend": np.random.choice(["increasing", "stable", "decreasing"]),
                "price_elasticity": np.random.uniform(-2.0, -0.5),
                "price_sensitivity": np.random.uniform(0.5, 2.0),
                "seasonal_factor": np.random.uniform(0.8, 1.2),
                "trend_factor": np.random.uniform(0.9, 1.1),
                "demand_volatility": np.random.uniform(0.1, 0.3)
            }
            
            # Generate trend analysis
            trend_analysis = {
                "trend_impact": np.random.uniform(0, 1),
                "trend_direction": np.random.choice(["upward", "downward", "neutral"]),
                "relevant_trends": np.random.randint(0, 5),
                "trend_confidence": np.random.uniform(0.3, 1.0)
            }
            
            # Calculate optimal price (simplified)
            optimal_price = avg_price * np.random.uniform(0.9, 1.1)
            
            training_data.append({
                "item_data": item_data,
                "competitor_analysis": competitor_analysis,
                "demand_analysis": demand_analysis,
                "trend_analysis": trend_analysis,
                "optimal_price": optimal_price
            })
        
        return training_data
