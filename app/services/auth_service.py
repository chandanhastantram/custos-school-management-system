"""
CUSTOS Auth Service

Authentication business logic.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_token_pair, verify_refresh_token, TokenPair
from app.auth.password import hash_password, verify_password
from app.core.exceptions import AuthenticationError, ResourceNotFoundError
from app.models.user import User, UserStatus
from app.models.tenant import Tenant, TenantStatus
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo


class AuthService:
    """Authentication service."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def login(self, request: LoginRequest, tenant_id: UUID) -> LoginResponse:
        """
        Authenticate user and return tokens.
        
        Args:
            request: Login credentials
            tenant_id: Tenant UUID
        
        Returns:
            LoginResponse with tokens and user info
        
        Raises:
            AuthenticationError: If credentials are invalid
        """
        user_repo = UserRepository(self.session, tenant_id)
        user = await user_repo.get_by_email(request.email)
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        if user.is_locked:
            raise AuthenticationError("Account is temporarily locked")
        
        if not verify_password(request.password, user.password_hash):
            user.record_failed_login()
            await self.session.commit()
            raise AuthenticationError("Invalid email or password")
        
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"Account is {user.status.value}")
        
        # Get tenant
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE:
            raise AuthenticationError("Tenant is not active")
        
        # Record successful login
        user.record_login()
        await self.session.commit()
        
        # Get roles and permissions
        role_codes = [r.code for r in user.roles]
        permissions = list(user.get_all_permissions())
        
        # Create tokens
        token_pair = create_token_pair(
            user_id=user.id,
            tenant_id=tenant_id,
            email=user.email,
            roles=role_codes,
            permissions=permissions,
        )
        
        return LoginResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            user=UserInfo(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                roles=role_codes,
                tenant_id=tenant_id,
                tenant_name=tenant.name,
            ),
        )
    
    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New token pair
        
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])
        
        user_repo = UserRepository(self.session, tenant_id)
        user = await user_repo.get_by_id_with_roles(user_id)
        
        if not user or user.status != UserStatus.ACTIVE:
            raise AuthenticationError("User not found or inactive")
        
        role_codes = [r.code for r in user.roles]
        permissions = list(user.get_all_permissions())
        
        return create_token_pair(
            user_id=user.id,
            tenant_id=tenant_id,
            email=user.email,
            roles=role_codes,
            permissions=permissions,
        )
    
    async def change_password(
        self,
        user_id: UUID,
        tenant_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        user_repo = UserRepository(self.session, tenant_id)
        user = await user_repo.get_by_id(user_id)
        
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.session.commit()
        
        return True
    
    async def request_password_reset(self, email: str, tenant_id: UUID) -> Optional[str]:
        """
        Request password reset.
        
        Returns reset token (in production, this would be sent via email).
        """
        from app.core.security import generate_token, hash_token, get_expiry_time
        
        user_repo = UserRepository(self.session, tenant_id)
        user = await user_repo.get_by_email(email)
        
        if not user:
            # Don't reveal if user exists
            return None
        
        # Generate reset token
        plain_token = generate_token(48)
        hashed_token = hash_token(plain_token)
        
        user.reset_token_hash = hashed_token
        user.reset_token_expires_at = get_expiry_time(hours=24)
        await self.session.commit()
        
        return plain_token
    
    async def reset_password(
        self,
        token: str,
        new_password: str,
        tenant_id: UUID,
    ) -> bool:
        """Reset password using token."""
        from app.core.security import hash_token, is_expired
        
        hashed_token = hash_token(token)
        
        # Find user with this token
        from sqlalchemy import select
        query = select(User).where(
            User.tenant_id == tenant_id,
            User.reset_token_hash == hashed_token
        )
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid reset token")
        
        if not user.reset_token_expires_at or is_expired(user.reset_token_expires_at):
            raise AuthenticationError("Reset token has expired")
        
        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        await self.session.commit()
        
        return True
