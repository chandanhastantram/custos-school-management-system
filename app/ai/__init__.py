"""
CUSTOS AI Module

AI-powered features: lesson plans, question generation, doubt solving, OCR.
"""

from app.ai.service import AIService
from app.ai.lesson_plan_generator import AILessonPlanService
from app.ai.question_gen_service import AIQuestionGenService
from app.ai.models import (
    AILessonPlanJob, 
    AIJobStatus,
    AIQuestionGenJob,
    QuestionGenDifficulty,
    QuestionGenType,
)
from app.ai.ocr_service import OCRService
from app.ai.ocr_models import OCRJob, OCRParsedResult, ExamType, OCRJobStatus
from app.ai.quota_manager import AIQuotaManager, SubscriptionTier, TIER_AI_LIMITS

__all__ = [
    "AIService",
    "AILessonPlanService",
    "AIQuestionGenService",
    "AILessonPlanJob",
    "AIJobStatus",
    "AIQuestionGenJob",
    "QuestionGenDifficulty",
    "QuestionGenType",
    "OCRService",
    "OCRJob",
    "OCRParsedResult",
    "ExamType",
    "OCRJobStatus",
    "AIQuotaManager",
    "SubscriptionTier",
    "TIER_AI_LIMITS",
]

