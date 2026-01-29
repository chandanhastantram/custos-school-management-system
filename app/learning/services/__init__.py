"""
CUSTOS Learning Services Init
"""

from app.learning.services.daily_loop_service import DailyLoopService
from app.learning.services.weekly_test_service import WeeklyTestService

__all__ = [
    "DailyLoopService",
    "WeeklyTestService",
]
