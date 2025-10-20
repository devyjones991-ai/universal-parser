"""
AI and Machine Learning service for price prediction and analysis
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import joblib
import os
from pathlib import Path
import logging

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import optuna

from app.core.cache import cache_service, cached
from app.core.config import settings

logger = logging.getLogger(__name__)


class PricePredictionService:
    """Service for price prediction using machine learning"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models"""
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'xgboost': xgb.XGBRegressor(n_estimators=100, random_state=42),
            'lightgbm': lgb.LGBMRegressor(n_estimators=100, random_state=42, verbose=-1),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0)
        }
        
        # Initialize scalers and encoders
        self.scalers = {
            'price': StandardScaler(),
            'features': StandardScaler()
        }
        
        self.encoders = {
            'marketplace': LabelEncoder(),
            'category': LabelEncoder()
        }
    
    def prepare_features(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for ML models"""
        if not data:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(data)
        
        # Convert timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Encode categorical features
        if 'marketplace' in df.columns:
            df['marketplace_encoded'] = self.encoders['marketplace'].fit_transform(df['marketplace'])
        if 'category' in df.columns:
            df['category_encoded'] = self.encoders['category'].fit_transform(df['category'])
        
        # Create lag features
        df = df.sort_values('timestamp')
        df['price_lag_1'] = df['price'].shift(1)
        df['price_lag_7'] = df['price'].shift(7)
        df['price_lag_30'] = df['price'].shift(30)
        
        # Rolling statistics
        df['price_ma_7'] = df['price'].rolling(window=7).mean()
        df['price_ma_30'] = df['price'].rolling(window=30).mean()
        df['price_std_7'] = df['price'].rolling(window=7).std()
        df['price_std_30'] = df['price'].rolling(window=30).std()
        
        # Price change features
        df['price_change_1d'] = df['price'].pct_change(1)
        df['price_change_7d'] = df['price'].pct_change(7)
        df['price_change_30d'] = df['price'].pct_change(30)
        
        # Select features
        feature_columns = [
            'day_of_week', 'month', 'day_of_year', 'is_weekend',
            'price_lag_1', 'price_lag_7', 'price_lag_30',
            'price_ma_7', 'price_ma_30', 'price_std_7', 'price_std_30',
            'price_change_1d', 'price_change_7d', 'price_change_30d'
        ]
        
        # Add encoded categorical features
        if 'marketplace_encoded' in df.columns:
            feature_columns.append('marketplace_encoded')
        if 'category_encoded' in df.columns:
            feature_columns.append('category_encoded')
        
        # Handle missing values
        df[feature_columns] = df[feature_columns].fillna(0)
        
        # Prepare X and y
        X = df[feature_columns].values
        y = df['price'].values
        
        return X, y
    
    @cached(expire=3600)  # Cache for 1 hour
    async def train_models(self, data: List[Dict]) -> Dict[str, Dict[str, float]]:
        """Train all ML models on price data"""
        if len(data) < 50:  # Need minimum data for training
            return {"error": "Insufficient data for training (minimum 50 records required)"}
        
        X, y = self.prepare_features(data)
        
        if len(X) == 0:
            return {"error": "No valid features found"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scalers['features'].fit_transform(X_train)
        X_test_scaled = self.scalers['features'].transform(X_test)
        
        results = {}
        
        # Train and evaluate each model
        for name, model in self.models.items():
            try:
                # Train model
                if name in ['xgboost', 'lightgbm']:
                    model.fit(X_train_scaled, y_train)
                else:
                    model.fit(X_train_scaled, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test_scaled)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, y_pred)
                
                # Cross-validation score
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
                
                results[name] = {
                    'mae': float(mae),
                    'mse': float(mse),
                    'rmse': float(rmse),
                    'r2': float(r2),
                    'cv_mean': float(cv_scores.mean()),
                    'cv_std': float(cv_scores.std())
                }
                
                # Save model
                model_path = self.model_dir / f"{name}_model.joblib"
                joblib.dump(model, model_path)
                
                logger.info(f"Trained {name}: R² = {r2:.3f}, MAE = {mae:.2f}")
                
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                results[name] = {"error": str(e)}
        
        # Save scalers and encoders
        joblib.dump(self.scalers, self.model_dir / "scalers.joblib")
        joblib.dump(self.encoders, self.model_dir / "encoders.joblib")
        
        return results
    
    async def predict_price(self, item_data: Dict, days_ahead: int = 7) -> Dict[str, Any]:
        """Predict future prices for an item"""
        try:
            # Load the best model (Random Forest by default)
            model_path = self.model_dir / "random_forest_model.joblib"
            if not model_path.exists():
                return {"error": "No trained model found. Please train models first."}
            
            model = joblib.load(model_path)
            
            # Load scalers and encoders
            scalers = joblib.load(self.model_dir / "scalers.joblib")
            encoders = joblib.load(self.model_dir / "encoders.joblib")
            
            # Prepare features for prediction
            current_time = datetime.now()
            predictions = []
            
            for i in range(days_ahead):
                future_time = current_time + timedelta(days=i)
                
                # Create feature vector
                features = np.array([[
                    future_time.dayofweek,  # day_of_week
                    future_time.month,     # month
                    future_time.timetuple().tm_yday,  # day_of_year
                    1 if future_time.weekday() >= 5 else 0,  # is_weekend
                    item_data.get('current_price', 0),  # price_lag_1 (current price)
                    item_data.get('current_price', 0),  # price_lag_7 (simplified)
                    item_data.get('current_price', 0),  # price_lag_30 (simplified)
                    item_data.get('current_price', 0),  # price_ma_7 (simplified)
                    item_data.get('current_price', 0),  # price_ma_30 (simplified)
                    0,  # price_std_7
                    0,  # price_std_30
                    0,  # price_change_1d
                    0,  # price_change_7d
                    0,  # price_change_30d
                ]])
                
                # Add encoded categorical features if available
                if 'marketplace' in item_data:
                    try:
                        marketplace_encoded = encoders['marketplace'].transform([item_data['marketplace']])[0]
                        features = np.append(features, [[marketplace_encoded]], axis=1)
                    except:
                        features = np.append(features, [[0]], axis=1)
                else:
                    features = np.append(features, [[0]], axis=1)
                
                if 'category' in item_data:
                    try:
                        category_encoded = encoders['category'].transform([item_data['category']])[0]
                        features = np.append(features, [[category_encoded]], axis=1)
                    except:
                        features = np.append(features, [[0]], axis=1)
                else:
                    features = np.append(features, [[0]], axis=1)
                
                # Scale features
                features_scaled = scalers['features'].transform(features)
                
                # Make prediction
                prediction = model.predict(features_scaled)[0]
                predictions.append({
                    'date': future_time.strftime('%Y-%m-%d'),
                    'predicted_price': float(prediction),
                    'confidence': 0.8  # Simplified confidence score
                })
            
            return {
                'item_id': item_data.get('id'),
                'item_name': item_data.get('name'),
                'current_price': item_data.get('current_price'),
                'predictions': predictions,
                'model_used': 'random_forest'
            }
            
        except Exception as e:
            logger.error(f"Error predicting price: {e}")
            return {"error": str(e)}
    
    async def detect_anomalies(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Detect price anomalies using statistical methods"""
        if not data:
            return []
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        anomalies = []
        
        # Calculate rolling statistics
        window = 7
        df['price_ma'] = df['price'].rolling(window=window).mean()
        df['price_std'] = df['price'].rolling(window=window).std()
        
        # Z-score method
        df['z_score'] = (df['price'] - df['price_ma']) / df['price_std']
        
        # IQR method
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Detect anomalies
        for idx, row in df.iterrows():
            is_anomaly = False
            anomaly_type = None
            severity = 0
            
            # Z-score anomaly
            if abs(row['z_score']) > 2:
                is_anomaly = True
                anomaly_type = "z_score"
                severity = min(abs(row['z_score']) / 3, 1.0)
            
            # IQR anomaly
            elif row['price'] < lower_bound or row['price'] > upper_bound:
                is_anomaly = True
                anomaly_type = "iqr"
                severity = 0.8
            
            if is_anomaly:
                anomalies.append({
                    'timestamp': row['timestamp'].isoformat(),
                    'price': float(row['price']),
                    'expected_price': float(row['price_ma']) if not pd.isna(row['price_ma']) else None,
                    'z_score': float(row['z_score']) if not pd.isna(row['z_score']) else None,
                    'anomaly_type': anomaly_type,
                    'severity': severity,
                    'description': f"Price anomaly detected: {row['price']:.2f} (expected: {row['price_ma']:.2f})"
                })
        
        return anomalies
    
    async def analyze_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze price trends and seasonality"""
        if not data:
            return {"error": "No data provided"}
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate trend
        df['day'] = (df['timestamp'] - df['timestamp'].min()).dt.days
        trend_slope = np.polyfit(df['day'], df['price'], 1)[0]
        
        # Calculate seasonality
        df['month'] = df['timestamp'].dt.month
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        monthly_avg = df.groupby('month')['price'].mean()
        weekly_avg = df.groupby('day_of_week')['price'].mean()
        
        # Calculate volatility
        price_changes = df['price'].pct_change().dropna()
        volatility = price_changes.std() * np.sqrt(252)  # Annualized volatility
        
        # Price statistics
        current_price = df['price'].iloc[-1]
        min_price = df['price'].min()
        max_price = df['price'].max()
        avg_price = df['price'].mean()
        
        # Trend direction
        if trend_slope > 0.01:
            trend_direction = "increasing"
        elif trend_slope < -0.01:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
        
        return {
            'trend_slope': float(trend_slope),
            'trend_direction': trend_direction,
            'volatility': float(volatility),
            'current_price': float(current_price),
            'min_price': float(min_price),
            'max_price': float(max_price),
            'avg_price': float(avg_price),
            'price_range': float(max_price - min_price),
            'monthly_patterns': monthly_avg.to_dict(),
            'weekly_patterns': weekly_avg.to_dict(),
            'data_points': len(df),
            'time_span_days': (df['timestamp'].max() - df['timestamp'].min()).days
        }
    
    async def get_recommendations(self, user_items: List[Dict], all_items: List[Dict]) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations"""
        if not user_items or not all_items:
            return []
        
        recommendations = []
        
        # Simple recommendation based on similar items
        user_categories = set(item.get('category', '') for item in user_items if item.get('category'))
        user_marketplaces = set(item.get('marketplace', '') for item in user_items)
        
        for item in all_items:
            if item in user_items:  # Skip items user already has
                continue
            
            score = 0
            
            # Category similarity
            if item.get('category') in user_categories:
                score += 0.4
            
            # Marketplace similarity
            if item.get('marketplace') in user_marketplaces:
                score += 0.3
            
            # Price range similarity
            user_prices = [i.get('current_price', 0) for i in user_items if i.get('current_price')]
            if user_prices and item.get('current_price'):
                avg_user_price = np.mean(user_prices)
                price_diff = abs(item['current_price'] - avg_user_price) / avg_user_price
                if price_diff < 0.2:  # Within 20% of user's average price
                    score += 0.3
            
            if score > 0.3:  # Minimum threshold
                recommendations.append({
                    'item': item,
                    'score': score,
                    'reason': self._get_recommendation_reason(item, user_items, score)
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:10]
    
    def _get_recommendation_reason(self, item: Dict, user_items: List[Dict], score: float) -> str:
        """Generate human-readable reason for recommendation"""
        reasons = []
        
        user_categories = set(i.get('category', '') for i in user_items if i.get('category'))
        if item.get('category') in user_categories:
            reasons.append(f"Similar category: {item.get('category')}")
        
        user_marketplaces = set(i.get('marketplace', '') for i in user_items)
        if item.get('marketplace') in user_marketplaces:
            reasons.append(f"From your preferred marketplace: {item.get('marketplace')}")
        
        user_prices = [i.get('current_price', 0) for i in user_items if i.get('current_price')]
        if user_prices and item.get('current_price'):
            avg_user_price = np.mean(user_prices)
            price_diff = abs(item['current_price'] - avg_user_price) / avg_user_price
            if price_diff < 0.2:
                reasons.append("Similar price range")
        
        return "; ".join(reasons) if reasons else "Based on your preferences"
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all trained models"""
        performance = {}
        
        for model_name in self.models.keys():
            model_path = self.model_dir / f"{model_name}_model.joblib"
            if model_path.exists():
                try:
                    model = joblib.load(model_path)
                    performance[model_name] = {
                        'trained': True,
                        'model_type': type(model).__name__,
                        'last_trained': model_path.stat().st_mtime
                    }
                except Exception as e:
                    performance[model_name] = {
                        'trained': False,
                        'error': str(e)
                    }
            else:
                performance[model_name] = {
                    'trained': False,
                    'error': 'Model not found'
                }
        
        return performance


