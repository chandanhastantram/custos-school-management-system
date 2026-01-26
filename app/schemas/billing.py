"""
CUSTOS Billing Schemas
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.models.billing import PlanType, SubscriptionStatus, BillingCycle


class PlanResponse(BaseModel):
    id: UUID
    name: str
    code: str
    plan_type: PlanType
    description: Optional[str] = None
    
    price_monthly: float
    price_yearly: float
    currency: str
    
    max_students: int
    max_teachers: int
    max_admins: int
    max_storage_gb: int
    ai_tokens_monthly: int
    
    features: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    plan_id: UUID
    billing_cycle: BillingCycle = BillingCycle.MONTHLY


class SubscriptionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    
    start_date: date
    end_date: date
    trial_end_date: Optional[date] = None
    
    next_billing_date: Optional[date] = None
    amount: float
    auto_renew: bool
    
    plan: PlanResponse
    
    class Config:
        from_attributes = True


class UsageLimitResponse(BaseModel):
    tenant_id: UUID
    
    current_students: int
    max_students: int
    
    current_teachers: int
    max_teachers: int
    
    current_storage_mb: int
    max_storage_mb: int
    
    current_ai_tokens: int
    max_ai_tokens: int
    
    is_within_limits: bool
