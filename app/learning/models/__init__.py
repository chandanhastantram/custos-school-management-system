"""
CUSTOS Learning Models Init
"""

from app.learning.models.daily_loops import (
    DailyLoopSession,
    DailyLoopAttempt,
    StudentTopicMastery,
)
from app.learning.models.weekly_tests import (
    WeeklyTest,
    WeeklyTestQuestion,
    WeeklyTestResult,
    WeeklyStudentPerformance,
    WeeklyTestStatus,
    QuestionStrengthType,
)

__all__ = [
    # Daily Loops
    "DailyLoopSession",
    "DailyLoopAttempt",
    "StudentTopicMastery",
    # Weekly Tests
    "WeeklyTest",
    "WeeklyTestQuestion",
    "WeeklyTestResult",
    "WeeklyStudentPerformance",
    "WeeklyTestStatus",
    "QuestionStrengthType",
]
