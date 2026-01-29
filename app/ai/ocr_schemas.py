"""
CUSTOS OCR Engine Schemas

Schemas for offline exam OCR processing.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


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


# ============================================
# Upload Request
# ============================================

class OCRUploadRequest(BaseModel):
    """Request metadata for OCR upload (file is multipart)."""
    exam_type: ExamType
    exam_id: UUID


# ============================================
# OCR Job Schemas
# ============================================

class OCRJobResponse(BaseModel):
    """OCR job response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    uploaded_by: UUID
    exam_type: ExamType
    exam_id: UUID
    status: OCRJobStatus
    image_path: str
    original_filename: Optional[str]
    ai_provider: str
    error_message: Optional[str]
    tokens_used: int
    results_extracted: int
    results_imported: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class OCRJobWithDetails(OCRJobResponse):
    """Job with additional details."""
    uploader_name: Optional[str] = None
    exam_title: Optional[str] = None
    input_snapshot: Optional[dict] = None
    output_snapshot: Optional[dict] = None


class OCRJobUploadResponse(BaseModel):
    """Response after uploading OCR image."""
    job_id: UUID
    status: OCRJobStatus
    message: str
    exam_type: ExamType
    exam_id: UUID


# ============================================
# Parsed Result Schemas
# ============================================

class OCRParsedResultResponse(BaseModel):
    """Individual parsed result from OCR."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    ocr_job_id: UUID
    student_identifier: str
    matched_student_id: Optional[UUID]
    total_marks: float
    marks_obtained: float
    attempted_questions: List[int]
    wrong_questions: List[int]
    percentage: float
    is_imported: bool
    imported_result_id: Optional[UUID]
    confidence_score: float
    created_at: datetime


class OCRParsedResultWithStudent(OCRParsedResultResponse):
    """Parsed result with matched student name."""
    student_name: Optional[str] = None
    roll_number: Optional[str] = None


class OCRJobResultsResponse(BaseModel):
    """All results for an OCR job."""
    job_id: UUID
    status: OCRJobStatus
    total_results: int
    imported_count: int
    pending_count: int
    results: List[OCRParsedResultWithStudent] = []


# ============================================
# Import Request
# ============================================

class ImportOCRResultsRequest(BaseModel):
    """Request to import OCR results into exam system."""
    result_ids: Optional[List[UUID]] = None  # If None, import all
    override_existing: bool = False


class ImportOCRResultsResponse(BaseModel):
    """Response after importing results."""
    job_id: UUID
    total_imported: int
    total_skipped: int
    errors: List[str] = []


# ============================================
# AI OCR Internal Schemas
# ============================================

class OCRStudentResult(BaseModel):
    """Single student result extracted by OCR."""
    student_identifier: str  # Name or roll number
    total_marks: float
    marks_obtained: float
    attempted_questions: List[int] = []
    wrong_questions: List[int] = []
    confidence: float = 0.8


class OCRExtractionResult(BaseModel):
    """Complete OCR extraction result."""
    success: bool
    exam_title: Optional[str] = None
    total_students: int = 0
    students: List[OCRStudentResult] = []
    raw_text: Optional[str] = None
    errors: List[str] = []


# ============================================
# Stats Schema
# ============================================

class OCRStats(BaseModel):
    """OCR processing statistics."""
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_results_extracted: int
    total_results_imported: int
