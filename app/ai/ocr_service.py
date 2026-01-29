"""
CUSTOS OCR Engine Service

Processes uploaded exam answer sheets and converts them to structured results.
"""

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError, ValidationError, UsageLimitExceededError
from app.ai.ocr_models import OCRJob, OCRParsedResult, ExamType, OCRJobStatus
from app.ai.ocr_schemas import (
    OCRUploadRequest,
    OCRJobUploadResponse,
    OCRJobResultsResponse,
    OCRParsedResultWithStudent,
    ImportOCRResultsRequest,
    ImportOCRResultsResponse,
    OCRExtractionResult,
    OCRStudentResult,
    OCRStats,
)
from app.ai.providers.openai import OpenAIProvider
from app.learning.models.weekly_tests import WeeklyTest, WeeklyTestResult
from app.learning.models.lesson_evaluation import LessonEvaluation, LessonEvaluationResult
from app.users.models import User


class OCRService:
    """
    OCR Engine Service.
    
    Workflow:
    1. Teacher uploads exam answer sheet image
    2. AI extracts marks and wrong questions
    3. System matches students
    4. Creates result records (WeeklyTestResult or LessonEvaluationResult)
    5. Updates mastery via existing services
    """
    
    # Supported image types
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.provider = OpenAIProvider()
    
    # ============================================
    # Upload & Create Job
    # ============================================
    
    async def upload_and_create_job(
        self,
        file: UploadFile,
        exam_type: ExamType,
        exam_id: UUID,
        uploaded_by: UUID,
    ) -> OCRJobUploadResponse:
        """
        Upload image and create OCR job.
        
        Steps:
        1. Validate file
        2. Check AI quota
        3. Save image
        4. Create job record
        5. Process immediately (or queue for later)
        """
        # 1. Validate file
        if file.content_type not in self.ALLOWED_TYPES:
            raise ValidationError(
                f"Unsupported file type: {file.content_type}. "
                f"Allowed: {', '.join(self.ALLOWED_TYPES)}"
            )
        
        # 2. Validate exam exists
        await self._validate_exam(exam_type, exam_id)
        
        # 3. Check AI quota
        await self._check_ai_quota()
        
        # 4. Save image
        image_path, original_filename = await self._save_image(file, exam_id)
        
        # 5. Create job
        job = OCRJob(
            tenant_id=self.tenant_id,
            uploaded_by=uploaded_by,
            exam_type=exam_type,
            exam_id=exam_id,
            image_path=image_path,
            original_filename=original_filename,
            status=OCRJobStatus.PENDING,
            ai_provider="openai",
            input_snapshot={
                "exam_type": exam_type.value,
                "exam_id": str(exam_id),
                "original_filename": original_filename,
                "file_size": file.size,
                "content_type": file.content_type,
            },
        )
        self.session.add(job)
        await self.session.flush()
        
        # 6. Process immediately
        await self.process_job(job.id)
        
        # Refresh to get updated status
        await self.session.refresh(job)
        
        return OCRJobUploadResponse(
            job_id=job.id,
            status=job.status,
            message="OCR processing completed" if job.status == OCRJobStatus.COMPLETED else "OCR processing started",
            exam_type=exam_type,
            exam_id=exam_id,
        )
    
    async def _save_image(
        self,
        file: UploadFile,
        exam_id: UUID,
    ) -> Tuple[str, str]:
        """Save uploaded image to filesystem."""
        # Create uploads directory
        upload_dir = Path(settings.upload_dir) / "ocr" / str(self.tenant_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ext = Path(file.filename).suffix or ".jpg"
        filename = f"{exam_id}_{timestamp}{ext}"
        
        file_path = upload_dir / filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return str(file_path), file.filename
    
    async def _validate_exam(self, exam_type: ExamType, exam_id: UUID) -> None:
        """Validate that the exam exists."""
        if exam_type == ExamType.WEEKLY:
            query = select(WeeklyTest).where(
                WeeklyTest.id == exam_id,
                WeeklyTest.tenant_id == self.tenant_id,
                WeeklyTest.deleted_at.is_(None),
            )
            result = await self.session.execute(query)
            if not result.scalar_one_or_none():
                raise ResourceNotFoundError("WeeklyTest", exam_id)
        
        elif exam_type == ExamType.LESSON:
            query = select(LessonEvaluation).where(
                LessonEvaluation.id == exam_id,
                LessonEvaluation.tenant_id == self.tenant_id,
                LessonEvaluation.deleted_at.is_(None),
            )
            result = await self.session.execute(query)
            if not result.scalar_one_or_none():
                raise ResourceNotFoundError("LessonEvaluation", exam_id)
    
    # ============================================
    # Process Job
    # ============================================
    
    async def process_job(self, job_id: UUID) -> OCRJob:
        """
        Process an OCR job.
        
        Steps:
        1. Load image
        2. Call AI OCR
        3. Parse results
        4. Store parsed results
        5. Update job status
        """
        job = await self.get_job(job_id)
        if not job:
            raise ResourceNotFoundError("OCRJob", job_id)
        
        if job.status not in [OCRJobStatus.PENDING, OCRJobStatus.FAILED]:
            return job  # Already processed or processing
        
        try:
            # Update status
            job.status = OCRJobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            await self.session.flush()
            
            # 1. Load image
            image_base64, image_type = self._load_image(job.image_path)
            
            # 2. Get exam context
            exam_context = await self._get_exam_context(job.exam_type, job.exam_id)
            
            # 3. Call AI OCR
            ocr_result = await self.provider.process_exam_ocr(
                image_base64=image_base64,
                image_type=image_type,
                exam_context=exam_context,
            )
            
            # Store raw output
            job.output_snapshot = ocr_result
            
            if not ocr_result.get("success", False):
                job.status = OCRJobStatus.FAILED
                job.error_message = "; ".join(ocr_result.get("errors", ["OCR failed"]))
                job.completed_at = datetime.utcnow()
                await self.session.flush()
                return job
            
            # 4. Parse and store results
            students = ocr_result.get("students", [])
            results_created = 0
            
            for student_data in students:
                # Calculate percentage
                total = float(student_data.get("total_marks", 0))
                obtained = float(student_data.get("marks_obtained", 0))
                percentage = (obtained / total * 100) if total > 0 else 0
                
                # Match student
                student_id = await self._match_student(
                    student_data.get("student_identifier", "")
                )
                
                # Create parsed result
                parsed = OCRParsedResult(
                    tenant_id=self.tenant_id,
                    ocr_job_id=job.id,
                    student_identifier=student_data.get("student_identifier", "Unknown"),
                    matched_student_id=student_id,
                    total_marks=total,
                    marks_obtained=obtained,
                    attempted_questions=student_data.get("attempted_questions", []),
                    wrong_questions=student_data.get("wrong_questions", []),
                    percentage=percentage,
                    confidence_score=float(student_data.get("confidence", 0.8)),
                )
                self.session.add(parsed)
                results_created += 1
            
            # 5. Update job
            job.status = OCRJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.results_extracted = results_created
            
            await self.session.flush()
            
            # 6. Increment AI usage
            await self._increment_ai_usage()
            
            return job
            
        except Exception as e:
            job.status = OCRJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await self.session.flush()
            raise
    
    def _load_image(self, image_path: str) -> Tuple[str, str]:
        """Load image and convert to base64."""
        path = Path(image_path)
        
        if not path.exists():
            raise ValidationError(f"Image file not found: {image_path}")
        
        with open(path, "rb") as f:
            image_data = f.read()
        
        # Determine type
        ext = path.suffix.lower()
        type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        image_type = type_map.get(ext, "image/jpeg")
        
        return base64.b64encode(image_data).decode("utf-8"), image_type
    
    async def _get_exam_context(
        self,
        exam_type: ExamType,
        exam_id: UUID,
    ) -> str:
        """Get exam context for OCR prompt."""
        if exam_type == ExamType.WEEKLY:
            query = select(WeeklyTest).where(WeeklyTest.id == exam_id)
            result = await self.session.execute(query)
            exam = result.scalar_one_or_none()
            if exam:
                return f"Exam: {exam.title}, Total Marks: {exam.total_marks}, Questions: {exam.total_questions}"
        
        elif exam_type == ExamType.LESSON:
            query = select(LessonEvaluation).where(LessonEvaluation.id == exam_id)
            result = await self.session.execute(query)
            exam = result.scalar_one_or_none()
            if exam:
                return f"Exam: {exam.title}, Total Marks: {exam.total_marks}, Questions: {exam.total_questions}"
        
        return ""
    
    async def _match_student(self, identifier: str) -> Optional[UUID]:
        """Try to match student identifier to a user."""
        if not identifier:
            return None
        
        identifier = identifier.strip()
        
        # Try matching by roll number or name
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        users = result.scalars().all()
        
        for user in users:
            # Check roll number (if stored in profile)
            if hasattr(user, 'student_profile') and user.student_profile:
                if user.student_profile.roll_number == identifier:
                    return user.id
            
            # Check name (case-insensitive partial match)
            if user.full_name and identifier.lower() in user.full_name.lower():
                return user.id
        
        return None
    
    # ============================================
    # Import Results
    # ============================================
    
    async def import_results(
        self,
        job_id: UUID,
        request: ImportOCRResultsRequest,
        imported_by: UUID,
    ) -> ImportOCRResultsResponse:
        """
        Import parsed OCR results into exam system.
        
        Creates WeeklyTestResult or LessonEvaluationResult records.
        """
        job = await self.get_job(job_id)
        if not job:
            raise ResourceNotFoundError("OCRJob", job_id)
        
        if job.status != OCRJobStatus.COMPLETED:
            raise ValidationError("Job is not completed")
        
        # Get parsed results
        parsed_results = await self._get_parsed_results(job_id)
        
        # Filter if specific IDs requested
        if request.result_ids:
            parsed_results = [r for r in parsed_results if r.id in request.result_ids]
        
        imported = 0
        skipped = 0
        errors = []
        
        for parsed in parsed_results:
            if parsed.is_imported and not request.override_existing:
                skipped += 1
                continue
            
            if not parsed.matched_student_id:
                errors.append(f"No student match for: {parsed.student_identifier}")
                skipped += 1
                continue
            
            try:
                result_id = await self._create_exam_result(
                    job=job,
                    parsed=parsed,
                    imported_by=imported_by,
                )
                
                parsed.is_imported = True
                parsed.imported_result_id = result_id
                imported += 1
                
            except Exception as e:
                errors.append(f"Error for {parsed.student_identifier}: {str(e)}")
                skipped += 1
        
        # Update job stats
        job.results_imported = imported
        await self.session.flush()
        
        return ImportOCRResultsResponse(
            job_id=job_id,
            total_imported=imported,
            total_skipped=skipped,
            errors=errors,
        )
    
    async def _create_exam_result(
        self,
        job: OCRJob,
        parsed: OCRParsedResult,
        imported_by: UUID,
    ) -> UUID:
        """Create the actual exam result record."""
        if job.exam_type == ExamType.WEEKLY:
            # Create WeeklyTestResult
            result = WeeklyTestResult(
                tenant_id=self.tenant_id,
                weekly_test_id=job.exam_id,
                student_id=parsed.matched_student_id,
                total_marks=parsed.total_marks,
                marks_obtained=parsed.marks_obtained,
                attempted_questions=parsed.attempted_questions,
                wrong_questions=parsed.wrong_questions,
                percentage=parsed.percentage,
                submitted_by=imported_by,
            )
            self.session.add(result)
            await self.session.flush()
            return result.id
        
        elif job.exam_type == ExamType.LESSON:
            # Create LessonEvaluationResult
            result = LessonEvaluationResult(
                tenant_id=self.tenant_id,
                lesson_evaluation_id=job.exam_id,
                student_id=parsed.matched_student_id,
                total_marks=parsed.total_marks,
                marks_obtained=parsed.marks_obtained,
                wrong_questions=parsed.wrong_questions,
                percentage=parsed.percentage,
                submitted_by=imported_by,
            )
            self.session.add(result)
            await self.session.flush()
            return result.id
        
        raise ValidationError(f"Unknown exam type: {job.exam_type}")
    
    # ============================================
    # Get Jobs & Results
    # ============================================
    
    async def get_job(self, job_id: UUID) -> Optional[OCRJob]:
        """Get OCR job by ID."""
        query = select(OCRJob).where(
            OCRJob.id == job_id,
            OCRJob.tenant_id == self.tenant_id,
            OCRJob.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_jobs(
        self,
        uploaded_by: Optional[UUID] = None,
        exam_type: Optional[ExamType] = None,
        status: Optional[OCRJobStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[OCRJob], int]:
        """List OCR jobs with filters."""
        query = select(OCRJob).where(
            OCRJob.tenant_id == self.tenant_id,
            OCRJob.deleted_at.is_(None),
        )
        
        if uploaded_by:
            query = query.where(OCRJob.uploaded_by == uploaded_by)
        if exam_type:
            query = query.where(OCRJob.exam_type == exam_type)
        if status:
            query = query.where(OCRJob.status == status)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0
        
        query = query.order_by(OCRJob.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def _get_parsed_results(
        self,
        job_id: UUID,
    ) -> List[OCRParsedResult]:
        """Get parsed results for a job."""
        query = select(OCRParsedResult).where(
            OCRParsedResult.ocr_job_id == job_id,
            OCRParsedResult.tenant_id == self.tenant_id,
            OCRParsedResult.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_job_results(
        self,
        job_id: UUID,
    ) -> OCRJobResultsResponse:
        """Get all results for an OCR job."""
        job = await self.get_job(job_id)
        if not job:
            raise ResourceNotFoundError("OCRJob", job_id)
        
        parsed_results = await self._get_parsed_results(job_id)
        
        results = [
            OCRParsedResultWithStudent(
                id=r.id,
                ocr_job_id=r.ocr_job_id,
                student_identifier=r.student_identifier,
                matched_student_id=r.matched_student_id,
                total_marks=r.total_marks,
                marks_obtained=r.marks_obtained,
                attempted_questions=r.attempted_questions,
                wrong_questions=r.wrong_questions,
                percentage=r.percentage,
                is_imported=r.is_imported,
                imported_result_id=r.imported_result_id,
                confidence_score=r.confidence_score,
                created_at=r.created_at,
            )
            for r in parsed_results
        ]
        
        imported_count = sum(1 for r in parsed_results if r.is_imported)
        
        return OCRJobResultsResponse(
            job_id=job_id,
            status=job.status,
            total_results=len(results),
            imported_count=imported_count,
            pending_count=len(results) - imported_count,
            results=results,
        )
    
    # ============================================
    # Stats
    # ============================================
    
    async def get_stats(self) -> OCRStats:
        """Get OCR processing statistics."""
        base_filter = [
            OCRJob.tenant_id == self.tenant_id,
            OCRJob.deleted_at.is_(None),
        ]
        
        total = await self.session.scalar(
            select(func.count(OCRJob.id)).where(*base_filter)
        ) or 0
        
        pending = await self.session.scalar(
            select(func.count(OCRJob.id)).where(
                *base_filter, OCRJob.status == OCRJobStatus.PENDING
            )
        ) or 0
        
        processing = await self.session.scalar(
            select(func.count(OCRJob.id)).where(
                *base_filter, OCRJob.status == OCRJobStatus.PROCESSING
            )
        ) or 0
        
        completed = await self.session.scalar(
            select(func.count(OCRJob.id)).where(
                *base_filter, OCRJob.status == OCRJobStatus.COMPLETED
            )
        ) or 0
        
        failed = await self.session.scalar(
            select(func.count(OCRJob.id)).where(
                *base_filter, OCRJob.status == OCRJobStatus.FAILED
            )
        ) or 0
        
        total_extracted = await self.session.scalar(
            select(func.sum(OCRJob.results_extracted)).where(*base_filter)
        ) or 0
        
        total_imported = await self.session.scalar(
            select(func.sum(OCRJob.results_imported)).where(*base_filter)
        ) or 0
        
        return OCRStats(
            total_jobs=total,
            pending_jobs=pending,
            processing_jobs=processing,
            completed_jobs=completed,
            failed_jobs=failed,
            total_results_extracted=total_extracted,
            total_results_imported=total_imported,
        )
    
    # ============================================
    # Cost Control
    # ============================================
    
    async def _check_ai_quota(self) -> None:
        """Check if tenant has AI credits."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            max_requests = 100  # Would get from subscription
            if usage.ai_requests_used >= max_requests:
                raise UsageLimitExceededError(
                    "AI requests", usage.ai_requests_used, max_requests
                )
    
    async def _increment_ai_usage(self) -> None:
        """Increment AI usage counter."""
        from app.billing.models import UsageLimit
        
        now = datetime.now()
        query = select(UsageLimit).where(
            UsageLimit.tenant_id == self.tenant_id,
            UsageLimit.year == now.year,
            UsageLimit.month == now.month,
        )
        result = await self.session.execute(query)
        usage = result.scalar_one_or_none()
        
        if usage:
            usage.ai_requests_used += 1
        else:
            usage = UsageLimit(
                tenant_id=self.tenant_id,
                year=now.year,
                month=now.month,
                ai_requests_used=1,
            )
            self.session.add(usage)
        
        await self.session.flush()
