"""
CUSTOS Academic Schemas

Pydantic schemas for academic entities.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.academic import SyllabusStatus, TopicStatus, LessonStatus


class ClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    grade_level: int = Field(..., ge=1, le=12)
    description: Optional[str] = None


class ClassCreate(ClassBase):
    academic_year_id: UUID
    display_order: int = 0


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ClassResponse(ClassBase):
    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    display_order: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    code: str = Field(..., min_length=1, max_length=10)
    capacity: int = Field(default=40, ge=1)
    room_number: Optional[str] = None


class SectionCreate(SectionBase):
    class_id: UUID
    class_teacher_id: Optional[UUID] = None


class SectionResponse(SectionBase):
    id: UUID
    tenant_id: UUID
    class_id: UUID
    class_teacher_id: Optional[UUID] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    category: Optional[str] = None


class SubjectCreate(SubjectBase):
    is_mandatory: bool = True
    credits: int = 1
    color: Optional[str] = None
    icon: Optional[str] = None


class SubjectResponse(SubjectBase):
    id: UUID
    tenant_id: UUID
    is_mandatory: bool
    is_active: bool
    credits: int
    color: Optional[str] = None
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True


class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    order: int = 0
    estimated_hours: float = 1.0


class TopicCreate(TopicBase):
    syllabus_id: UUID
    parent_topic_id: Optional[UUID] = None
    learning_objectives: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class TopicResponse(TopicBase):
    id: UUID
    tenant_id: UUID
    syllabus_id: UUID
    parent_topic_id: Optional[UUID] = None
    status: TopicStatus
    completed_at: Optional[datetime] = None
    learning_objectives: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class SyllabusBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    total_hours: int = 0


class SyllabusCreate(SyllabusBase):
    class_id: UUID
    subject_id: UUID
    academic_year_id: UUID


class SyllabusResponse(SyllabusBase):
    id: UUID
    tenant_id: UUID
    class_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    status: SyllabusStatus
    completion_percentage: float
    topics: List[TopicResponse] = []
    
    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(default=45, ge=15)


class LessonCreate(LessonBase):
    topic_id: UUID
    objectives: Optional[List[str]] = None
    content: Optional[dict] = None
    resources: Optional[List[dict]] = None
    activities: Optional[List[dict]] = None
    homework: Optional[str] = None
    scheduled_date: Optional[date] = None


class LessonResponse(LessonBase):
    id: UUID
    tenant_id: UUID
    topic_id: UUID
    teacher_id: UUID
    status: LessonStatus
    objectives: Optional[List[str]] = None
    content: Optional[dict] = None
    resources: Optional[List[dict]] = None
    activities: Optional[List[dict]] = None
    homework: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    is_ai_generated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AcademicYearBase(BaseModel):
    name: str
    start_date: date
    end_date: date


class AcademicYearCreate(AcademicYearBase):
    is_current: bool = False


class AcademicYearResponse(AcademicYearBase):
    id: UUID
    tenant_id: UUID
    is_current: bool
    is_active: bool
    
    class Config:
        from_attributes = True
