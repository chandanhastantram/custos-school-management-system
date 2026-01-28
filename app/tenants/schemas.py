"""
CUSTOS Tenant Schemas

Tenant request/response schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.tenants.models import TenantType, TenantStatus


class TenantCreate(BaseModel):
    """Create new tenant (school registration)."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    type: TenantType = TenantType.SCHOOL
    
    email: EmailStr
    phone: Optional[str] = None
    website: Optional[str] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    
    timezone: str = "Asia/Kolkata"


class TenantUpdate(BaseModel):
    """Update tenant."""
    name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    
    logo: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    
    timezone: Optional[str] = None


class TenantResponse(BaseModel):
    """Tenant response."""
    id: UUID
    name: str
    slug: str
    type: str
    
    email: str
    phone: Optional[str]
    website: Optional[str]
    
    city: Optional[str]
    state: Optional[str]
    country: str
    
    logo: Optional[str]
    primary_color: str
    
    status: str
    is_verified: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Tenant statistics."""
    tenant_id: UUID
    student_count: int
    teacher_count: int
    question_count: int
    assignment_count: int
    
    class Config:
        from_attributes = True


class TenantPublicInfo(BaseModel):
    """Public tenant info (for login page)."""
    exists: bool
    id: Optional[UUID] = None
    name: Optional[str] = None
    logo: Optional[str] = None
    primary_color: Optional[str] = None
