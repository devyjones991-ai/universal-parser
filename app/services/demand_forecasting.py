"""
Demand forecasting service using machine learning and time series analysis
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
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

from app.core.cache import cache_service, cached
from app.services.parsing_service import EnhancedParsingService
from app.services.trend_detector import TrendDetectorService

logger = logging.getLogger(__name__)


class ForecastMethod(Enum):
    PROPHET = "prophet"
    ARIMA = "arima"
    LSTM = "lstm"
    RANDOM_FOREST = "random_forest"
    ENSEMBLE = "ensemble"


class SeasonalityType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    MULTIPLE = "multiple"


@dataclass
class ForecastResult:
    """Result of demand forecasting"""
    item_id: str
    forecast_method: ForecastMethod
    forecast_period: int  # days
    predictions: List[Dict[str, Any]]
    confidence_intervals: List[Dict[str, Any]]
    accuracy_metrics: Dict[str, float]
    seasonality_detected: bool
    trend_direction: str
    forecast_quality: float
    recommendations: List[str]


@dataclass
class SeasonalPattern:
    """Detected seasonal pattern"""
    pattern_type: SeasonalityType
    strength: float
    period: int
    amplitude: float
    phase: float
    confidence: float
    description: str


@dataclass
class InventoryRecommendation:
    """Inventory recommendation based on forecast"""
    item_id: str
    current_stock: int
    recommended_stock: int
    stock_change: int
    reorder_point: int
    reorder_quantity: int
    stockout_risk: float
    overstock_risk: float
    recommendation_reason: str


class DemandForecastingService:
    """Service for demand forecasting and inventory optimization"""
    
    def __init__(self):
        self.parsing_service = EnhancedParsingService()
        self.trend_service = TrendDetectorService()
        
        # ML models
        self.demand_models = {}
        self.seasonality_models = {}
        self.scaler = StandardScaler()
        
        # Prophet models for time series
        self.prophet_models = {}
        
        # Historical data cache
        self.historical_data = {}
        
        # Configuration
        self.min_data_points = 30  # Minimum data points for forecasting
        self.forecast_horizon = 30  # Default forecast horizon in days
        self.confidence_level = 0.95  # Confidence level for intervals
        
    async def predict_demand(self, 
                           item_ids: List[str], 
                           days_ahead: int = 30,
                           method: ForecastMethod = ForecastMethod.ENSEMBLE) -> List[ForecastResult]:
        """Predict demand for specific items"""
        try:
            logger.info(f"Predicting demand for {len(item_ids)} items, {days_ahead} days ahead")
            
            results = []
            
            for item_id in item_ids:
                try:
                    result = await self._forecast_item_demand(item_id, days_ahead, method)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error forecasting demand for item {item_id}: {e}")
                    continue
            
            # Sort by forecast quality
            results.sort(key=lambda x: x.forecast_quality, reverse=True)
            
            logger.info(f"Generated forecasts for {len(results)} items")
            return results
            
        except Exception as e:
            logger.error(f"Error predicting demand: {e}")
            return []
    
    async def _forecast_item_demand(self, 
                                  item_id: str, 
                                  days_ahead: int,
                                  method: ForecastMethod) -> Optional[ForecastResult]:
        """Forecast demand for a single item"""
        try:
            # Get historical data
            historical_data = await self._get_historical_demand_data(item_id)
            
            if not historical_data or len(historical_data) < self.min_data_points:
                logger.warning(f"Insufficient data for forecasting item {item_id}")
                return None
            
            # Prepare data for forecasting
            df = self._prepare_forecast_data(historical_data)
            
            # Generate forecast based on method
            if method == ForecastMethod.PROPHET:
                predictions, confidence_intervals = await self._forecast_with_prophet(df, days_ahead)
            elif method == ForecastMethod.RANDOM_FOREST:
                predictions, confidence_intervals = await self._forecast_with_random_forest(df, days_ahead)
            elif method == ForecastMethod.ENSEMBLE:
                predictions, confidence_intervals = await self._forecast_with_ensemble(df, days_ahead)
            else:
                # Default to Prophet
                predictions, confidence_intervals = await self._forecast_with_prophet(df, days_ahead)
            
            # Calculate accuracy metrics
            accuracy_metrics = await self._calculate_accuracy_metrics(historical_data, predictions)
            
            # Detect seasonality
            seasonality_detected, seasonal_patterns = await self._detect_seasonality(df)
            
            # Determine trend direction
            trend_direction = await self._determine_trend_direction(df)
            
            # Calculate forecast quality
            forecast_quality = await self._calculate_forecast_quality(
                accuracy_metrics, seasonality_detected, len(historical_data)
            )
            
            # Generate recommendations
            recommendations = await self._generate_forecast_recommendations(
                item_id, predictions, seasonality_detected, trend_direction
            )
            
            return ForecastResult(
                item_id=item_id,
                forecast_method=method,
                forecast_period=days_ahead,
                predictions=predictions,
                confidence_intervals=confidence_intervals,
                accuracy_metrics=accuracy_metrics,
                seasonality_detected=seasonality_detected,
                trend_direction=trend_direction,
                forecast_quality=forecast_quality,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error forecasting item demand for {item_id}: {e}")
            return None
    
    async def _get_historical_demand_data(self, item_id: str) -> List[Dict[str, Any]]:
        """Get historical demand data for an item"""
        try:
            cache_key = f"demand_data:{item_id}"
            
            # Check cache first
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                return cached_data
            
            # Generate mock historical data (in real app, this would query database)
            historical_data = await self._generate_mock_demand_data(item_id)
            
            # Cache for 1 hour
            await cache_service.set(cache_key, historical_data, expire=3600)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error getting historical demand data for {item_id}: {e}")
            return []
    
    async def _generate_mock_demand_data(self, item_id: str) -> List[Dict[str, Any]]:
        """Generate mock historical demand data"""
        try:
            # Generate 90 days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            data = []
            current_date = start_date
            
            # Base demand with some randomness
            base_demand = np.random.uniform(10, 100)
            
            while current_date <= end_date:
                # Add seasonal patterns
                day_of_week = current_date.weekday()
                day_of_month = current_date.day
                
                # Weekly pattern (higher on weekends)
                weekly_factor = 1.2 if day_of_week >= 5 else 1.0
                
                # Monthly pattern (higher mid-month)
                monthly_factor = 1 + 0.3 * np.sin(2 * np.pi * day_of_month / 30)
                
                # Random variation
                random_factor = np.random.uniform(0.7, 1.3)
                
                # Calculate demand
                demand = base_demand * weekly_factor * monthly_factor * random_factor
                demand = max(0, int(demand))  # Ensure non-negative integer
                
                data.append({
                    "date": current_date.isoformat(),
                    "demand": demand,
                    "price": np.random.uniform(50, 500),
                    "inventory": np.random.randint(0, 100),
                    "rating": np.random.uniform(3.0, 5.0),
                    "competition": np.random.uniform(0.2, 0.8)
                })
                
                current_date += timedelta(days=1)
            
            return data
            
        except Exception as e:
            logger.error(f"Error generating mock demand data: {e}")
            return []
    
    def _prepare_forecast_data(self, historical_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare data for forecasting"""
        try:
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df.sort_index()
            
            # Add additional features
            df['day_of_week'] = df.index.dayofweek
            df['day_of_month'] = df.index.day
            df['month'] = df.index.month
            df['week_of_year'] = df.index.isocalendar().week
            
            # Add lag features
            df['demand_lag_1'] = df['demand'].shift(1)
            df['demand_lag_7'] = df['demand'].shift(7)
            df['demand_lag_30'] = df['demand'].shift(30)
            
            # Add rolling averages
            df['demand_ma_7'] = df['demand'].rolling(window=7).mean()
            df['demand_ma_30'] = df['demand'].rolling(window=30).mean()
            
            # Add trend
            df['trend'] = range(len(df))
            
            return df.dropna()
            
        except Exception as e:
            logger.error(f"Error preparing forecast data: {e}")
            return pd.DataFrame()
    
    async def _forecast_with_prophet(self, df: pd.DataFrame, days_ahead: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Forecast using Prophet"""
        try:
            # Prepare data for Prophet
            prophet_df = df.reset_index()
            prophet_df = prophet_df[['date', 'demand']].rename(columns={'date': 'ds', 'demand': 'y'})
            
            # Create and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                seasonality_mode='multiplicative'
            )
            
            model.fit(prophet_df)
            
            # Make future dataframe
            future = model.make_future_dataframe(periods=days_ahead)
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Extract predictions
            predictions = []
            confidence_intervals = []
            
            for i in range(len(prophet_df), len(forecast)):
                pred_date = forecast.iloc[i]['ds']
                pred_value = forecast.iloc[i]['yhat']
                lower_bound = forecast.iloc[i]['yhat_lower']
                upper_bound = forecast.iloc[i]['yhat_upper']
                
                predictions.append({
                    "date": pred_date.isoformat(),
                    "demand": max(0, int(pred_value)),
                    "method": "prophet"
                })
                
                confidence_intervals.append({
                    "date": pred_date.isoformat(),
                    "lower_bound": max(0, int(lower_bound)),
                    "upper_bound": max(0, int(upper_bound)),
                    "confidence_level": self.confidence_level
                })
            
            return predictions, confidence_intervals
            
        except Exception as e:
            logger.error(f"Error forecasting with Prophet: {e}")
            return [], []
    
    async def _forecast_with_random_forest(self, df: pd.DataFrame, days_ahead: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Forecast using Random Forest"""
        try:
            # Prepare features
            feature_columns = ['day_of_week', 'day_of_month', 'month', 'week_of_year', 
                             'demand_lag_1', 'demand_lag_7', 'demand_lag_30',
                             'demand_ma_7', 'demand_ma_30', 'trend', 'price', 'rating', 'competition']
            
            X = df[feature_columns].values
            y = df['demand'].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            
            # Generate predictions
            predictions = []
            confidence_intervals = []
            
            last_date = df.index[-1]
            
            for i in range(days_ahead):
                pred_date = last_date + timedelta(days=i+1)
                
                # Prepare features for prediction
                pred_features = self._prepare_prediction_features(df, pred_date, i)
                pred_features_scaled = self.scaler.transform([pred_features])
                
                # Make prediction
                pred_value = model.predict(pred_features_scaled)[0]
                pred_value = max(0, int(pred_value))
                
                # Calculate confidence interval (simplified)
                # In practice, you'd use prediction intervals or bootstrap
                std_error = np.std(y) * 0.1  # Simplified error estimation
                lower_bound = max(0, int(pred_value - 1.96 * std_error))
                upper_bound = max(0, int(pred_value + 1.96 * std_error))
                
                predictions.append({
                    "date": pred_date.isoformat(),
                    "demand": pred_value,
                    "method": "random_forest"
                })
                
                confidence_intervals.append({
                    "date": pred_date.isoformat(),
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "confidence_level": self.confidence_level
                })
            
            return predictions, confidence_intervals
            
        except Exception as e:
            logger.error(f"Error forecasting with Random Forest: {e}")
            return [], []
    
    async def _forecast_with_ensemble(self, df: pd.DataFrame, days_ahead: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Forecast using ensemble of methods"""
        try:
            # Get predictions from different methods
            prophet_preds, prophet_intervals = await self._forecast_with_prophet(df, days_ahead)
            rf_preds, rf_intervals = await self._forecast_with_random_forest(df, days_ahead)
            
            # Combine predictions (weighted average)
            predictions = []
            confidence_intervals = []
            
            for i in range(days_ahead):
                if i < len(prophet_preds) and i < len(rf_preds):
                    # Weighted average (Prophet 60%, Random Forest 40%)
                    prophet_demand = prophet_preds[i]['demand']
                    rf_demand = rf_preds[i]['demand']
                    combined_demand = int(0.6 * prophet_demand + 0.4 * rf_demand)
                    
                    # Combined confidence interval
                    prophet_lower = prophet_intervals[i]['lower_bound']
                    prophet_upper = prophet_intervals[i]['upper_bound']
                    rf_lower = rf_intervals[i]['lower_bound']
                    rf_upper = rf_intervals[i]['upper_bound']
                    
                    combined_lower = int(0.6 * prophet_lower + 0.4 * rf_lower)
                    combined_upper = int(0.6 * prophet_upper + 0.4 * rf_upper)
                    
                    predictions.append({
                        "date": prophet_preds[i]['date'],
                        "demand": combined_demand,
                        "method": "ensemble"
                    })
                    
                    confidence_intervals.append({
                        "date": prophet_preds[i]['date'],
                        "lower_bound": combined_lower,
                        "upper_bound": combined_upper,
                        "confidence_level": self.confidence_level
                    })
            
            return predictions, confidence_intervals
            
        except Exception as e:
            logger.error(f"Error forecasting with ensemble: {e}")
            return [], []
    
    def _prepare_prediction_features(self, df: pd.DataFrame, pred_date: datetime, days_ahead: int) -> List[float]:
        """Prepare features for prediction"""
        try:
            features = []
            
            # Date features
            features.extend([
                pred_date.weekday(),
                pred_date.day,
                pred_date.month,
                pred_date.isocalendar().week
            ])
            
            # Lag features (use last available values)
            features.extend([
                df['demand_lag_1'].iloc[-1] if not pd.isna(df['demand_lag_1'].iloc[-1]) else df['demand'].iloc[-1],
                df['demand_lag_7'].iloc[-1] if not pd.isna(df['demand_lag_7'].iloc[-1]) else df['demand'].iloc[-1],
                df['demand_lag_30'].iloc[-1] if not pd.isna(df['demand_lag_30'].iloc[-1]) else df['demand'].iloc[-1]
            ])
            
            # Rolling averages
            features.extend([
                df['demand_ma_7'].iloc[-1] if not pd.isna(df['demand_ma_7'].iloc[-1]) else df['demand'].iloc[-1],
                df['demand_ma_30'].iloc[-1] if not pd.isna(df['demand_ma_30'].iloc[-1]) else df['demand'].iloc[-1]
            ])
            
            # Trend
            features.append(len(df) + days_ahead)
            
            # Other features (use last available values)
            features.extend([
                df['price'].iloc[-1],
                df['rating'].iloc[-1],
                df['competition'].iloc[-1]
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing prediction features: {e}")
            return [0] * 13  # Return zeros for all features
    
    async def _calculate_accuracy_metrics(self, 
                                        historical_data: List[Dict[str, Any]],
                                        predictions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate accuracy metrics for the forecast"""
        try:
            if not predictions:
                return {"mae": 0, "mse": 0, "rmse": 0, "mape": 0}
            
            # Use last 30% of historical data for validation
            validation_size = int(len(historical_data) * 0.3)
            if validation_size < 5:
                return {"mae": 0, "mse": 0, "rmse": 0, "mape": 0}
            
            # Get actual values
            actual_values = [d['demand'] for d in historical_data[-validation_size:]]
            
            # Get predicted values (use first validation_size predictions)
            predicted_values = [p['demand'] for p in predictions[:validation_size]]
            
            if len(actual_values) != len(predicted_values):
                min_len = min(len(actual_values), len(predicted_values))
                actual_values = actual_values[:min_len]
                predicted_values = predicted_values[:min_len]
            
            if not actual_values or not predicted_values:
                return {"mae": 0, "mse": 0, "rmse": 0, "mape": 0}
            
            # Calculate metrics
            actual = np.array(actual_values)
            predicted = np.array(predicted_values)
            
            mae = mean_absolute_error(actual, predicted)
            mse = mean_squared_error(actual, predicted)
            rmse = np.sqrt(mse)
            
            # MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((actual - predicted) / (actual + 1e-8))) * 100
            
            return {
                "mae": float(mae),
                "mse": float(mse),
                "rmse": float(rmse),
                "mape": float(mape)
            }
            
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}")
            return {"mae": 0, "mse": 0, "rmse": 0, "mape": 0}
    
    async def _detect_seasonality(self, df: pd.DataFrame) -> Tuple[bool, List[SeasonalPattern]]:
        """Detect seasonal patterns in the data"""
        try:
            if len(df) < 30:
                return False, []
            
            patterns = []
            seasonality_detected = False
            
            # Check for weekly seasonality
            weekly_strength = self._calculate_seasonality_strength(df, 'day_of_week', 7)
            if weekly_strength > 0.3:
                patterns.append(SeasonalPattern(
                    pattern_type=SeasonalityType.WEEKLY,
                    strength=weekly_strength,
                    period=7,
                    amplitude=weekly_strength * df['demand'].std(),
                    phase=0,
                    confidence=weekly_strength,
                    description=f"Weekly seasonality with {weekly_strength:.1%} strength"
                ))
                seasonality_detected = True
            
            # Check for monthly seasonality
            monthly_strength = self._calculate_seasonality_strength(df, 'day_of_month', 30)
            if monthly_strength > 0.2:
                patterns.append(SeasonalPattern(
                    pattern_type=SeasonalityType.MONTHLY,
                    strength=monthly_strength,
                    period=30,
                    amplitude=monthly_strength * df['demand'].std(),
                    phase=0,
                    confidence=monthly_strength,
                    description=f"Monthly seasonality with {monthly_strength:.1%} strength"
                ))
                seasonality_detected = True
            
            # Check for yearly seasonality
            yearly_strength = self._calculate_seasonality_strength(df, 'month', 12)
            if yearly_strength > 0.2:
                patterns.append(SeasonalPattern(
                    pattern_type=SeasonalityType.YEARLY,
                    strength=yearly_strength,
                    period=365,
                    amplitude=yearly_strength * df['demand'].std(),
                    phase=0,
                    confidence=yearly_strength,
                    description=f"Yearly seasonality with {yearly_strength:.1%} strength"
                ))
                seasonality_detected = True
            
            return seasonality_detected, patterns
            
        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return False, []
    
    def _calculate_seasonality_strength(self, df: pd.DataFrame, column: str, period: int) -> float:
        """Calculate strength of seasonality for a given period"""
        try:
            # Group by the seasonal column and calculate mean demand
            seasonal_means = df.groupby(column)['demand'].mean()
            
            if len(seasonal_means) < 2:
                return 0.0
            
            # Calculate coefficient of variation
            mean_demand = seasonal_means.mean()
            std_demand = seasonal_means.std()
            
            if mean_demand == 0:
                return 0.0
            
            # Normalize by mean to get relative strength
            strength = std_demand / mean_demand
            
            return min(strength, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating seasonality strength: {e}")
            return 0.0
    
    async def _determine_trend_direction(self, df: pd.DataFrame) -> str:
        """Determine trend direction"""
        try:
            if len(df) < 7:
                return "unknown"
            
            # Calculate trend using linear regression
            from sklearn.linear_model import LinearRegression
            
            X = np.arange(len(df)).reshape(-1, 1)
            y = df['demand'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            slope = model.coef_[0]
            r2 = model.score(X, y)
            
            # Only consider trend if R² is reasonable
            if r2 < 0.1:
                return "stable"
            
            if slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"Error determining trend direction: {e}")
            return "unknown"
    
    async def _calculate_forecast_quality(self, 
                                        accuracy_metrics: Dict[str, float],
                                        seasonality_detected: bool,
                                        data_length: int) -> float:
        """Calculate overall forecast quality score"""
        try:
            quality = 0.5  # Base quality
            
            # Accuracy component (40%)
            mape = accuracy_metrics.get("mape", 100)
            if mape < 10:
                quality += 0.2
            elif mape < 20:
                quality += 0.1
            elif mape > 50:
                quality -= 0.2
            
            # Data length component (20%)
            if data_length >= 90:
                quality += 0.1
            elif data_length >= 60:
                quality += 0.05
            elif data_length < 30:
                quality -= 0.1
            
            # Seasonality component (20%)
            if seasonality_detected:
                quality += 0.1  # Seasonality makes forecasting more reliable
            
            # Trend component (20%)
            # This would be calculated based on trend strength
            
            return max(0, min(1, quality))
            
        except Exception as e:
            logger.error(f"Error calculating forecast quality: {e}")
            return 0.5
    
    async def _generate_forecast_recommendations(self, 
                                               item_id: str,
                                               predictions: List[Dict[str, Any]],
                                               seasonality_detected: bool,
                                               trend_direction: str) -> List[str]:
        """Generate recommendations based on forecast"""
        try:
            recommendations = []
            
            if not predictions:
                return ["Insufficient data for reliable forecasting"]
            
            # Calculate average predicted demand
            avg_demand = np.mean([p['demand'] for p in predictions])
            
            # Trend-based recommendations
            if trend_direction == "increasing":
                recommendations.append("Demand is increasing - consider increasing inventory levels")
            elif trend_direction == "decreasing":
                recommendations.append("Demand is decreasing - consider reducing inventory or offering promotions")
            else:
                recommendations.append("Demand is stable - maintain current inventory levels")
            
            # Seasonality recommendations
            if seasonality_detected:
                recommendations.append("Seasonal patterns detected - adjust inventory planning accordingly")
            
            # Demand level recommendations
            if avg_demand > 50:
                recommendations.append("High demand expected - ensure adequate stock levels")
            elif avg_demand < 10:
                recommendations.append("Low demand expected - consider promotional activities")
            
            # Variability recommendations
            demand_values = [p['demand'] for p in predictions]
            demand_std = np.std(demand_values)
            demand_cv = demand_std / avg_demand if avg_demand > 0 else 0
            
            if demand_cv > 0.5:
                recommendations.append("High demand variability - maintain safety stock")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating forecast recommendations: {e}")
            return ["Error generating recommendations"]
    
    async def get_seasonal_patterns(self, category: str) -> Dict[str, Any]:
        """Get seasonal patterns for a category"""
        try:
            # In a real implementation, this would analyze historical data for the category
            # For now, return mock seasonal patterns
            
            patterns = {
                "category": category,
                "seasonal_patterns": [
                    {
                        "pattern_type": "weekly",
                        "strength": 0.3,
                        "description": "Higher demand on weekends",
                        "peak_days": ["Saturday", "Sunday"],
                        "low_days": ["Monday", "Tuesday"]
                    },
                    {
                        "pattern_type": "monthly",
                        "strength": 0.2,
                        "description": "Higher demand mid-month",
                        "peak_period": "Days 10-20",
                        "low_period": "Month end"
                    }
                ],
                "trend_analysis": {
                    "overall_trend": "increasing",
                    "trend_strength": 0.4,
                    "seasonal_adjustment": "multiplicative"
                },
                "recommendations": [
                    "Plan inventory increases for weekend periods",
                    "Consider promotional activities during low-demand periods",
                    "Monitor mid-month demand spikes"
                ]
            }
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting seasonal patterns for {category}: {e}")
            return {}
    
    async def optimize_inventory(self, 
                               item_ids: List[str],
                               target_service_level: float = 0.95) -> List[InventoryRecommendation]:
        """Optimize inventory levels based on demand forecasts"""
        try:
            logger.info(f"Optimizing inventory for {len(item_ids)} items")
            
            recommendations = []
            
            for item_id in item_ids:
                try:
                    # Get demand forecast
                    forecast_result = await self._forecast_item_demand(item_id, 30, ForecastMethod.ENSEMBLE)
                    
                    if not forecast_result:
                        continue
                    
                    # Get current inventory (mock data)
                    current_stock = np.random.randint(0, 100)
                    
                    # Calculate optimal inventory
                    avg_demand = np.mean([p['demand'] for p in forecast_result.predictions])
                    demand_std = np.std([p['demand'] for p in forecast_result.predictions])
                    
                    # Calculate reorder point and quantity
                    lead_time = 7  # days
                    safety_stock = self._calculate_safety_stock(demand_std, lead_time, target_service_level)
                    reorder_point = int(avg_demand * lead_time + safety_stock)
                    reorder_quantity = int(avg_demand * 14)  # 2 weeks of demand
                    
                    # Calculate recommended stock
                    recommended_stock = reorder_point + reorder_quantity
                    stock_change = recommended_stock - current_stock
                    
                    # Calculate risks
                    stockout_risk = self._calculate_stockout_risk(current_stock, avg_demand, demand_std)
                    overstock_risk = self._calculate_overstock_risk(current_stock, avg_demand)
                    
                    # Generate recommendation reason
                    reason = self._generate_inventory_recommendation_reason(
                        current_stock, recommended_stock, avg_demand, stockout_risk, overstock_risk
                    )
                    
                    recommendation = InventoryRecommendation(
                        item_id=item_id,
                        current_stock=current_stock,
                        recommended_stock=recommended_stock,
                        stock_change=stock_change,
                        reorder_point=reorder_point,
                        reorder_quantity=reorder_quantity,
                        stockout_risk=stockout_risk,
                        overstock_risk=overstock_risk,
                        recommendation_reason=reason
                    )
                    
                    recommendations.append(recommendation)
                    
                except Exception as e:
                    logger.warning(f"Error optimizing inventory for item {item_id}: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error optimizing inventory: {e}")
            return []
    
    def _calculate_safety_stock(self, demand_std: float, lead_time: int, service_level: float) -> float:
        """Calculate safety stock based on demand variability and service level"""
        try:
            # Z-score for service level
            from scipy.stats import norm
            z_score = norm.ppf(service_level)
            
            # Safety stock = Z * sqrt(lead_time) * demand_std
            safety_stock = z_score * np.sqrt(lead_time) * demand_std
            
            return max(0, safety_stock)
            
        except Exception as e:
            logger.error(f"Error calculating safety stock: {e}")
            return 0
    
    def _calculate_stockout_risk(self, current_stock: int, avg_demand: float, demand_std: float) -> float:
        """Calculate stockout risk"""
        try:
            if avg_demand <= 0:
                return 0.0
            
            # Probability that demand exceeds current stock
            from scipy.stats import norm
            z_score = (current_stock - avg_demand) / (demand_std + 1e-8)
            stockout_risk = 1 - norm.cdf(z_score)
            
            return max(0, min(1, stockout_risk))
            
        except Exception as e:
            logger.error(f"Error calculating stockout risk: {e}")
            return 0.5
    
    def _calculate_overstock_risk(self, current_stock: int, avg_demand: float) -> float:
        """Calculate overstock risk"""
        try:
            if avg_demand <= 0:
                return 0.0
            
            # Simple overstock risk based on stock-to-demand ratio
            ratio = current_stock / (avg_demand * 30)  # 30 days of demand
            
            if ratio > 2:
                return 0.8
            elif ratio > 1.5:
                return 0.5
            elif ratio > 1:
                return 0.2
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating overstock risk: {e}")
            return 0.0
    
    def _generate_inventory_recommendation_reason(self, 
                                                current_stock: int,
                                                recommended_stock: int,
                                                avg_demand: float,
                                                stockout_risk: float,
                                                overstock_risk: float) -> str:
        """Generate reason for inventory recommendation"""
        try:
            stock_change = recommended_stock - current_stock
            
            if stock_change > 0:
                if stockout_risk > 0.3:
                    return f"Increase inventory by {stock_change} units to reduce stockout risk ({stockout_risk:.1%})"
                else:
                    return f"Increase inventory by {stock_change} units to meet expected demand"
            elif stock_change < 0:
                if overstock_risk > 0.5:
                    return f"Reduce inventory by {abs(stock_change)} units to avoid overstock (risk: {overstock_risk:.1%})"
                else:
                    return f"Reduce inventory by {abs(stock_change)} units based on demand forecast"
            else:
                return "Current inventory levels are optimal"
                
        except Exception as e:
            logger.error(f"Error generating inventory recommendation reason: {e}")
            return "Inventory optimization recommended"


