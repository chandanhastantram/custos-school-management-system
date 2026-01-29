"""
CUSTOS AI Module

AI-powered features: lesson plans, question generation, doubt solving.
"""

from app.ai.service import AIService
from app.ai.lesson_plan_generator import AILessonPlanService
from app.ai.models import AILessonPlanJob, AIJobStatus

__all__ = [
    "AIService",
    "AILessonPlanService",
    "AILessonPlanJob",
    "AIJobStatus",
]
