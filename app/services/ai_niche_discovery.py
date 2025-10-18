"""
AI-powered niche discovery service for automated market analysis
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score

from app.core.cache import cache_service, cached
from app.services.niche_analysis_service import NicheAnalysisService
from app.services.parsing_service import EnhancedParsingService

logger = logging.getLogger(__name__)


class NicheTrend(Enum):
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class NicheOpportunity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class NicheDiscoveryResult:
    """Result of AI niche discovery analysis"""
    niche: str
    keywords: List[str]
    opportunity_score: float
    trend: NicheTrend
    competition_level: float
    market_size: float
    growth_potential: float
    seasonality: float
    profit_margin: float
    entry_difficulty: float
    confidence: float
    recommendations: List[str]
    risks: List[str]
    market_data: Dict[str, Any]


@dataclass
class TrendPattern:
    """Detected trend pattern in niche data"""
    pattern_type: str
    strength: float
    duration_days: int
    confidence: float
    description: str


class AINicheDiscoveryService:
    """AI-powered service for automated niche discovery and analysis"""
    
    def __init__(self):
        self.niche_service = NicheAnalysisService()
        self.parsing_service = EnhancedParsingService()
        
        # ML models
        self.trend_model = None
        self.opportunity_model = None
        self.seasonality_model = None
        self.scaler = StandardScaler()
        
        # Historical data cache
        self.historical_data = {}
        
        # Popular keywords for each niche
        self.niche_keywords = {
            "electronics": ["smartphone", "headphones", "laptop", "tablet", "camera", "smartwatch", "gaming", "audio"],
            "fashion": ["dress", "shirt", "jeans", "shoes", "jacket", "accessories", "handbag", "jewelry"],
            "beauty_health": ["skincare", "makeup", "vitamins", "supplements", "cosmetics", "perfume", "hair", "fitness"],
            "home_garden": ["decor", "furniture", "plants", "kitchen", "bathroom", "lighting", "storage", "cleaning"],
            "sports_outdoors": ["fitness", "running", "yoga", "camping", "hiking", "cycling", "swimming", "gym"],
            "toys_games": ["toys", "games", "puzzles", "educational", "collectibles", "board", "video", "dolls"],
            "automotive": ["car", "accessories", "parts", "tools", "cleaning", "maintenance", "electronics", "safety"],
            "books_media": ["books", "ebooks", "movies", "music", "magazines", "audiobooks", "comics", "educational"],
            "food_beverages": ["snacks", "drinks", "coffee", "tea", "supplements", "organic", "gourmet", "baking"],
            "jewelry_watches": ["rings", "necklaces", "bracelets", "watches", "earrings", "pendants", "chains", "luxury"],
            "pet_supplies": ["dog", "cat", "food", "toys", "accessories", "health", "grooming", "training"],
            "office_supplies": ["stationery", "paper", "pens", "notebooks", "organizers", "technology", "furniture", "supplies"]
        }
    
    async def discover_niches(self, 
                            max_niches: int = 10,
                            min_opportunity_score: float = 0.6,
                            include_trends: bool = True) -> List[NicheDiscoveryResult]:
        """Discover promising niches using AI analysis"""
        try:
            logger.info(f"Starting AI niche discovery for {max_niches} niches")
            
            # Get all available niches
            all_niches = list(self.niche_keywords.keys())
            
            # Analyze each niche
            niche_results = []
            for niche in all_niches:
                try:
                    result = await self._analyze_niche_with_ai(niche, include_trends)
                    if result and result.opportunity_score >= min_opportunity_score:
                        niche_results.append(result)
                except Exception as e:
                    logger.warning(f"Error analyzing niche {niche}: {e}")
                    continue
            
            # Sort by opportunity score
            niche_results.sort(key=lambda x: x.opportunity_score, reverse=True)
            
            # Return top niches
            return niche_results[:max_niches]
            
        except Exception as e:
            logger.error(f"Error in niche discovery: {e}")
            return []
    
    async def _analyze_niche_with_ai(self, niche: str, include_trends: bool) -> Optional[NicheDiscoveryResult]:
        """Analyze a single niche using AI methods"""
        try:
            # Get keywords for niche
            keywords = self.niche_keywords.get(niche, [])
            if not keywords:
                return None
            
            # Get historical data
            historical_data = await self._get_historical_data(niche, keywords)
            
            # Analyze trends
            trend_analysis = None
            if include_trends:
                trend_analysis = await self._analyze_trends(historical_data)
            
            # Calculate opportunity score
            opportunity_score = await self._calculate_opportunity_score(niche, historical_data, trend_analysis)
            
            # Get basic niche metrics
            niche_metrics = await self.niche_service.analyze_niche(niche, keywords)
            
            # Generate recommendations and risks
            recommendations, risks = await self._generate_recommendations_and_risks(
                niche, opportunity_score, niche_metrics, trend_analysis
            )
            
            # Determine trend direction
            trend = NicheTrend.STABLE
            if trend_analysis:
                if trend_analysis.pattern_type == "rising":
                    trend = NicheTrend.RISING
                elif trend_analysis.pattern_type == "declining":
                    trend = NicheTrend.DECLINING
                elif trend_analysis.pattern_type == "volatile":
                    trend = NicheTrend.VOLATILE
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(historical_data, trend_analysis)
            
            return NicheDiscoveryResult(
                niche=niche,
                keywords=keywords,
                opportunity_score=opportunity_score,
                trend=trend,
                competition_level=niche_metrics.competition_level,
                market_size=niche_metrics.market_size,
                growth_potential=niche_metrics.growth_potential,
                seasonality=niche_metrics.seasonality,
                profit_margin=niche_metrics.profit_margin,
                entry_difficulty=1.0 - opportunity_score,  # Inverse of opportunity
                confidence=confidence,
                recommendations=recommendations,
                risks=risks,
                market_data=historical_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing niche {niche}: {e}")
            return None
    
    async def _get_historical_data(self, niche: str, keywords: List[str]) -> Dict[str, Any]:
        """Get historical data for niche analysis"""
        cache_key = f"niche_historical_data:{niche}"
        
        # Check cache first
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return cached_data
        
        # Generate mock historical data (in real app, this would come from database)
        historical_data = await self._generate_mock_historical_data(niche, keywords)
        
        # Cache for 1 hour
        await cache_service.set(cache_key, historical_data, expire=3600)
        
        return historical_data
    
    async def _generate_mock_historical_data(self, niche: str, keywords: List[str]) -> Dict[str, Any]:
        """Generate mock historical data for analysis"""
        # Generate 90 days of data
        dates = pd.date_range(start=datetime.now() - timedelta(days=90), end=datetime.now(), freq='D')
        
        # Base metrics for different niches
        niche_bases = {
            "electronics": {"base_price": 200, "volatility": 0.1, "trend": 0.02},
            "fashion": {"base_price": 80, "volatility": 0.15, "trend": 0.01},
            "beauty_health": {"base_price": 50, "volatility": 0.08, "trend": 0.03},
            "home_garden": {"base_price": 120, "volatility": 0.12, "trend": 0.015},
            "sports_outdoors": {"base_price": 100, "volatility": 0.18, "trend": 0.025},
            "toys_games": {"base_price": 60, "volatility": 0.2, "trend": 0.01},
            "automotive": {"base_price": 150, "volatility": 0.1, "trend": 0.005},
            "books_media": {"base_price": 30, "volatility": 0.05, "trend": 0.001},
            "food_beverages": {"base_price": 25, "volatility": 0.08, "trend": 0.02},
            "jewelry_watches": {"base_price": 300, "volatility": 0.12, "trend": 0.01},
            "pet_supplies": {"base_price": 40, "volatility": 0.06, "trend": 0.02},
            "office_supplies": {"base_price": 35, "volatility": 0.04, "trend": 0.005}
        }
        
        base = niche_bases.get(niche, {"base_price": 100, "volatility": 0.1, "trend": 0.01})
        
        # Generate price data with trend and seasonality
        prices = []
        search_volumes = []
        competition_scores = []
        
        for i, date in enumerate(dates):
            # Base price with trend
            base_price = base["base_price"] * (1 + base["trend"] * i)
            
            # Add seasonality (weekly and monthly patterns)
            weekly_pattern = np.sin(2 * np.pi * i / 7) * 0.05
            monthly_pattern = np.sin(2 * np.pi * i / 30) * 0.1
            
            # Add random volatility
            volatility = np.random.normal(0, base["volatility"])
            
            # Calculate final price
            price = base_price * (1 + weekly_pattern + monthly_pattern + volatility)
            prices.append(max(price, 1))  # Ensure positive prices
            
            # Generate search volume (higher on weekends)
            search_volume = 1000 + 500 * np.sin(2 * np.pi * i / 7) + np.random.normal(0, 200)
            search_volumes.append(max(search_volume, 100))
            
            # Generate competition score (inverse of opportunity)
            competition = 0.3 + 0.4 * np.sin(2 * np.pi * i / 14) + np.random.normal(0, 0.1)
            competition_scores.append(max(0, min(1, competition)))
        
        return {
            "dates": [d.isoformat() for d in dates],
            "prices": prices,
            "search_volumes": search_volumes,
            "competition_scores": competition_scores,
            "keywords": keywords,
            "niche": niche
        }
    
    async def _analyze_trends(self, historical_data: Dict[str, Any]) -> Optional[TrendPattern]:
        """Analyze trends in historical data"""
        try:
            if not historical_data or "prices" not in historical_data:
                return None
            
            prices = historical_data["prices"]
            dates = historical_data["dates"]
            
            if len(prices) < 7:  # Need at least a week of data
                return None
            
            # Convert to pandas for analysis
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'price': prices
            })
            
            # Calculate trend using linear regression
            from sklearn.linear_model import LinearRegression
            
            X = np.arange(len(df)).reshape(-1, 1)
            y = df['price'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            slope = model.coef_[0]
            r2 = model.score(X, y)
            
            # Determine trend type
            if slope > 0.01 and r2 > 0.3:
                pattern_type = "rising"
                strength = min(abs(slope) / np.mean(y), 1.0)
            elif slope < -0.01 and r2 > 0.3:
                pattern_type = "declining"
                strength = min(abs(slope) / np.mean(y), 1.0)
            elif r2 < 0.1:
                pattern_type = "volatile"
                strength = 1.0 - r2
            else:
                pattern_type = "stable"
                strength = 1.0 - abs(slope) / np.mean(y)
            
            # Calculate confidence
            confidence = min(r2 * 2, 1.0) if pattern_type != "volatile" else 1.0 - r2
            
            return TrendPattern(
                pattern_type=pattern_type,
                strength=strength,
                duration_days=len(df),
                confidence=confidence,
                description=f"{pattern_type.title()} trend with {strength:.1%} strength over {len(df)} days"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return None
    
    async def _calculate_opportunity_score(self, 
                                         niche: str, 
                                         historical_data: Dict[str, Any],
                                         trend_analysis: Optional[TrendPattern]) -> float:
        """Calculate opportunity score using ML"""
        try:
            # Extract features
            features = self._extract_features(niche, historical_data, trend_analysis)
            
            # If we have a trained model, use it
            if self.opportunity_model:
                score = self.opportunity_model.predict([features])[0]
                return max(0, min(1, score))
            
            # Otherwise, use rule-based scoring
            return self._rule_based_opportunity_score(features)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.5  # Default neutral score
    
    def _extract_features(self, 
                         niche: str, 
                         historical_data: Dict[str, Any],
                         trend_analysis: Optional[TrendPattern]) -> List[float]:
        """Extract features for ML model"""
        features = []
        
        # Price features
        if "prices" in historical_data and historical_data["prices"]:
            prices = historical_data["prices"]
            features.extend([
                np.mean(prices),  # Average price
                np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0,  # Price volatility
                (max(prices) - min(prices)) / np.mean(prices) if np.mean(prices) > 0 else 0,  # Price range
                len([p for p in prices if p > np.mean(prices)]) / len(prices)  # Above average ratio
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Search volume features
        if "search_volumes" in historical_data and historical_data["search_volumes"]:
            volumes = historical_data["search_volumes"]
            features.extend([
                np.mean(volumes),  # Average search volume
                np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0,  # Volume volatility
                np.mean(volumes[-7:]) / np.mean(volumes[:7]) if len(volumes) >= 14 else 1,  # Recent vs early trend
            ])
        else:
            features.extend([0, 0, 1])
        
        # Competition features
        if "competition_scores" in historical_data and historical_data["competition_scores"]:
            competition = historical_data["competition_scores"]
            features.extend([
                np.mean(competition),  # Average competition
                1 - np.mean(competition),  # Opportunity (inverse of competition)
                np.std(competition)  # Competition volatility
            ])
        else:
            features.extend([0.5, 0.5, 0])
        
        # Trend features
        if trend_analysis:
            features.extend([
                1 if trend_analysis.pattern_type == "rising" else 0,
                1 if trend_analysis.pattern_type == "declining" else 0,
                1 if trend_analysis.pattern_type == "volatile" else 0,
                trend_analysis.strength,
                trend_analysis.confidence
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # Niche-specific features
        niche_features = {
            "electronics": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "fashion": [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "beauty_health": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "home_garden": [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            "sports_outdoors": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
            "toys_games": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            "automotive": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            "books_media": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "food_beverages": [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "jewelry_watches": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            "pet_supplies": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            "office_supplies": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        }
        
        features.extend(niche_features.get(niche, [0] * 12))
        
        return features
    
    def _rule_based_opportunity_score(self, features: List[float]) -> float:
        """Calculate opportunity score using rules"""
        if len(features) < 20:
            return 0.5
        
        score = 0.5  # Base score
        
        # Price volatility (lower is better for stability)
        price_volatility = features[1]
        if price_volatility < 0.1:
            score += 0.2
        elif price_volatility > 0.3:
            score -= 0.1
        
        # Search volume trend (growing is better)
        volume_trend = features[6]
        if volume_trend > 1.1:
            score += 0.2
        elif volume_trend < 0.9:
            score -= 0.1
        
        # Competition (lower is better)
        competition = features[7]
        if competition < 0.3:
            score += 0.2
        elif competition > 0.7:
            score -= 0.2
        
        # Opportunity (higher is better)
        opportunity = features[8]
        score += opportunity * 0.2
        
        # Trend (rising is better)
        is_rising = features[13]
        if is_rising:
            score += 0.1
        
        # Trend strength
        trend_strength = features[16]
        score += trend_strength * 0.1
        
        return max(0, min(1, score))
    
    def _calculate_confidence(self, 
                            historical_data: Dict[str, Any],
                            trend_analysis: Optional[TrendPattern]) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence
        
        # Data quality factors
        if historical_data and "prices" in historical_data:
            data_points = len(historical_data["prices"])
            if data_points >= 30:
                confidence += 0.2
            elif data_points >= 14:
                confidence += 0.1
            
            # Price stability (less volatile = more confident)
            prices = historical_data["prices"]
            if prices:
                volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 1
                if volatility < 0.2:
                    confidence += 0.1
                elif volatility > 0.5:
                    confidence -= 0.1
        
        # Trend analysis confidence
        if trend_analysis:
            confidence += trend_analysis.confidence * 0.2
        
        return max(0, min(1, confidence))
    
    async def _generate_recommendations_and_risks(self,
                                                niche: str,
                                                opportunity_score: float,
                                                niche_metrics,
                                                trend_analysis: Optional[TrendPattern]) -> Tuple[List[str], List[str]]:
        """Generate recommendations and risks based on analysis"""
        recommendations = []
        risks = []
        
        # Opportunity-based recommendations
        if opportunity_score > 0.8:
            recommendations.append("Excellent opportunity! This niche shows high potential for success.")
            recommendations.append("Consider aggressive market entry with strong branding.")
        elif opportunity_score > 0.6:
            recommendations.append("Good opportunity with moderate risk. Plan carefully and test the market.")
            recommendations.append("Focus on differentiation and unique value proposition.")
        elif opportunity_score > 0.4:
            recommendations.append("Moderate opportunity. Consider if you have specific advantages in this niche.")
            recommendations.append("Start small and scale based on results.")
        else:
            recommendations.append("Low opportunity. Consider other niches unless you have unique advantages.")
            risks.append("High competition and low profit potential.")
        
        # Trend-based recommendations
        if trend_analysis:
            if trend_analysis.pattern_type == "rising":
                recommendations.append("Rising trend detected - good time to enter the market.")
            elif trend_analysis.pattern_type == "declining":
                risks.append("Declining trend - market may be shrinking.")
                recommendations.append("Consider if this is a temporary decline or long-term trend.")
            elif trend_analysis.pattern_type == "volatile":
                risks.append("High volatility - prices and demand may be unpredictable.")
                recommendations.append("Use dynamic pricing strategies to manage volatility.")
        
        # Competition-based recommendations
        if niche_metrics.competition_level < 0.3:
            recommendations.append("Low competition - easier to establish market presence.")
        elif niche_metrics.competition_level > 0.7:
            risks.append("High competition - difficult to stand out.")
            recommendations.append("Focus on niche segments or unique positioning.")
        
        # Profit margin recommendations
        if niche_metrics.profit_margin > 0.4:
            recommendations.append("High profit margins - good for sustainable business.")
        elif niche_metrics.profit_margin < 0.2:
            risks.append("Low profit margins - may be difficult to be profitable.")
            recommendations.append("Focus on cost optimization and volume strategies.")
        
        # Seasonality risks
        if niche_metrics.seasonality > 0.7:
            risks.append("High seasonality - business may be seasonal.")
            recommendations.append("Plan for seasonal variations and consider complementary products.")
        
        return recommendations, risks
    
    async def train_models(self, training_data: Optional[List[Dict[str, Any]]] = None):
        """Train ML models for niche discovery"""
        try:
            logger.info("Training AI niche discovery models...")
            
            # Generate training data if not provided
            if not training_data:
                training_data = await self._generate_training_data()
            
            # Prepare features and targets
            X = []
            y = []
            
            for data in training_data:
                features = self._extract_features(
                    data["niche"], 
                    data["historical_data"], 
                    data.get("trend_analysis")
                )
                X.append(features)
                y.append(data["opportunity_score"])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train opportunity model
            from sklearn.ensemble import RandomForestRegressor
            self.opportunity_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.opportunity_model.fit(X_scaled, y)
            
            logger.info("AI niche discovery models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    async def _generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for model training"""
        training_data = []
        
        for niche in self.niche_keywords.keys():
            keywords = self.niche_keywords[niche]
            historical_data = await self._generate_mock_historical_data(niche, keywords)
            trend_analysis = await self._analyze_trends(historical_data)
            opportunity_score = self._rule_based_opportunity_score(
                self._extract_features(niche, historical_data, trend_analysis)
            )
            
            training_data.append({
                "niche": niche,
                "keywords": keywords,
                "historical_data": historical_data,
                "trend_analysis": trend_analysis,
                "opportunity_score": opportunity_score
            })
        
        return training_data
    
    @cached(expire=3600)  # Cache for 1 hour
    async def get_niche_insights(self, niche: str) -> Dict[str, Any]:
        """Get detailed insights for a specific niche"""
        try:
            keywords = self.niche_keywords.get(niche, [])
            if not keywords:
                return {}
            
            # Get comprehensive analysis
            discovery_result = await self._analyze_niche_with_ai(niche, include_trends=True)
            
            if not discovery_result:
                return {}
            
            # Get additional insights
            insights = {
                "niche": niche,
                "keywords": keywords,
                "opportunity_score": discovery_result.opportunity_score,
                "trend": discovery_result.trend.value,
                "competition_level": discovery_result.competition_level,
                "market_size": discovery_result.market_size,
                "growth_potential": discovery_result.growth_potential,
                "seasonality": discovery_result.seasonality,
                "profit_margin": discovery_result.profit_margin,
                "entry_difficulty": discovery_result.entry_difficulty,
                "confidence": discovery_result.confidence,
                "recommendations": discovery_result.recommendations,
                "risks": discovery_result.risks,
                "market_data": discovery_result.market_data,
                "analysis_date": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting niche insights for {niche}: {e}")
            return {}
