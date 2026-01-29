"""
CUSTOS Learning Repositories Init
"""

from app.learning.repositories.daily_loop_repo import DailyLoopRepository
from app.learning.repositories.weekly_test_repo import WeeklyTestRepository
from app.learning.repositories.lesson_eval_repo import LessonEvaluationRepository

__all__ = [
    "DailyLoopRepository",
    "WeeklyTestRepository",
    "LessonEvaluationRepository",
]
