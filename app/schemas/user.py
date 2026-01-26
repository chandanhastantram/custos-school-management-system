"""
CUSTOS User Schemas

Pydantic schemas for user management.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserStatus, Gender


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    role_codes: List[str] = Field(default_factory=list)
    
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None
    notification_settings: Optional[dict] = None


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    tenant_id: UUID
    status: UserStatus
    
    avatar_url: Optional[str] = None
    gender: Optional[Gender] = None
    
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    
    roles: List["RoleResponse"] = []
    
    points: int
    level: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema."""
    permission_ids: List[UUID] = Field(default_factory=list)
    hierarchy_level: int = 0


class RoleResponse(RoleBase):
    """Role response schema."""
    id: UUID
    is_system: bool
    is_active: bool
    hierarchy_level: int
    permissions: List["PermissionResponse"] = []
    
    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """Permission response schema."""
    id: UUID
    name: str
    code: str
    category: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class StudentProfileCreate(BaseModel):
    """Student profile creation."""
    admission_number: str
    admission_date: Optional[date] = None
    class_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    roll_number: Optional[str] = None
    
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[EmailStr] = None
    guardian_relation: Optional[str] = None
    
    blood_group: Optional[str] = None
    uses_transport: bool = False


class StudentProfileResponse(StudentProfileCreate):
    """Student profile response."""
    id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True


class TeacherProfileCreate(BaseModel):
    """Teacher profile creation."""
    employee_id: str
    department: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None


class TeacherProfileResponse(TeacherProfileCreate):
    """Teacher profile response."""
    id: UUID
    user_id: UUID
    is_class_teacher: bool
    
    class Config:
        from_attributes = True


# Update forward references
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
