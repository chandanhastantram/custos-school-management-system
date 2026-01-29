"""
CUSTOS AI Module

AI-powered features: lesson plans, question generation, doubt solving, OCR.
"""

from app.ai.service import AIService
from app.ai.lesson_plan_generator import AILessonPlanService
from app.ai.models import AILessonPlanJob, AIJobStatus
from app.ai.ocr_service import OCRService
from app.ai.ocr_models import OCRJob, OCRParsedResult, ExamType, OCRJobStatus

__all__ = [
    "AIService",
    "AILessonPlanService",
    "AILessonPlanJob",
    "AIJobStatus",
    "OCRService",
    "OCRJob",
    "OCRParsedResult",
    "ExamType",
    "OCRJobStatus",
]
