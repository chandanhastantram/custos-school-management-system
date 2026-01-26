"""
CUSTOS Tenant Schemas

Pydantic schemas for tenant management.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, HttpUrl

from app.models.tenant import TenantStatus, TenantType


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    type: TenantType = TenantType.SCHOOL


class TenantCreate(TenantBase):
    """Tenant creation schema."""
    slug: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-z0-9-]+$")
    
    # Admin user
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1)
    admin_last_name: str = Field(..., min_length=1)


class TenantUpdate(BaseModel):
    """Tenant update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    
    timezone: Optional[str] = None
    academic_year_start_month: Optional[int] = Field(None, ge=1, le=12)
    
    settings: Optional[dict] = None


class TenantResponse(TenantBase):
    """Tenant response schema."""
    id: UUID
    slug: str
    status: TenantStatus
    is_verified: bool
    
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    timezone: str
    
    trial_ends_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    items: List[TenantResponse]
    total: int
    page: int
    size: int
    pages: int


class TenantStats(BaseModel):
    """Tenant statistics."""
    total_students: int
    total_teachers: int
    total_classes: int
    total_sections: int
    total_subjects: int
    storage_used_mb: int
    ai_tokens_used: int
