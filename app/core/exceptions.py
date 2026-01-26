"""
CUSTOS Exceptions Module

Custom exception classes and exception handlers for the application.
"""

from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class CustosException(Exception):
    """Base exception for all CUSTOS errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "CUSTOS_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CustosException):
    """Authentication failed."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class AuthorizationError(CustosException):
    """User lacks required permissions."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        code: str = "FORBIDDEN",
        required_permission: Optional[str] = None,
    ):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, code, details)


class TenantError(CustosException):
    """Tenant-related error."""
    
    def __init__(
        self,
        message: str = "Tenant error",
        code: str = "TENANT_ERROR",
        tenant_id: Optional[str] = None,
    ):
        details = {}
        if tenant_id:
            details["tenant_id"] = tenant_id
        super().__init__(message, code, details)


class TenantNotFoundError(TenantError):
    """Tenant not found."""
    
    def __init__(self, tenant_id: str):
        super().__init__(
            message=f"Tenant not found: {tenant_id}",
            code="TENANT_NOT_FOUND",
            tenant_id=tenant_id,
        )


class TenantSuspendedError(TenantError):
    """Tenant is suspended."""
    
    def __init__(self, tenant_id: str):
        super().__init__(
            message="Tenant account is suspended",
            code="TENANT_SUSPENDED",
            tenant_id=tenant_id,
        )


class ResourceNotFoundError(CustosException):
    """Requested resource not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
    ):
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ValidationError(CustosException):
    """Input validation error."""
    
    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[list[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"errors": errors or []},
        )


class DuplicateError(CustosException):
    """Duplicate resource error."""
    
    def __init__(
        self,
        resource_type: str,
        field: str,
        value: str,
    ):
        super().__init__(
            message=f"{resource_type} with {field}='{value}' already exists",
            code="DUPLICATE_ERROR",
            details={"resource_type": resource_type, "field": field, "value": value},
        )


class RateLimitError(CustosException):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)


class QuotaExceededError(CustosException):
    """Resource quota exceeded."""
    
    def __init__(
        self,
        resource: str,
        limit: int,
        current: int,
    ):
        super().__init__(
            message=f"{resource} quota exceeded. Limit: {limit}, Current: {current}",
            code="QUOTA_EXCEEDED",
            details={"resource": resource, "limit": limit, "current": current},
        )


class SubscriptionError(CustosException):
    """Subscription-related error."""
    
    def __init__(
        self,
        message: str = "Subscription error",
        code: str = "SUBSCRIPTION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)


class SubscriptionRequiredError(SubscriptionError):
    """Feature requires active subscription."""
    
    def __init__(self, feature: str):
        super().__init__(
            message=f"Active subscription required for: {feature}",
            code="SUBSCRIPTION_REQUIRED",
            details={"feature": feature},
        )


class PlanLimitError(SubscriptionError):
    """Plan limit reached."""
    
    def __init__(
        self,
        feature: str,
        current_plan: str,
        required_plan: Optional[str] = None,
    ):
        message = f"Plan limit reached for: {feature}"
        if required_plan:
            message += f". Upgrade to {required_plan} for more."
        super().__init__(
            message=message,
            code="PLAN_LIMIT",
            details={
                "feature": feature,
                "current_plan": current_plan,
                "required_plan": required_plan,
            },
        )


class AIServiceError(CustosException):
    """AI service error."""
    
    def __init__(
        self,
        message: str = "AI service error",
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if provider:
            error_details["provider"] = provider
        super().__init__(message, "AI_ERROR", error_details)


class AITokenLimitError(AIServiceError):
    """AI token limit exceeded."""
    
    def __init__(
        self,
        limit: int,
        used: int,
        provider: str = "openai",
    ):
        super().__init__(
            message=f"Monthly AI token limit exceeded. Used: {used}, Limit: {limit}",
            provider=provider,
            details={"limit": limit, "used": used},
        )


class StorageError(CustosException):
    """File storage error."""
    
    def __init__(
        self,
        message: str = "Storage error",
        file_name: Optional[str] = None,
    ):
        details = {}
        if file_name:
            details["file_name"] = file_name
        super().__init__(message, "STORAGE_ERROR", details)


class ExternalServiceError(CustosException):
    """External service integration error."""
    
    def __init__(
        self,
        service: str,
        message: str = "External service error",
        status_code: Optional[int] = None,
    ):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code},
        )


# HTTP Exception factories
def http_400(message: str = "Bad request", **kwargs) -> HTTPException:
    """Create 400 Bad Request exception."""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"message": message, **kwargs},
    )


def http_401(message: str = "Unauthorized", **kwargs) -> HTTPException:
    """Create 401 Unauthorized exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": message, **kwargs},
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_403(message: str = "Forbidden", **kwargs) -> HTTPException:
    """Create 403 Forbidden exception."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"message": message, **kwargs},
    )


def http_404(message: str = "Not found", **kwargs) -> HTTPException:
    """Create 404 Not Found exception."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"message": message, **kwargs},
    )


def http_409(message: str = "Conflict", **kwargs) -> HTTPException:
    """Create 409 Conflict exception."""
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"message": message, **kwargs},
    )


def http_422(message: str = "Validation error", errors: list = None, **kwargs) -> HTTPException:
    """Create 422 Unprocessable Entity exception."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"message": message, "errors": errors or [], **kwargs},
    )


def http_429(message: str = "Too many requests", retry_after: int = 60, **kwargs) -> HTTPException:
    """Create 429 Too Many Requests exception."""
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={"message": message, **kwargs},
        headers={"Retry-After": str(retry_after)},
    )


def http_500(message: str = "Internal server error", **kwargs) -> HTTPException:
    """Create 500 Internal Server Error exception."""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": message, **kwargs},
    )


def http_503(message: str = "Service unavailable", **kwargs) -> HTTPException:
    """Create 503 Service Unavailable exception."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"message": message, **kwargs},
    )
