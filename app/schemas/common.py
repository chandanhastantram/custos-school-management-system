"""
CUSTOS Common Schemas

Shared response schemas.
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel


T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str = "Operation successful"


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    code: str
    details: Optional[dict] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "asc"


class SearchParams(BaseModel):
    """Search parameters."""
    query: Optional[str] = None
    filters: Optional[dict] = None


class BulkDeleteRequest(BaseModel):
    """Bulk delete request."""
    ids: List[str]


class BulkActionResponse(BaseModel):
    """Bulk action response."""
    success_count: int
    failure_count: int
    failures: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    uptime: float
