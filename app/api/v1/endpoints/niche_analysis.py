"""
API endpoints for niche analysis and beginner guidance
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.niche_analysis_service import NicheAnalysisService, NicheDifficulty, SupplierType
from app.schemas.niche_analysis import (
    NicheAnalysisRequest, NicheAnalysisResponse,
    SupplierSearchRequest, SupplierSearchResponse,
    PricingRequest, PricingResponse,
    BeginnerRecommendationsRequest, BeginnerRecommendationsResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize niche analysis service
niche_service = NicheAnalysisService()


@router.post("/analyze", response_model=NicheAnalysisResponse)
async def analyze_niche(
    request: NicheAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Analyze a specific niche for e-commerce opportunities"""
    try:
        metrics = await niche_service.analyze_niche(
            niche=request.niche,
            keywords=request.keywords
        )
        
        return NicheAnalysisResponse(
            niche=request.niche,
            keywords=request.keywords,
            competition_level=metrics.competition_level,
            market_size=metrics.market_size,
            average_price=metrics.average_price,
            min_price=metrics.price_range[0],
            max_price=metrics.price_range[1],
            demand_trend=metrics.demand_trend,
            seasonality=metrics.seasonality,
            profit_margin=metrics.profit_margin,
            difficulty=metrics.difficulty.value,
            growth_potential=metrics.growth_potential,
            recommendation_score=self._calculate_recommendation_score(metrics)
        )
        
    except Exception as e:
        logger.error(f"Niche analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/suppliers", response_model=SupplierSearchResponse)
async def find_suppliers(
    request: SupplierSearchRequest,
    background_tasks: BackgroundTasks
):
    """Find suppliers for a specific product"""
    try:
        suppliers = await niche_service.find_suppliers(
            product_name=request.product_name,
            category=request.category,
            budget=request.budget
        )
        
        supplier_data = []
        for supplier in suppliers:
            supplier_data.append({
                "name": supplier.name,
                "type": supplier.type.value,
                "country": supplier.country,
                "min_order_quantity": supplier.min_order_quantity,
                "price_per_unit": supplier.price_per_unit,
                "shipping_cost": supplier.shipping_cost,
                "delivery_time_days": supplier.delivery_time_days,
                "quality_rating": supplier.quality_rating,
                "reliability_score": supplier.reliability_score,
                "total_cost": supplier.price_per_unit + supplier.shipping_cost,
                "contact_info": supplier.contact_info
            })
        
        return SupplierSearchResponse(
            product_name=request.product_name,
            category=request.category,
            budget=request.budget,
            suppliers_found=len(supplier_data),
            suppliers=supplier_data
        )
        
    except Exception as e:
        logger.error(f"Supplier search error: {e}")
        raise HTTPException(status_code=500, detail=f"Supplier search failed: {str(e)}")


@router.post("/pricing", response_model=PricingResponse)
async def calculate_pricing(
    request: PricingRequest,
    background_tasks: BackgroundTasks
):
    """Calculate optimal pricing for a product"""
    try:
        pricing = await niche_service.calculate_pricing(
            product_name=request.product_name,
            category=request.category,
            supplier_cost=request.supplier_cost,
            target_margin=request.target_margin
        )
        
        return PricingResponse(
            product_name=pricing.product_name,
            recommended_price=pricing.recommended_price,
            min_price=pricing.min_price,
            max_price=pricing.max_price,
            competitor_analysis=pricing.competitor_analysis,
            profit_margin=pricing.profit_margin,
            market_position=pricing.market_position,
            pricing_strategy=pricing.pricing_strategy,
            supplier_cost=request.supplier_cost,
            target_margin=request.target_margin
        )
        
    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Pricing calculation failed: {str(e)}")


@router.post("/beginner-recommendations", response_model=BeginnerRecommendationsResponse)
async def get_beginner_recommendations(
    request: BeginnerRecommendationsRequest,
    background_tasks: BackgroundTasks
):
    """Get personalized recommendations for beginners"""
    try:
        recommendations = await niche_service.get_beginner_recommendations(
            budget=request.budget,
            experience_level=request.experience_level
        )
        
        if "error" in recommendations:
            raise HTTPException(status_code=400, detail=recommendations["error"])
        
        return BeginnerRecommendationsResponse(**recommendations)
        
    except Exception as e:
        logger.error(f"Beginner recommendations error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.get("/popular-niches")
async def get_popular_niches():
    """Get list of popular niches for analysis"""
    try:
        return {
            "popular_niches": niche_service.popular_niches,
            "niche_descriptions": {
                "electronics": "Электроника и гаджеты",
                "fashion": "Мода и одежда",
                "beauty_health": "Красота и здоровье",
                "home_garden": "Дом и сад",
                "sports_outdoors": "Спорт и отдых",
                "toys_games": "Игрушки и игры",
                "automotive": "Автомобильные товары",
                "books_media": "Книги и медиа",
                "food_beverages": "Еда и напитки",
                "jewelry_watches": "Украшения и часы",
                "pet_supplies": "Товары для животных",
                "office_supplies": "Канцелярские товары"
            }
        }
    except Exception as e:
        logger.error(f"Error getting popular niches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get niches: {str(e)}")


@router.get("/supplier-types")
async def get_supplier_types():
    """Get available supplier types"""
    try:
        return {
            "supplier_types": [
                {
                    "value": supplier_type.value,
                    "name": supplier_type.name,
                    "description": _get_supplier_type_description(supplier_type)
                }
                for supplier_type in SupplierType
            ]
        }
    except Exception as e:
        logger.error(f"Error getting supplier types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supplier types: {str(e)}")


@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """Get available difficulty levels"""
    try:
        return {
            "difficulty_levels": [
                {
                    "value": difficulty.value,
                    "name": difficulty.name,
                    "description": _get_difficulty_description(difficulty)
                }
                for difficulty in NicheDifficulty
            ]
        }
    except Exception as e:
        logger.error(f"Error getting difficulty levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get difficulty levels: {str(e)}")


@router.get("/beginner-tips")
async def get_beginner_tips(
    experience_level: str = Query(..., description="Experience level: complete_beginner, some_experience")
):
    """Get tips for beginners based on experience level"""
    try:
        tips = niche_service._get_beginner_tips(experience_level)
        next_steps = niche_service._get_next_steps(experience_level)
        
        return {
            "experience_level": experience_level,
            "tips": tips,
            "next_steps": next_steps
        }
    except Exception as e:
        logger.error(f"Error getting beginner tips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tips: {str(e)}")


@router.get("/profit-calculator")
async def calculate_profit(
    product_name: str = Query(..., description="Product name"),
    supplier_cost: float = Query(..., description="Supplier cost per unit"),
    selling_price: float = Query(..., description="Selling price"),
    marketplace_fees: float = Query(0.1, description="Marketplace fees (0.1 = 10%)"),
    shipping_cost: float = Query(0, description="Shipping cost per unit"),
    other_costs: float = Query(0, description="Other costs per unit")
):
    """Calculate profit margins and costs"""
    try:
        # Calculate costs
        total_costs = supplier_cost + shipping_cost + other_costs
        marketplace_fee_amount = selling_price * marketplace_fees
        total_costs += marketplace_fee_amount
        
        # Calculate profit
        profit_per_unit = selling_price - total_costs
        profit_margin = (profit_per_unit / selling_price) * 100 if selling_price > 0 else 0
        
        # Calculate break-even
        break_even_price = total_costs / (1 - marketplace_fees) if marketplace_fees < 1 else total_costs
        
        return {
            "product_name": product_name,
            "selling_price": selling_price,
            "total_costs": round(total_costs, 2),
            "profit_per_unit": round(profit_per_unit, 2),
            "profit_margin": round(profit_margin, 2),
            "break_even_price": round(break_even_price, 2),
            "cost_breakdown": {
                "supplier_cost": supplier_cost,
                "shipping_cost": shipping_cost,
                "marketplace_fees": round(marketplace_fee_amount, 2),
                "other_costs": other_costs
            },
            "recommendations": _get_profit_recommendations(profit_margin)
        }
    except Exception as e:
        logger.error(f"Error calculating profit: {e}")
        raise HTTPException(status_code=500, detail=f"Profit calculation failed: {str(e)}")


def _calculate_recommendation_score(metrics) -> float:
    """Calculate overall recommendation score for a niche"""
    # Weighted score based on multiple factors
    score = (
        metrics.growth_potential * 0.3 +
        (1 - metrics.competition_level) * 0.25 +
        metrics.profit_margin * 0.25 +
        (1 - metrics.seasonality) * 0.2
    )
    return min(score, 1.0)


def _get_supplier_type_description(supplier_type: SupplierType) -> str:
    """Get description for supplier type"""
    descriptions = {
        SupplierType.MANUFACTURER: "Производитель - прямые поставки от фабрики",
        SupplierType.WHOLESALER: "Оптовик - крупные партии со скидками",
        SupplierType.DROPSHIPPER: "Дропшиппер - без собственных складов",
        SupplierType.DISTRIBUTOR: "Дистрибьютор - официальный представитель бренда"
    }
    return descriptions.get(supplier_type, "Неизвестный тип поставщика")


def _get_difficulty_description(difficulty: NicheDifficulty) -> str:
    """Get description for difficulty level"""
    descriptions = {
        NicheDifficulty.EASY: "Легко - низкая конкуренция, высокая маржа",
        NicheDifficulty.MEDIUM: "Средне - умеренная конкуренция",
        NicheDifficulty.HARD: "Сложно - высокая конкуренция, требует опыта",
        NicheDifficulty.EXPERT: "Эксперт - очень сложная ниша, только для профессионалов"
    }
    return descriptions.get(difficulty, "Неизвестный уровень сложности")


def _get_profit_recommendations(profit_margin: float) -> List[str]:
    """Get recommendations based on profit margin"""
    if profit_margin >= 50:
        return [
            "Отличная маржа! Рассмотрите возможность увеличения объемов",
            "Можете позволить себе рекламу и продвижение",
            "Рассмотрите создание собственного бренда"
        ]
    elif profit_margin >= 30:
        return [
            "Хорошая маржа, но есть потенциал для улучшения",
            "Ищите способы снизить себестоимость",
            "Рассмотрите прямые поставки от производителя"
        ]
    elif profit_margin >= 15:
        return [
            "Маржа на грани рентабельности",
            "Необходимо пересмотреть ценообразование",
            "Ищите более дешевых поставщиков"
        ]
    else:
        return [
            "Очень низкая маржа, проект может быть убыточным",
            "Срочно пересмотрите всю бизнес-модель",
            "Рассмотрите другую нишу или товары"
        ]
