"""Pydantic схемы для подписок и биллинга"""

from pydantic import BaseModel, Field
from enum import Enum

from app.models.subscription import SubscriptionTier, PaymentStatus

class SubscriptionTierSchema(str, Enum):
    """Схема уровней подписки"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class PaymentStatusSchema(str, Enum):
    """Схема статусов платежей"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class SubscriptionBase(BaseModel):
    """Базовая схема подписки"""
    tier: SubscriptionTierSchema
    status: str = "active"
    auto_renew: bool = True

class SubscriptionCreate(SubscriptionBase):
    """Схема создания подписки"""
    user_id: str
    end_date: Optional[datetime] = None

class SubscriptionUpdate(BaseModel):
    """Схема обновления подписки"""
    tier: Optional[SubscriptionTierSchema] = None
    status: Optional[str] = None
    auto_renew: Optional[bool] = None
    end_date: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    """Схема ответа подписки"""
    id: str
    user_id: str
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    days_remaining: int
    is_active: bool

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    """Базовая схема платежа"""
    amount: float
    currency: str = "USD"
    payment_method: str
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    """Схема создания платежа"""
    user_id: str
    subscription_id: Optional[str] = None

class PaymentUpdate(BaseModel):
    """Схема обновления платежа"""
    status: Optional[PaymentStatusSchema] = None
    external_id: Optional[str] = None

class PaymentResponse(PaymentBase):
    """Схема ответа платежа"""
    id: str
    user_id: str
    subscription_id: Optional[str]
    status: PaymentStatusSchema
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CashbackBase(BaseModel):
    """Базовая схема кэшбека"""
    amount: float
    percentage: float
    source: str
    description: Optional[str] = None

class CashbackCreate(CashbackBase):
    """Схема создания кэшбека"""
    user_id: str

class CashbackResponse(CashbackBase):
    """Схема ответа кэшбека"""
    id: str
    user_id: str
    status: str
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True

class ReferralBase(BaseModel):
    """Базовая схема реферала"""
    referred_id: str
    reward_amount: float = 0.0

class ReferralCreate(ReferralBase):
    """Схема создания реферала"""
    referrer_id: str

class ReferralResponse(ReferralBase):
    """Схема ответа реферала"""
    id: str
    referrer_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class SubscriptionPlanBase(BaseModel):
    """Базовая схема тарифного плана"""
    name: str
    tier: SubscriptionTierSchema
    price_monthly: float
    price_yearly: float
    features: List[str] = []
    limits: Dict[str, Any] = {}

class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Схема создания тарифного плана"""
    pass

class SubscriptionPlanUpdate(BaseModel):
    """Схема обновления тарифного плана"""
    name: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    features: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Схема ответа тарифного плана"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BillingSummary(BaseModel):
    """Схема сводки по биллингу"""
    current_subscription: Optional[SubscriptionResponse]
    total_payments: float
    total_cashback: float
    available_cashback: float
    next_payment_date: Optional[datetime]
    referral_rewards: float

class PaymentIntentCreate(BaseModel):
    """Схема создания намерения платежа"""
    amount: float
    currency: str = "USD"
    subscription_tier: SubscriptionTierSchema
    payment_method: str = "stripe"

class PaymentIntentResponse(BaseModel):
    """Схема ответа намерения платежа"""
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str
