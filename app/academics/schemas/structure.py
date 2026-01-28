"""
CUSTOS Academic Structure Schemas
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class AcademicYearCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearResponse(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    
    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    academic_year_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    grade_level: int = Field(..., ge=1, le=12)
    description: Optional[str] = None


class ClassResponse(BaseModel):
    id: UUID
    name: str
    code: str
    grade_level: int
    is_active: bool
    
    class Config:
        from_attributes = True


class SectionCreate(BaseModel):
    class_id: UUID
    name: str = Field(..., min_length=1, max_length=20)
    code: str
    capacity: int = 40
    room_number: Optional[str] = None
    class_teacher_id: Optional[UUID] = None


class SectionResponse(BaseModel):
    id: UUID
    name: str
    code: str
    capacity: int
    room_number: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True
