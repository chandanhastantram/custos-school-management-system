"""
CUSTOS JWT Authentication Module

JWT token creation and validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from uuid import UUID

import jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str  # User ID
    tenant_id: str
    email: str
    roles: list[str]
    permissions: list[str]
    type: str  # access or refresh
    iat: datetime
    exp: datetime
    jti: Optional[str] = None  # Token ID for revocation


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    roles: list[str],
    permissions: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token.
    
    Args:
        user_id: User's UUID
        tenant_id: Tenant's UUID
        email: User's email
        roles: List of role codes
        permissions: List of permission codes
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    user_id: UUID,
    tenant_id: UUID,
    token_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token.
    
    Args:
        user_id: User's UUID
        tenant_id: Tenant's UUID
        token_id: Unique token ID for revocation
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT refresh token string
    """
    from app.core.security import generate_token
    
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "jti": token_id or generate_token(16),
        "iat": now,
        "exp": expire,
    }
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_pair(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    roles: list[str],
    permissions: list[str],
) -> TokenPair:
    """
    Create access and refresh token pair.
    
    Args:
        user_id: User's UUID
        tenant_id: Tenant's UUID
        email: User's email
        roles: List of role codes
        permissions: List of permission codes
    
    Returns:
        TokenPair with access and refresh tokens
    """
    access_token = create_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        email=email,
        roles=roles,
        permissions=permissions,
    )
    
    refresh_token = create_refresh_token(
        user_id=user_id,
        tenant_id=tenant_id,
    )
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def verify_access_token(token: str) -> Optional[TokenPayload]:
    """
    Verify access token and return payload.
    
    Args:
        token: JWT access token
    
    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            return None
        
        return TokenPayload(
            sub=payload["sub"],
            tenant_id=payload["tenant_id"],
            email=payload["email"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
            type=payload["type"],
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Verify refresh token and return payload.
    
    Args:
        token: JWT refresh token
    
    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        
        if payload.get("type") != "refresh":
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
