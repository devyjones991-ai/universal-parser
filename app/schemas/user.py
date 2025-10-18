"""
Pydantic schemas for user management
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")


class UserCreate(UserBase):
    """Schema for creating new user"""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool = True
    is_verified: bool = False
    is_premium: bool = False
    subscription_tier: str = "free"
    subscription_expires: Optional[datetime] = None
    subscription_auto_renew: bool = False
    created_at: datetime
    last_activity: datetime
    last_login: Optional[datetime] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    """Schema for creating API key"""
    key_name: str = Field(..., description="Name for the API key")
    permissions: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response"""
    id: int
    user_id: int
    key_name: str
    permissions: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics"""
    total_items: int
    active_items: int
    total_alerts: int
    active_alerts: int
    subscription_tier: str
    subscription_expires: Optional[datetime] = None
    api_keys_count: int
    last_activity: datetime
