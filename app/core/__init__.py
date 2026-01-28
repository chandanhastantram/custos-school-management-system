"""
CUSTOS Core Module

Cross-cutting concerns: configuration, database, security, exceptions.
"""

from app.core.config import settings
from app.core.database import get_db, engine
from app.core.exceptions import CustosException
from app.core.base_model import BaseModel, TenantBaseModel

__all__ = [
    "settings",
    "get_db",
    "engine",
    "CustosException",
    "BaseModel",
    "TenantBaseModel",
]
