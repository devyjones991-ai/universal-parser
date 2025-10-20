"""
Real-time trend detection service using machine learning
"""
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
import joblib
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.core.cache import cache_service, cached
from app.services.parsing_service import EnhancedParsingService

logger = logging.getLogger(__name__)

class TrendType(Enum):
    PRICE_SPIKE = "price_spike"
    PRICE_DROP = "price_drop"
    VOLUME_SURGE = "volume_surge"
    COMPETITION_CHANGE = "competition_change"
    SEASONAL_PATTERN = "seasonal_pattern"
    ANOMALY = "anomaly"

class TrendSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TrendAlert:
    """Alert about a detected trend"""
    trend_type: TrendType
    severity: TrendSeverity
    confidence: float
    description: str
    affected_items: List[str]
    affected_marketplaces: List[str]
    detected_at: datetime
    expected_duration: Optional[int]  # days
    impact_score: float
    recommendations: List[str]
    data_points: Dict[str, Any]

@dataclass
class TrendPattern:
    """Detected trend pattern"""
    pattern_id: str
    pattern_type: str
    start_time: datetime
    end_time: Optional[datetime]
    strength: float
    confidence: float
    frequency: float
    description: str
    affected_entities: List[str]

class TrendDetectorService:
    """Service for real-time trend detection and analysis"""

    def __init__(self):
        self.parsing_service = EnhancedParsingService()

        # ML models
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.trend_classifier = None
        self.scaler = StandardScaler()

        # Trend patterns cache
        self.detected_patterns = {}

        # Configuration
        self.min_data_points = 10
        self.trend_threshold = 0.7
        self.anomaly_threshold = 0.8

    async def detect_trends(self, 
                          marketplaces: Optional[List[str]] = None,
                          categories: Optional[List[str]] = None,
                          time_window_hours: int = 24) -> List[TrendAlert]:
        """Detect trends across marketplaces and categories"""
        try:
            logger.info("Starting trend detection for {time_window_hours} hours")

            # Get data for analysis
            data = await self._collect_trend_data(marketplaces, categories, time_window_hours)

            if not data:
                logger.warning("No data available for trend detection")
                return []

            # Detect different types of trends
            trends = []

            # Price trends
            price_trends = await self._detect_price_trends(data)
            trends.extend(price_trends)

            # Volume trends
            volume_trends = await self._detect_volume_trends(data)
            trends.extend(volume_trends)

            # Competition trends
            competition_trends = await self._detect_competition_trends(data)
            trends.extend(competition_trends)

            # Seasonal patterns
            seasonal_trends = await self._detect_seasonal_patterns(data)
            trends.extend(seasonal_trends)

            # Anomalies
            anomaly_trends = await self._detect_anomalies(data)
            trends.extend(anomaly_trends)

            # Sort by impact score
            trends.sort(key=lambda x: x.impact_score, reverse=True)

            logger.info("Detected {len(trends)} trends")
            return trends

        except Exception as e:
            logger.error("Error in trend detection: {e}")
            return []

    async def _collect_trend_data(self, 
                                marketplaces: Optional[List[str]],
                                categories: Optional[List[str]],
                                time_window_hours: int) -> Dict[str, Any]:
        """Collect data for trend analysis"""
        try:
            # In a real implementation, this would query the database
            # For now, we'll generate mock data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_window_hours)

            # Generate mock data
            data = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "marketplaces": marketplaces or ["wildberries", "ozon", "aliexpress", "amazon"],
                "categories": categories or ["electronics", "fashion", "beauty_health"],
                "price_data": await self._generate_mock_price_data(start_time, end_time),
                "volume_data": await self._generate_mock_volume_data(start_time, end_time),
                "competition_data": await self._generate_mock_competition_data(start_time, end_time)
            }

            return data

        except Exception as e:
            logger.error("Error collecting trend data: {e}")
            return {}

    async def _generate_mock_price_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Generate mock price data for trend analysis"""
        data = []
        current_time = start_time

        while current_time < end_time:
            # Generate price data for different items
            for i in range(10):  # 10 items
                item_id = f"item_{i}"
                marketplace = ["wildberries", "ozon", "aliexpress", "amazon"][i % 4]
                category = ["electronics", "fashion", "beauty_health"][i % 3]

                # Base price with some trend
                base_price = 100 + i * 20

                # Add some randomness and trends
                trend_factor = 1 + 0.1 * np.sin(2 * np.pi * (current_time - start_time).total_seconds() / 3600)
                random_factor = 1 + np.random.normal(0, 0.05)

                price = base_price * trend_factor * random_factor

                data.append({
                    "timestamp": current_time.isoformat(),
                    "item_id": item_id,
                    "marketplace": marketplace,
                    "category": category,
                    "price": max(price, 1),  # Ensure positive price
                    "currency": "RUB"
                })

            current_time += timedelta(minutes=30)  # Data every 30 minutes

        return data

    async def _generate_mock_volume_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Generate mock volume data for trend analysis"""
        data = []
        current_time = start_time

        while current_time < end_time:
            for i in range(10):
                item_id = f"item_{i}"
                marketplace = ["wildberries", "ozon", "aliexpress", "amazon"][i % 4]
                category = ["electronics", "fashion", "beauty_health"][i % 3]

                # Base volume with trends
                base_volume = 1000 + i * 100

                # Add daily pattern (higher during day)
                hour = current_time.hour
                daily_factor = 0.5 + 0.5 * np.sin(2 * np.pi * (hour - 6) / 24) if 6 <= hour <= 22 else 0.3

                # Add some randomness
                random_factor = 1 + np.random.normal(0, 0.2)

                volume = base_volume * daily_factor * random_factor

                data.append({
                    "timestamp": current_time.isoformat(),
                    "item_id": item_id,
                    "marketplace": marketplace,
                    "category": category,
                    "search_volume": max(volume, 0),
                    "sales_volume": max(volume * 0.1, 0)  # 10% conversion
                })

            current_time += timedelta(hours=1)  # Data every hour

        return data

    async def _generate_mock_competition_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]  # noqa  # noqa: E501 E501
        """Generate mock competition data for trend analysis"""
        data = []
        current_time = start_time

        while current_time < end_time:
            for i in range(10):
                item_id = f"item_{i}"
                marketplace = ["wildberries", "ozon", "aliexpress", "amazon"][i % 4]
                category = ["electronics", "fashion", "beauty_health"][i % 3]

                # Base competition score
                base_competition = 0.3 + i * 0.05

                # Add some variation
                variation = np.random.normal(0, 0.1)
                competition = max(0, min(1, base_competition + variation))

                data.append({
                    "timestamp": current_time.isoformat(),
                    "item_id": item_id,
                    "marketplace": marketplace,
                    "category": category,
                    "competition_score": competition,
                    "competitor_count": int(50 + competition * 100 + np.random.normal(0, 10))
                })

            current_time += timedelta(hours=2)  # Data every 2 hours

        return data

    async def _detect_price_trends(self, data: Dict[str, Any]) -> List[TrendAlert]  # noqa  # noqa: E501 E501
        """Detect price-related trends"""
        trends = []

        try:
            price_data = data.get("price_data", [])
            if not price_data:
                return trends

            # Group by item and marketplace
            grouped_data = {}
            for item in price_data:
                key = f"{item['item_id']}_{item['marketplace']}"
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(item)

            # Analyze each item
            for key, items in grouped_data.items():
                if len(items) < self.min_data_points:
                    continue

                # Sort by timestamp
                items.sort(key=lambda x: x["timestamp"])

                # Calculate price trend
                prices = [item["price"] for item in items]
                timestamps = [datetime.fromisoformat(item["timestamp"]) for item in items]

                # Detect spikes and drops
                price_changes = np.diff(prices) / prices[:-1]

                # Check for significant changes
                for i, change in enumerate(price_changes):
                    if abs(change) > 0.2:  # 20% change
                        trend_type = TrendType.PRICE_SPIKE if change > 0 else TrendType.PRICE_DROP
                        severity = self._calculate_severity(abs(change))

                        alert = TrendAlert(
                            trend_type=trend_type,
                            severity=severity,
                            confidence=min(abs(change) * 2, 1.0),
                            description=f"Price {'increased' if change > 0 else 'decreased'} by {abs(change)  # noqa  # noqa: E501 E501.1%}",
                            affected_items=[items[i]["item_id"]],
                            affected_marketplaces=[items[i]["marketplace"]],
                            detected_at=timestamps[i + 1],
                            expected_duration=1,  # 1 day
                            impact_score=abs(change),
                            recommendations=self._get_price_trend_recommendations(change),
                            data_points={"price_change": change, "old_price": prices[i], "new_price"  # noqa  # noqa: E501 E501 prices[i + 1]}
                        )

                        trends.append(alert)

        except Exception as e:
            logger.error("Error detecting price trends: {e}")

        return trends

    async def _detect_volume_trends(self, data: Dict[str, Any]) -> List[TrendAlert]  # noqa  # noqa: E501 E501
        """Detect volume-related trends"""
        trends = []

        try:
            volume_data = data.get("volume_data", [])
            if not volume_data:
                return trends

            # Group by item and marketplace
            grouped_data = {}
            for item in volume_data:
                key = f"{item['item_id']}_{item['marketplace']}"
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(item)

            # Analyze each item
            for key, items in grouped_data.items():
                if len(items) < self.min_data_points:
                    continue

                # Sort by timestamp
                items.sort(key=lambda x: x["timestamp"])

                # Calculate volume trend
                volumes = [item["search_volume"] for item in items]
                timestamps = [datetime.fromisoformat(item["timestamp"]) for item in items]

                # Detect volume surges
                volume_changes = np.diff(volumes) / (np.array(volumes[:-1]) + 1)  # Add 1 to avoid division by zero

                for i, change in enumerate(volume_changes):
                    if change > 0.5:  # 50% increase
                        alert = TrendAlert(
                            trend_type=TrendType.VOLUME_SURGE,
                            severity=self._calculate_severity(change),
                            confidence=min(change, 1.0),
                            description=f"Search volume increased by {change:.1%}",
                            affected_items=[items[i]["item_id"]],
                            affected_marketplaces=[items[i]["marketplace"]],
                            detected_at=timestamps[i + 1],
                            expected_duration=2,  # 2 days
                            impact_score=change,
                            recommendations=self._get_volume_trend_recommendations(change),
                            data_points={"volume_change": change, "old_volume": volumes[i], "new_volume"  # noqa  # noqa: E501 E501 volumes[i + 1]}
                        )

                        trends.append(alert)

        except Exception as e:
            logger.error("Error detecting volume trends: {e}")

        return trends

    async def _detect_competition_trends(self, data: Dict[str, Any]) -> List[TrendAlert]  # noqa  # noqa: E501 E501
        """Detect competition-related trends"""
        trends = []

        try:
            competition_data = data.get("competition_data", [])
            if not competition_data:
                return trends

            # Group by category and marketplace
            grouped_data = {}
            for item in competition_data:
                key = f"{item['category']}_{item['marketplace']}"
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(item)

            # Analyze each category
            for key, items in grouped_data.items():
                if len(items) < self.min_data_points:
                    continue

                # Sort by timestamp
                items.sort(key=lambda x: x["timestamp"])

                # Calculate competition trend
                competition_scores = [item["competition_score"] for item in items]
                competitor_counts = [item["competitor_count"] for item in items]
                timestamps = [datetime.fromisoformat(item["timestamp"]) for item in items]

                # Detect significant changes
                competition_changes = np.diff(competition_scores)
                count_changes = np.diff(competitor_counts)

                for i, (comp_change, count_change) in enumerate(zip(competition_changes, count_changes))  # noqa  # noqa: E501 E501
                    if abs(comp_change) > 0.1 or abs(count_change) > 10:  # Significant change
                        alert = TrendAlert(
                            trend_type=TrendType.COMPETITION_CHANGE,
                            severity=self._calculate_severity(abs(comp_change) + abs(count_change) / 100),
                            confidence=min(abs(comp_change) + abs(count_change) / 100, 1.0),
                            description=f"Competition {'increased' if comp_change > 0 else 'decreased'} by {abs(comp_change)  # noqa  # noqa: E501 E501.1%}",
                            affected_items=[items[i]["item_id"]],
                            affected_marketplaces=[items[i]["marketplace"]],
                            detected_at=timestamps[i + 1],
                            expected_duration=7,  # 1 week
                            impact_score=abs(comp_change) + abs(count_change) / 100,
                            recommendations=self._get_competition_trend_recommendations(comp_change),
                            data_points={
                                "competition_change": comp_change,
                                "count_change": count_change,
                                "old_competition": competition_scores[i],
                                "new_competition": competition_scores[i + 1]
                            }
                        )

                        trends.append(alert)

        except Exception as e:
            logger.error("Error detecting competition trends: {e}")

        return trends

    async def _detect_seasonal_patterns(self, data: Dict[str, Any]) -> List[TrendAlert]  # noqa  # noqa: E501 E501
        """Detect seasonal patterns in data"""
        trends = []

        try:
            # This would require longer historical data
            # For now, we'll detect basic patterns in the available data

            price_data = data.get("price_data", [])
            if not price_data:
                return trends

            # Group by category
            category_data = {}
            for item in price_data:
                category = item["category"]
                if category not in category_data:
                    category_data[category] = []
                category_data[category].append(item)

            # Analyze each category for patterns
            for category, items in category_data.items():
                if len(items) < 20:  # Need more data for seasonal analysis
                    continue

                # Sort by timestamp
                items.sort(key=lambda x: x["timestamp"])

                # Extract hourly patterns
                hourly_prices = {}
                for item in items:
                    hour = datetime.fromisoformat(item["timestamp"]).hour
                    if hour not in hourly_prices:
                        hourly_prices[hour] = []
                    hourly_prices[hour].append(item["price"])

                # Calculate average prices by hour
                avg_prices_by_hour = {}
                for hour, prices in hourly_prices.items():
                    avg_prices_by_hour[hour] = np.mean(prices)

                # Detect significant hourly patterns
                if len(avg_prices_by_hour) >= 6:  # At least 6 hours of data
                    hours = sorted(avg_prices_by_hour.keys())
                    prices = [avg_prices_by_hour[h] for h in hours]

                    # Calculate coefficient of variation
                    cv = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0

                    if cv > 0.1:  # Significant variation
                        alert = TrendAlert(
                            trend_type=TrendType.SEASONAL_PATTERN,
                            severity=TrendSeverity.MEDIUM,
                            confidence=min(cv * 2, 1.0),
                            description=f"Detected hourly price pattern in {category}",
                            affected_items=list(set(item["item_id"] for item in items)),
                            affected_marketplaces=list(set(item["marketplace"] for item in items)),
                            detected_at=datetime.now(),
                            expected_duration=None,  # Ongoing pattern
                            impact_score=cv,
                            recommendations=self._get_seasonal_recommendations(category),
                            data_points={"hourly_prices": avg_prices_by_hour, "variation"  # noqa  # noqa: E501 E501 cv}
                        )

                        trends.append(alert)

        except Exception as e:
            logger.error("Error detecting seasonal patterns: {e}")

        return trends

    async def _detect_anomalies(self, data: Dict[str, Any]) -> List[TrendAlert]  # noqa  # noqa: E501 E501
        """Detect anomalies in the data"""
        trends = []

        try:
            # Combine all data for anomaly detection
            all_features = []
            all_items = []

            # Price features
            price_data = data.get("price_data", [])
            for item in price_data:
                features = [
                    item["price"],
                    datetime.fromisoformat(item["timestamp"]).hour,
                    datetime.fromisoformat(item["timestamp"]).weekday()
                ]
                all_features.append(features)
                all_items.append(item)

            if len(all_features) < 10:
                return trends

            # Scale features
            X = self.scaler.fit_transform(all_features)

            # Detect anomalies
            anomaly_scores = self.anomaly_detector.decision_function(X)
            is_anomaly = self.anomaly_detector.predict(X) == -1

            # Create alerts for anomalies
            for i, (is_anom, score) in enumerate(zip(is_anomaly, anomaly_scores))  # noqa  # noqa: E501 E501
                if is_anom and abs(score) > self.anomaly_threshold:
                    item = all_items[i]

                    alert = TrendAlert(
                        trend_type=TrendType.ANOMALY,
                        severity=self._calculate_severity(abs(score)),
                        confidence=min(abs(score), 1.0),
                        description=f"Anomaly detected in {item['category']} data",
                        affected_items=[item["item_id"]],
                        affected_marketplaces=[item["marketplace"]],
                        detected_at=datetime.fromisoformat(item["timestamp"]),
                        expected_duration=1,
                        impact_score=abs(score),
                        recommendations=self._get_anomaly_recommendations(),
                        data_points={"anomaly_score": score, "features": all_features[i]}
                    )

                    trends.append(alert)

        except Exception as e:
            logger.error("Error detecting anomalies: {e}")

        return trends

    def _calculate_severity(self, impact_score: float) -> TrendSeverity:
        """Calculate severity based on impact score"""
        if impact_score >= 0.8:
            return TrendSeverity.CRITICAL
        elif impact_score >= 0.6:
            return TrendSeverity.HIGH
        elif impact_score >= 0.3:
            return TrendSeverity.MEDIUM
        else:
            return TrendSeverity.LOW

    def _get_price_trend_recommendations(self, change: float) -> List[str]:
        """Get recommendations for price trends"""
        if change > 0.2:  # Price spike
            return [
                "Consider increasing your prices to match market trends",
                "Monitor competitor pricing closely",
                "Check if this is a temporary spike or long-term trend"
            ]
        elif change < -0.2:  # Price drop
            return [
                "Consider reducing prices to stay competitive",
                "Look for cost optimization opportunities",
                "Evaluate if this is a market-wide trend"
            ]
        else:
            return [
                "Monitor price changes closely",
                "Consider dynamic pricing strategies"
            ]

    def _get_volume_trend_recommendations(self, change: float) -> List[str]:
        """Get recommendations for volume trends"""
        return [
            "Increase marketing efforts to capitalize on higher demand",
            "Ensure adequate inventory levels",
            "Consider expanding product range in this category",
            "Monitor for potential supply shortages"
        ]

    def _get_competition_trend_recommendations(self, change: float) -> List[str]  # noqa  # noqa: E501 E501
        """Get recommendations for competition trends"""
        if change > 0:  # Increased competition
            return [
                "Focus on differentiation and unique value proposition",
                "Consider niche market segments",
                "Improve product quality and customer service",
                "Monitor competitor strategies closely"
            ]
        else:  # Decreased competition
            return [
                "Consider expanding market presence",
                "Increase marketing investment",
                "Look for new market opportunities"
            ]

    def _get_seasonal_recommendations(self, category: str) -> List[str]:
        """Get recommendations for seasonal patterns"""
        return [
            f"Adjust pricing strategy based on {category} seasonal patterns",
            "Plan inventory levels according to demand cycles",
            "Consider complementary products for off-season periods",
            "Use seasonal patterns for marketing timing"
        ]

    def _get_anomaly_recommendations(self) -> List[str]:
        """Get recommendations for anomalies"""
        return [
            "Investigate the cause of the anomaly",
            "Check data quality and sources",
            "Monitor for similar patterns in the future",
            "Consider if this represents a new trend"
        ]

    @cached(expire=1800)  # Cache for 30 minutes
    async def get_trend_summary(self, 
                              marketplaces: Optional[List[str]] = None,
                              categories: Optional[List[str]] = None,
                              hours: int = 24) -> Dict[str, Any]:
        """Get a summary of recent trends"""
        try:
            trends = await self.detect_trends(marketplaces, categories, hours)

            # Group trends by type
            trends_by_type = {}
            for trend in trends:
                trend_type = trend.trend_type.value
                if trend_type not in trends_by_type:
                    trends_by_type[trend_type] = []
                trends_by_type[trend_type].append(trend)

            # Calculate summary statistics
            summary = {
                "total_trends": len(trends),
                "trends_by_type": {k: len(v) for k, v in trends_by_type.items()},
                "high_impact_trends": len([t for t in trends if t.impact_score > 0.7]),
                "critical_trends": len([t for t in trends if t.severity == TrendSeverity.CRITICAL]),
                "recent_trends": [
                    {
                        "type": trend.trend_type.value,
                        "severity": trend.severity.value,
                        "description": trend.description,
                        "confidence": trend.confidence,
                        "impact_score": trend.impact_score,
                        "detected_at": trend.detected_at.isoformat()
                    }
                    for trend in trends[:10]  # Top 10 trends
                ],
                "analysis_period": {
                    "start": (datetime.now() - timedelta(hours=hours)).isoformat(),
                    "end": datetime.now().isoformat()
                }
            }

            return summary

        except Exception as e:
            logger.error("Error getting trend summary: {e}")
            return {}

    async def train_anomaly_detector(self, training_data: Optional[List[Dict[str, Any]]] = None)  # noqa  # noqa: E501 E501
        """Train the anomaly detection model"""
        try:
            logger.info("Training anomaly detection model...")

            if not training_data:
                # Generate training data
                training_data = await self._generate_training_data()

            # Prepare features
            features = []
            for data_point in training_data:
                feature_vector = [
                    data_point.get("price", 0),
                    data_point.get("volume", 0),
                    data_point.get("competition", 0),
                    data_point.get("hour", 12),
                    data_point.get("weekday", 1)
                ]
                features.append(feature_vector)

            # Scale features
            X = self.scaler.fit_transform(features)

            # Train anomaly detector
            self.anomaly_detector.fit(X)

            logger.info("Anomaly detection model trained successfully")

        except Exception as e:
            logger.error("Error training anomaly detector: {e}")

    async def _generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for anomaly detection"""
        training_data = []

        # Generate normal data
        for _ in range(1000):
            training_data.append({
                "price": np.random.normal(100, 20),
                "volume": np.random.normal(1000, 200),
                "competition": np.random.uniform(0.2, 0.8),
                "hour": np.random.randint(0, 24),
                "weekday": np.random.randint(0, 7)
            })

        # Generate some anomalies
        for _ in range(50):
            training_data.append({
                "price": np.random.normal(500, 100),  # High prices
                "volume": np.random.normal(5000, 1000),  # High volume
                "competition": np.random.uniform(0.9, 1.0),  # High competition
                "hour": np.random.randint(0, 24),
                "weekday": np.random.randint(0, 7)
            })

        return training_data
