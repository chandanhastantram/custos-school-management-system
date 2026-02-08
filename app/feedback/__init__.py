"""
CUSTOS Feedback & Surveys Module

Survey management for Course, Faculty, and General feedback.
"""

from app.feedback.models import (
    Survey,
    SurveyQuestion,
    SurveyResponse,
    SurveyAnswer,
    SurveyTemplate,
    SurveyType,
    SurveyStatus,
    QuestionType,
    ResponseStatus,
)
from app.feedback.service import FeedbackService
from app.feedback.router import router

__all__ = [
    # Models
    "Survey",
    "SurveyQuestion",
    "SurveyResponse",
    "SurveyAnswer",
    "SurveyTemplate",
    # Enums
    "SurveyType",
    "SurveyStatus",
    "QuestionType",
    "ResponseStatus",
    # Service
    "FeedbackService",
    # Router
    "router",
]
