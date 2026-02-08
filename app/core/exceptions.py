"""
CUSTOS Exceptions

Custom exception classes for the application.
"""

from typing import Optional, Any


class CustosException(Exception):
    """Base exception for CUSTOS application."""
    
    def __init__(
        self,
        message: str,
        code: str = "ERROR",
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CustosException):
    """Authentication failed."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
        )


class AuthorizationError(CustosException):
    """Authorization/permission denied."""
    
    def __init__(self, message: str = "Permission denied", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
        )


class ResourceNotFoundError(CustosException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with ID '{identifier}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class DuplicateError(CustosException):
    """Duplicate resource error."""
    
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(
            message=f"{resource} with {field} '{value}' already exists",
            code="DUPLICATE",
            status_code=409,
            details={"resource": resource, "field": field, "value": value},
        )


class ValidationError(CustosException):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class TenantNotFoundError(CustosException):
    """Tenant not found."""
    
    def __init__(self, identifier: str):
        super().__init__(
            message=f"Tenant '{identifier}' not found",
            code="TENANT_NOT_FOUND",
            status_code=404,
            details={"identifier": identifier},
        )


class TenantSuspendedError(CustosException):
    """Tenant is suspended."""
    
    def __init__(self, tenant_id: str):
        super().__init__(
            message="This organization's account is suspended",
            code="TENANT_SUSPENDED",
            status_code=403,
            details={"tenant_id": tenant_id},
        )


class UsageLimitExceededError(CustosException):
    """Usage limit exceeded."""
    
    def __init__(self, limit_type: str, current: int, max_limit: int):
        super().__init__(
            message=f"{limit_type} limit exceeded ({current}/{max_limit})",
            code="USAGE_LIMIT_EXCEEDED",
            status_code=402,
            details={"limit_type": limit_type, "current": current, "max": max_limit},
        )


class RateLimitError(CustosException):
    """Rate limit exceeded."""
    
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after},
        )


class PaymentError(CustosException):
    """Payment processing error."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="PAYMENT_ERROR",
            status_code=400,
            details=details,
        )


class PermissionDeniedError(CustosException):
    """Permission denied error."""
    
    def __init__(self, message: str = "Permission denied", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=403,
            details=details,
        )


class NotFoundError(CustosException):
    """Generic not found error."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class BadRequestError(CustosException):
    """Bad request error."""
    
    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details,
        )


class ForbiddenError(CustosException):
    """Forbidden error."""
    
    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details,
        )

