"""
CUSTOS Governance, Compliance & Audit Module

Enterprise-grade audit trails and compliance management.

CORE PRINCIPLES:
1. IMMUTABLE AUDIT LOGS - Append-only, never update/delete
2. Role-based access to audit data
3. Inspection-ready exports
4. Works across ALL modules
"""

from app.governance.models import (
    AuditLog,
    DataAccessLog,
    ConsentRecord,
    InspectionExport,
    ActionType,
    EntityType,
    AccessType,
    SubjectType,
    ConsentType,
    InspectionScope,
    InspectionStatus,
)
from app.governance.service import GovernanceService
from app.governance.router import router as governance_router

__all__ = [
    # Models
    "AuditLog",
    "DataAccessLog",
    "ConsentRecord",
    "InspectionExport",
    # Enums
    "ActionType",
    "EntityType",
    "AccessType",
    "SubjectType",
    "ConsentType",
    "InspectionScope",
    "InspectionStatus",
    # Service
    "GovernanceService",
    # Router
    "governance_router",
]
