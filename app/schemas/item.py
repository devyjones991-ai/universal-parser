"""
Pydantic schemas for item management
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ItemBase(BaseModel):
    """Base item schema"""
    item_id: str = Field(..., description="Item ID on marketplace")
    marketplace: str = Field(..., description="Marketplace code")
    name: str = Field(..., description="Item name")
    brand: Optional[str] = Field(None, description="Item brand")
    category: Optional[str] = Field(None, description="Item category")
    url: Optional[str] = Field(None, description="Item URL")
    sku: Optional[str] = Field(None, description="Item SKU")


class ItemCreate(ItemBase):
    """Schema for creating new item"""
    tracking_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ItemUpdate(BaseModel):
    """Schema for updating item"""
    name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    tracking_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item response"""
    id: int
    user_id: int
    current_price: Optional[float] = None
    current_stock: Optional[int] = None
    current_rating: Optional[float] = None
    current_reviews_count: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_available: bool = True
    created_at: datetime
    last_updated: datetime
    last_checked: Optional[datetime] = None
    tracking_settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    """Schema for price history response"""
    id: int
    user_id: int
    tracked_item_id: int
    price: float
    old_price: Optional[float] = None
    discount_percent: Optional[float] = None
    stock: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    source: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ItemStatsResponse(BaseModel):
    """Schema for item statistics"""
    total_items: int
    active_items: int
    available_items: int
    avg_price: Optional[float] = None
    price_changes_24h: int
    new_items_24h: int
    marketplaces: Dict[str, int] = Field(default_factory=dict)
