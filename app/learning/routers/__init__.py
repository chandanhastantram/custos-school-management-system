"""
CUSTOS Learning Routers Init
"""

from app.learning.routers.daily_loops import router as daily_loops_router
from app.learning.routers.weekly_tests import router as weekly_tests_router

__all__ = [
    "daily_loops_router",
    "weekly_tests_router",
]
