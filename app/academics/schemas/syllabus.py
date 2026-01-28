"""
CUSTOS Syllabus Engine Schemas

Pydantic schemas for syllabus CRUD operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Board Schemas
# ============================================

class BoardBase(BaseModel):
    """Base schema for Board."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    language_code: str = "en"
    display_order: int = 0


class BoardCreate(BoardBase):
    """Schema for creating a Board."""
    pass


class BoardUpdate(BaseModel):
    """Schema for updating a Board."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    language_code: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class BoardResponse(BoardBase):
    """Schema for Board response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class BoardWithLevels(BoardResponse):
    """Board with class levels."""
    class_levels: List["ClassLevelResponse"] = []


# ============================================
# ClassLevel Schemas
# ============================================

class ClassLevelBase(BaseModel):
    """Base schema for ClassLevel."""
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    grade_number: int = Field(..., ge=1, le=12)
    display_order: int = 0


class ClassLevelCreate(ClassLevelBase):
    """Schema for creating a ClassLevel."""
    board_id: UUID


class ClassLevelUpdate(BaseModel):
    """Schema for updating a ClassLevel."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    grade_number: Optional[int] = Field(None, ge=1, le=12)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ClassLevelResponse(ClassLevelBase):
    """Schema for ClassLevel response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    board_id: UUID
    is_active: bool
    created_at: datetime


class ClassLevelWithSubjects(ClassLevelResponse):
    """ClassLevel with subjects."""
    subjects: List["SubjectResponse"] = []


# ============================================
# Subject Schemas
# ============================================

class SubjectBase(BaseModel):
    """Base schema for SyllabusSubject."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    category: Optional[str] = None
    is_mandatory: bool = True
    credits: float = 1.0
    periods_per_week: int = 5
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    display_order: int = 0


class SubjectCreate(SubjectBase):
    """Schema for creating a Subject."""
    class_level_id: UUID


class SubjectUpdate(BaseModel):
    """Schema for updating a Subject."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    category: Optional[str] = None
    is_mandatory: Optional[bool] = None
    credits: Optional[float] = None
    periods_per_week: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class SubjectResponse(SubjectBase):
    """Schema for Subject response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    class_level_id: UUID
    total_hours: int
    is_active: bool
    version: int
    created_at: datetime


class SubjectWithChapters(SubjectResponse):
    """Subject with chapters."""
    chapters: List["ChapterResponse"] = []


# ============================================
# Chapter Schemas
# ============================================

class ChapterBase(BaseModel):
    """Base schema for Chapter."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    order: int = 0
    learning_objectives: Optional[str] = None
    prerequisites: Optional[str] = None


class ChapterCreate(ChapterBase):
    """Schema for creating a Chapter."""
    subject_id: UUID


class ChapterUpdate(BaseModel):
    """Schema for updating a Chapter."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    order: Optional[int] = None
    learning_objectives: Optional[str] = None
    prerequisites: Optional[str] = None
    is_active: Optional[bool] = None


class ChapterResponse(ChapterBase):
    """Schema for Chapter response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    subject_id: UUID
    estimated_hours: float
    is_active: bool
    created_at: datetime


class ChapterWithTopics(ChapterResponse):
    """Chapter with topics."""
    topics: List["TopicResponse"] = []


# ============================================
# Topic Schemas
# ============================================

class TopicBase(BaseModel):
    """Base schema for SyllabusTopic."""
    name: str = Field(..., min_length=1, max_length=300)
    code: str = Field(..., min_length=1, max_length=30)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    order: int = 0
    estimated_hours: float = 1.0
    estimated_periods: int = 1
    learning_objectives: Optional[str] = None
    keywords: Optional[str] = None
    difficulty_level: int = Field(3, ge=1, le=5)
    importance_level: int = Field(3, ge=1, le=5)


class TopicCreate(TopicBase):
    """Schema for creating a Topic."""
    chapter_id: UUID


class TopicUpdate(BaseModel):
    """Schema for updating a Topic."""
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    code: Optional[str] = Field(None, min_length=1, max_length=30)
    description: Optional[str] = None
    name_vernacular: Optional[str] = None
    order: Optional[int] = None
    estimated_hours: Optional[float] = None
    estimated_periods: Optional[int] = None
    learning_objectives: Optional[str] = None
    keywords: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    importance_level: Optional[int] = Field(None, ge=1, le=5)
    is_active: Optional[bool] = None


class TopicResponse(TopicBase):
    """Schema for Topic response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    chapter_id: UUID
    is_active: bool
    created_at: datetime


class TopicWithWeightages(TopicResponse):
    """Topic with weightages."""
    weightages: List["TopicWeightageResponse"] = []


# ============================================
# TopicWeightage Schemas
# ============================================

class TopicWeightageBase(BaseModel):
    """Base schema for TopicWeightage."""
    exam_type: str = Field(..., min_length=1, max_length=50)
    weightage_percent: float = Field(0, ge=0, le=100)
    expected_marks: float = Field(0, ge=0)
    mcq_count: int = Field(0, ge=0)
    short_answer_count: int = Field(0, ge=0)
    long_answer_count: int = Field(0, ge=0)


class TopicWeightageCreate(TopicWeightageBase):
    """Schema for creating a TopicWeightage."""
    topic_id: UUID


class TopicWeightageUpdate(BaseModel):
    """Schema for updating a TopicWeightage."""
    weightage_percent: Optional[float] = Field(None, ge=0, le=100)
    expected_marks: Optional[float] = Field(None, ge=0)
    mcq_count: Optional[int] = Field(None, ge=0)
    short_answer_count: Optional[int] = Field(None, ge=0)
    long_answer_count: Optional[int] = Field(None, ge=0)


class TopicWeightageResponse(TopicWeightageBase):
    """Schema for TopicWeightage response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    topic_id: UUID
    created_at: datetime


# ============================================
# Bulk Operations
# ============================================

class BulkTopicCreate(BaseModel):
    """Schema for bulk topic creation."""
    chapter_id: UUID
    topics: List[TopicBase]


class ReorderRequest(BaseModel):
    """Schema for reordering items."""
    items: List[UUID]  # Ordered list of IDs


# ============================================
# Full Syllabus View
# ============================================

class FullSyllabusResponse(BaseModel):
    """Full syllabus tree structure."""
    board: BoardResponse
    class_levels: List[ClassLevelWithSubjects]


# Resolve forward references
BoardWithLevels.model_rebuild()
ClassLevelWithSubjects.model_rebuild()
SubjectWithChapters.model_rebuild()
ChapterWithTopics.model_rebuild()
TopicWithWeightages.model_rebuild()
