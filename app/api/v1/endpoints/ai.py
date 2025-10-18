"""
API endpoints for AI and Machine Learning features
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ai_service import PricePredictionService
from app.schemas.ai import (
    PredictionRequest, PredictionResponse, 
    AnomalyResponse, TrendAnalysisResponse,
    RecommendationResponse, ModelPerformanceResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize AI service
ai_service = PricePredictionService()


@router.post("/predict", response_model=PredictionResponse)
async def predict_price(
    request: PredictionRequest,
    background_tasks: BackgroundTasks
):
    """Predict future prices for an item"""
    try:
        result = await ai_service.predict_price(
            item_data=request.item_data,
            days_ahead=request.days_ahead
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return PredictionResponse(**result)
        
    except Exception as e:
        logger.error(f"Price prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/train", response_model=Dict[str, Any])
async def train_models(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Train ML models on historical price data"""
    try:
        # Get historical data from database
        # This would typically fetch from your database
        # For now, we'll use mock data
        historical_data = [
            {
                "timestamp": "2024-01-01T00:00:00",
                "price": 100.0,
                "marketplace": "wildberries",
                "category": "electronics"
            },
            # Add more historical data here
        ]
        
        result = await ai_service.train_models(historical_data)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Model training error: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/anomalies", response_model=List[AnomalyResponse])
async def detect_anomalies(
    data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """Detect price anomalies in historical data"""
    try:
        anomalies = await ai_service.detect_anomalies(data)
        
        return [AnomalyResponse(**anomaly) for anomaly in anomalies]
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@router.post("/trends", response_model=TrendAnalysisResponse)
async def analyze_trends(
    data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """Analyze price trends and seasonality"""
    try:
        trends = await ai_service.analyze_trends(data)
        
        if "error" in trends:
            raise HTTPException(status_code=400, detail=trends["error"])
        
        return TrendAnalysisResponse(**trends)
        
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.post("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    user_items: List[Dict[str, Any]],
    all_items: List[Dict[str, Any]],
    background_tasks: BackgroundTasks
):
    """Get AI-powered item recommendations"""
    try:
        recommendations = await ai_service.get_recommendations(user_items, all_items)
        
        return [RecommendationResponse(**rec) for rec in recommendations]
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.get("/models/performance", response_model=ModelPerformanceResponse)
async def get_model_performance():
    """Get performance metrics for all trained models"""
    try:
        performance = await ai_service.get_model_performance()
        return ModelPerformanceResponse(performance=performance)
        
    except Exception as e:
        logger.error(f"Model performance error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(e)}")


@router.get("/health")
async def ai_health_check():
    """Health check for AI service"""
    try:
        # Check if models directory exists
        import os
        models_dir = "models"
        models_exist = os.path.exists(models_dir) and len(os.listdir(models_dir)) > 0
        
        return {
            "status": "healthy",
            "models_available": models_exist,
            "service": "ai_service",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.delete("/models")
async def clear_models():
    """Clear all trained models"""
    try:
        import shutil
        import os
        
        models_dir = "models"
        if os.path.exists(models_dir):
            shutil.rmtree(models_dir)
            os.makedirs(models_dir, exist_ok=True)
        
        return {"message": "All models cleared successfully"}
        
    except Exception as e:
        logger.error(f"Clear models error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear models: {str(e)}")


@router.get("/insights")
async def get_ai_insights(
    item_id: Optional[int] = Query(None, description="Item ID for specific insights"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get comprehensive AI insights for items"""
    try:
        # This would typically fetch data from database
        # For now, return mock insights
        insights = {
            "item_id": item_id,
            "analysis_period_days": days,
            "insights": {
                "price_trend": "increasing",
                "volatility": "medium",
                "anomalies_detected": 2,
                "recommendation": "Consider monitoring closely due to high volatility",
                "confidence_score": 0.85
            },
            "timestamp": time.time()
        }
        
        return insights
        
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")
