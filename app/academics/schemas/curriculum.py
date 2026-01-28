"""
CUSTOS Curriculum Schemas
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    category: Optional[str] = None
    is_mandatory: bool = True
    credits: float = 1.0
    color: Optional[str] = None


class SubjectResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str]
    category: Optional[str]
    is_mandatory: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class SyllabusCreate(BaseModel):
    class_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    total_hours: int = 0


class SyllabusResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    total_hours: int
    status: str
    
    class Config:
        from_attributes = True


class TopicCreate(BaseModel):
    syllabus_id: UUID
    parent_topic_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order: int = 0
    estimated_hours: float = 1.0
    learning_objectives: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class TopicResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    order: int
    status: str
    
    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    topic_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: int = 45
    objectives: Optional[List[str]] = None
    content: Optional[str] = None
    resources: Optional[List[str]] = None
    activities: Optional[List[str]] = None
    homework: Optional[str] = None
    scheduled_date: Optional[date] = None


class LessonResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    duration_minutes: int
    status: str
    scheduled_date: Optional[date]
    
    class Config:
        from_attributes = True
