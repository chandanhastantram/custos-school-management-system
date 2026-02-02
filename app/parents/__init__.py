"""
CUSTOS Parent Portal Module

Parent-facing features for school communication and fee management.
"""

from app.parents.service import ParentPortalService, ParentService
from app.parents.router import router as parents_router

__all__ = [
    "ParentPortalService",
    "ParentService",
    "parents_router",
]
