"""
Pydantic schemas for niche analysis and beginner guidance
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ExperienceLevel(str, Enum):
    COMPLETE_BEGINNER = "complete_beginner"
    SOME_EXPERIENCE = "some_experience"
    EXPERIENCED = "experienced"


class NicheAnalysisRequest(BaseModel):
    """Request schema for niche analysis"""
    niche: str = Field(..., description="Niche to analyze")
    keywords: List[str] = Field(..., description="Keywords to search for in the niche")


class NicheAnalysisResponse(BaseModel):
    """Response schema for niche analysis"""
    niche: str
    keywords: List[str]
    competition_level: float = Field(..., ge=0, le=1, description="Competition level (0-1)")
    market_size: float = Field(..., description="Estimated market size")
    average_price: float = Field(..., description="Average product price in the niche")
    min_price: float = Field(..., description="Minimum price found")
    max_price: float = Field(..., description="Maximum price found")
    demand_trend: str = Field(..., description="Demand trend: growing, stable, declining")
    seasonality: float = Field(..., ge=0, le=1, description="Seasonality factor (0-1)")
    profit_margin: float = Field(..., ge=0, le=1, description="Average profit margin (0-1)")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard, expert")
    growth_potential: float = Field(..., ge=0, le=1, description="Growth potential (0-1)")
    recommendation_score: float = Field(..., ge=0, le=1, description="Overall recommendation score")


class SupplierSearchRequest(BaseModel):
    """Request schema for supplier search"""
    product_name: str = Field(..., description="Product name to find suppliers for")
    category: str = Field(..., description="Product category")
    budget: float = Field(..., gt=0, description="Maximum budget per unit")


class SupplierInfo(BaseModel):
    """Schema for supplier information"""
    name: str = Field(..., description="Supplier name")
    type: str = Field(..., description="Supplier type")
    country: str = Field(..., description="Supplier country")
    min_order_quantity: int = Field(..., description="Minimum order quantity")
    price_per_unit: float = Field(..., description="Price per unit")
    shipping_cost: float = Field(..., description="Shipping cost per unit")
    delivery_time_days: int = Field(..., description="Delivery time in days")
    quality_rating: float = Field(..., ge=0, le=5, description="Quality rating (0-5)")
    reliability_score: float = Field(..., ge=0, le=1, description="Reliability score (0-1)")
    total_cost: float = Field(..., description="Total cost per unit")
    contact_info: Dict[str, str] = Field(..., description="Contact information")


class SupplierSearchResponse(BaseModel):
    """Response schema for supplier search"""
    product_name: str
    category: str
    budget: float
    suppliers_found: int = Field(..., description="Number of suppliers found")
    suppliers: List[SupplierInfo] = Field(..., description="List of suppliers")


class PricingRequest(BaseModel):
    """Request schema for pricing calculation"""
    product_name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    supplier_cost: float = Field(..., gt=0, description="Supplier cost per unit")
    target_margin: float = Field(..., ge=0, le=1, description="Target profit margin (0-1)")


class PricingResponse(BaseModel):
    """Response schema for pricing calculation"""
    product_name: str
    recommended_price: float = Field(..., description="Recommended selling price")
    min_price: float = Field(..., description="Minimum recommended price")
    max_price: float = Field(..., description="Maximum recommended price")
    competitor_analysis: Dict[str, float] = Field(..., description="Competitor price analysis")
    profit_margin: float = Field(..., description="Actual profit margin")
    market_position: str = Field(..., description="Market position: budget, mid-range, premium")
    pricing_strategy: str = Field(..., description="Recommended pricing strategy")
    supplier_cost: float = Field(..., description="Supplier cost per unit")
    target_margin: float = Field(..., description="Target profit margin")


class BeginnerRecommendationsRequest(BaseModel):
    """Request schema for beginner recommendations"""
    budget: float = Field(..., gt=0, description="Available budget")
    experience_level: ExperienceLevel = Field(..., description="Experience level")


class NicheRecommendation(BaseModel):
    """Schema for niche recommendation"""
    niche: str = Field(..., description="Niche name")
    metrics: Dict[str, Any] = Field(..., description="Niche metrics")
    sample_products: List[Dict[str, Any]] = Field(..., description="Sample products")
    suppliers: List[SupplierInfo] = Field(..., description="Recommended suppliers")
    difficulty: str = Field(..., description="Difficulty level")
    growth_potential: float = Field(..., ge=0, le=1, description="Growth potential")
    profit_margin: float = Field(..., ge=0, le=1, description="Profit margin")


class BeginnerRecommendationsResponse(BaseModel):
    """Response schema for beginner recommendations"""
    budget: float
    experience_level: str
    recommendations: List[NicheRecommendation] = Field(..., description="Top niche recommendations")
    general_tips: List[str] = Field(..., description="General tips for beginners")
    next_steps: List[str] = Field(..., description="Next steps to take")


class ProfitCalculationRequest(BaseModel):
    """Request schema for profit calculation"""
    product_name: str = Field(..., description="Product name")
    supplier_cost: float = Field(..., gt=0, description="Supplier cost per unit")
    selling_price: float = Field(..., gt=0, description="Selling price")
    marketplace_fees: float = Field(0.1, ge=0, le=1, description="Marketplace fees (0-1)")
    shipping_cost: float = Field(0, ge=0, description="Shipping cost per unit")
    other_costs: float = Field(0, ge=0, description="Other costs per unit")


class ProfitCalculationResponse(BaseModel):
    """Response schema for profit calculation"""
    product_name: str
    selling_price: float
    total_costs: float = Field(..., description="Total costs per unit")
    profit_per_unit: float = Field(..., description="Profit per unit")
    profit_margin: float = Field(..., description="Profit margin percentage")
    break_even_price: float = Field(..., description="Break-even price")
    cost_breakdown: Dict[str, float] = Field(..., description="Cost breakdown")
    recommendations: List[str] = Field(..., description="Recommendations based on margin")


class MarketAnalysisRequest(BaseModel):
    """Request schema for market analysis"""
    niche: str = Field(..., description="Niche to analyze")
    keywords: List[str] = Field(..., description="Keywords to analyze")
    time_period_days: int = Field(30, ge=1, le=365, description="Time period for analysis")


class MarketAnalysisResponse(BaseModel):
    """Response schema for market analysis"""
    niche: str
    keywords: List[str]
    time_period_days: int
    total_products_analyzed: int = Field(..., description="Total products analyzed")
    price_trends: Dict[str, Any] = Field(..., description="Price trend analysis")
    demand_patterns: Dict[str, Any] = Field(..., description="Demand pattern analysis")
    competition_analysis: Dict[str, Any] = Field(..., description="Competition analysis")
    seasonal_patterns: Dict[str, Any] = Field(..., description="Seasonal pattern analysis")
    recommendations: List[str] = Field(..., description="Market recommendations")


class ProductResearchRequest(BaseModel):
    """Request schema for product research"""
    product_name: str = Field(..., description="Product name to research")
    category: str = Field(..., description="Product category")
    marketplaces: List[str] = Field(..., description="Marketplaces to search")


class ProductResearchResponse(BaseModel):
    """Response schema for product research"""
    product_name: str
    category: str
    marketplaces_searched: List[str]
    total_results: int = Field(..., description="Total results found")
    price_analysis: Dict[str, Any] = Field(..., description="Price analysis")
    competition_analysis: Dict[str, Any] = Field(..., description="Competition analysis")
    trend_analysis: Dict[str, Any] = Field(..., description="Trend analysis")
    recommendations: List[str] = Field(..., description="Product recommendations")


class BeginnerGuideRequest(BaseModel):
    """Request schema for beginner guide"""
    experience_level: ExperienceLevel = Field(..., description="Experience level")
    interests: List[str] = Field(..., description="Areas of interest")
    budget: float = Field(..., gt=0, description="Available budget")


class BeginnerGuideResponse(BaseModel):
    """Response schema for beginner guide"""
    experience_level: str
    interests: List[str]
    budget: float
    guide_sections: List[Dict[str, Any]] = Field(..., description="Guide sections")
    recommended_actions: List[str] = Field(..., description="Recommended actions")
    resources: List[Dict[str, str]] = Field(..., description="Helpful resources")
    timeline: Dict[str, str] = Field(..., description="Recommended timeline")
