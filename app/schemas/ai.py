"""
Pydantic schemas for AI and Machine Learning features
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request schema for price prediction"""
    item_data: Dict[str, Any] = Field(..., description="Item data for prediction")
    days_ahead: int = Field(default=7, ge=1, le=30, description="Number of days to predict ahead")


class PricePrediction(BaseModel):
    """Schema for individual price prediction"""
    date: str = Field(..., description="Prediction date")
    predicted_price: float = Field(..., description="Predicted price")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")


class PredictionResponse(BaseModel):
    """Response schema for price prediction"""
    item_id: Optional[int] = Field(None, description="Item ID")
    item_name: Optional[str] = Field(None, description="Item name")
    current_price: Optional[float] = Field(None, description="Current price")
    predictions: List[PricePrediction] = Field(..., description="Price predictions")
    model_used: str = Field(..., description="ML model used for prediction")


class AnomalyResponse(BaseModel):
    """Response schema for price anomaly"""
    timestamp: str = Field(..., description="Anomaly timestamp")
    price: float = Field(..., description="Anomalous price")
    expected_price: Optional[float] = Field(None, description="Expected price")
    z_score: Optional[float] = Field(None, description="Z-score")
    anomaly_type: str = Field(..., description="Type of anomaly")
    severity: float = Field(..., ge=0, le=1, description="Anomaly severity (0-1)")
    description: str = Field(..., description="Human-readable description")


class TrendAnalysisResponse(BaseModel):
    """Response schema for trend analysis"""
    trend_slope: float = Field(..., description="Price trend slope")
    trend_direction: str = Field(..., description="Trend direction (increasing/decreasing/stable)")
    volatility: float = Field(..., description="Price volatility")
    current_price: float = Field(..., description="Current price")
    min_price: float = Field(..., description="Minimum price in period")
    max_price: float = Field(..., description="Maximum price in period")
    avg_price: float = Field(..., description="Average price in period")
    price_range: float = Field(..., description="Price range (max - min)")
    monthly_patterns: Dict[str, float] = Field(..., description="Monthly price patterns")
    weekly_patterns: Dict[str, float] = Field(..., description="Weekly price patterns")
    data_points: int = Field(..., description="Number of data points analyzed")
    time_span_days: int = Field(..., description="Time span in days")


class RecommendationResponse(BaseModel):
    """Response schema for item recommendation"""
    item: Dict[str, Any] = Field(..., description="Recommended item data")
    score: float = Field(..., ge=0, le=1, description="Recommendation score (0-1)")
    reason: str = Field(..., description="Reason for recommendation")


class ModelMetrics(BaseModel):
    """Schema for model performance metrics"""
    mae: Optional[float] = Field(None, description="Mean Absolute Error")
    mse: Optional[float] = Field(None, description="Mean Squared Error")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error")
    r2: Optional[float] = Field(None, description="R-squared score")
    cv_mean: Optional[float] = Field(None, description="Cross-validation mean score")
    cv_std: Optional[float] = Field(None, description="Cross-validation std score")


class ModelInfo(BaseModel):
    """Schema for model information"""
    trained: bool = Field(..., description="Whether model is trained")
    model_type: Optional[str] = Field(None, description="Model type")
    last_trained: Optional[float] = Field(None, description="Last training timestamp")
    error: Optional[str] = Field(None, description="Error message if any")


class ModelPerformanceResponse(BaseModel):
    """Response schema for model performance"""
    performance: Dict[str, ModelInfo] = Field(..., description="Performance info for each model")


class TrainingRequest(BaseModel):
    """Request schema for model training"""
    data_source: str = Field(default="database", description="Data source for training")
    models: Optional[List[str]] = Field(None, description="Specific models to train")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set size")


class TrainingResponse(BaseModel):
    """Response schema for model training"""
    success: bool = Field(..., description="Whether training was successful")
    results: Dict[str, ModelMetrics] = Field(..., description="Training results for each model")
    training_time: float = Field(..., description="Training time in seconds")


class AIInsightsResponse(BaseModel):
    """Response schema for AI insights"""
    item_id: Optional[int] = Field(None, description="Item ID")
    analysis_period_days: int = Field(..., description="Analysis period in days")
    insights: Dict[str, Any] = Field(..., description="AI insights")
    timestamp: float = Field(..., description="Analysis timestamp")


