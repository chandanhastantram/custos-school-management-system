"""
CUSTOS OCR Engine Models

Models for offline exam answer sheet OCR processing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class ExamType(str, Enum):
    """Type of exam being processed."""
    WEEKLY = "weekly"
    LESSON = "lesson"


class OCRJobStatus(str, Enum):
    """OCR job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRJob(TenantBaseModel):
    """
    OCR Job - Processes uploaded exam result images.
    
    Workflow:
    1. Teacher uploads answer sheet photo
    2. AI extracts marks and wrong questions
    3. System creates result records automatically
    
    Connects offline exams → digital learning engine.
    """
    __tablename__ = "ocr_jobs"
    
    __table_args__ = (
        Index("ix_ocr_job_tenant_teacher", "tenant_id", "uploaded_by"),
        Index("ix_ocr_job_status", "tenant_id", "status"),
        Index("ix_ocr_job_exam", "exam_type", "exam_id"),
    )
    
    # Who uploaded
    uploaded_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Exam linkage
    exam_type: Mapped[ExamType] = mapped_column(
        SQLEnum(ExamType),
        nullable=False,
    )
    
    exam_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,  # Can be weekly_test_id or lesson_evaluation_id
    )
    
    # Processing status
    status: Mapped[OCRJobStatus] = mapped_column(
        SQLEnum(OCRJobStatus),
        default=OCRJobStatus.PENDING,
        nullable=False,
    )
    
    # Image storage
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # AI provider used
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    
    # Input snapshot (original image metadata)
    input_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    
    # Output snapshot (AI raw response)
    output_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Token usage (for cost tracking)
    tokens_used: Mapped[int] = mapped_column(default=0)
    
    # Statistics
    results_extracted: Mapped[int] = mapped_column(Integer, default=0)
    results_imported: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    parsed_results: Mapped[List["OCRParsedResult"]] = relationship(
        "OCRParsedResult",
        back_populates="ocr_job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OCRParsedResult(TenantBaseModel):
    """
    OCR Parsed Result - Individual student result extracted from image.
    
    Contains raw extracted data before matching to actual student records.
    """
    __tablename__ = "ocr_parsed_results"
    
    __table_args__ = (
        Index("ix_ocr_result_job", "ocr_job_id"),
    )
    
    ocr_job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ocr_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Student identification (from OCR)
    student_identifier: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Could be roll_no, name, or student_id
    
    # Matched student (after lookup)
    matched_student_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Marks
    total_marks: Mapped[float] = mapped_column(Float, nullable=False)
    marks_obtained: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Question analysis  
    attempted_questions: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    wrong_questions: Mapped[List[int]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    
    # Computed
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Import status
    is_imported: Mapped[bool] = mapped_column(default=False)
    imported_result_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )  # ID of created WeeklyTestResult or LessonEvaluationResult
    
    # Confidence score from OCR
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationship
    ocr_job: Mapped["OCRJob"] = relationship(
        "OCRJob", back_populates="parsed_results"
    )
