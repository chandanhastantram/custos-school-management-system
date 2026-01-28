"""
CUSTOS API Module

Router aggregation and versioning.
"""

from app.api.v1 import router as v1_router
from app.api.health import router as health_router

__all__ = [
    "v1_router",
    "health_router",
]
