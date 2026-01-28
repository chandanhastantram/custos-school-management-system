"""
CUSTOS User Schemas

User request/response schemas.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.users.models import UserStatus, Gender


class UserCreate(BaseModel):
    """Create user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    role_ids: List[UUID] = []


class UserUpdate(BaseModel):
    """Update user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    avatar: Optional[str] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    """User response."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar: Optional[str]
    status: str
    roles: List[str] = []
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class StudentCreate(BaseModel):
    """Create student."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    
    # Student-specific
    admission_number: str
    admission_date: Optional[date] = None
    section_id: Optional[UUID] = None
    roll_number: Optional[int] = None


class TeacherCreate(BaseModel):
    """Create teacher."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    
    # Teacher-specific
    employee_id: str
    joining_date: Optional[date] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    qualifications: Optional[List[str]] = None


class RoleResponse(BaseModel):
    """Role response."""
    id: UUID
    name: str
    code: str
    is_system: bool
    
    class Config:
        from_attributes = True
