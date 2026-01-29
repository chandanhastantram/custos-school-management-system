"""
CUSTOS Learning Schemas Init
"""

from app.learning.schemas.daily_loops import (
    MasteryLevel,
    DailySessionCreate,
    DailySessionResponse,
    DailySessionWithDetails,
    DailySessionWithQuestions,
    AttemptSubmit,
    AttemptBulkSubmit,
    AttemptResponse,
    AttemptWithFeedback,
    StudentMasteryResponse,
    MasteryWithDetails,
    StudentMasterySummary,
    StrongWeakQuestion,
    StrongWeakAnalysis,
    QuestionOption,
    QuestionForAttempt,
    TodaySessionInfo,
    DailyLoopStats,
)

__all__ = [
    "MasteryLevel",
    "DailySessionCreate",
    "DailySessionResponse",
    "DailySessionWithDetails",
    "DailySessionWithQuestions",
    "AttemptSubmit",
    "AttemptBulkSubmit",
    "AttemptResponse",
    "AttemptWithFeedback",
    "StudentMasteryResponse",
    "MasteryWithDetails",
    "StudentMasterySummary",
    "StrongWeakQuestion",
    "StrongWeakAnalysis",
    "QuestionOption",
    "QuestionForAttempt",
    "TodaySessionInfo",
    "DailyLoopStats",
]
