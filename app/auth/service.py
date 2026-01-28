"""
CUSTOS Auth Service

Authentication business logic.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password, verify_password, create_token_pair,
    PasswordValidator,
)
from app.core.exceptions import (
    AuthenticationError, ValidationError, ResourceNotFoundError,
)
from app.auth.schemas import (
    LoginRequest, TokenResponse, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.auth.models import RefreshToken, PasswordResetToken, LoginAttempt


class AuthService:
    """Authentication service."""
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.password_validator = PasswordValidator()
    
    async def login(
        self,
        data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """Authenticate user and return tokens."""
        from app.users.models import User
        
        # Check for lockout
        if await self._is_locked_out(data.email, ip_address):
            raise AuthenticationError("Account temporarily locked due to too many failed attempts")
        
        # Find user
        query = select(User).where(
            User.tenant_id == self.tenant_id,
            User.email == data.email.lower(),
            User.is_deleted == False,
        )
        result = await self.session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(data.password, user.password_hash):
            await self._record_login_attempt(data.email, ip_address, user_agent, False)
            raise AuthenticationError("Invalid email or password")
        
        # Check user status
        if user.status.value != "active":
            raise AuthenticationError(f"Account is {user.status.value}")
        
        # Record successful login
        await self._record_login_attempt(data.email, ip_address, user_agent, True)
        
        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        
        # Get roles and permissions
        roles = [role.code for role in user.roles]
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.code)
        
        # Create tokens
        token_data = create_token_pair(
            user_id=user.id,
            tenant_id=self.tenant_id,
            email=user.email,
            roles=roles,
            permissions=list(permissions),
        )
        
        # Store refresh token
        await self._store_refresh_token(
            user_id=user.id,
            token=token_data["refresh_token"],
            ip_address=ip_address,
        )
        
        await self.session.commit()
        
        return TokenResponse(**token_data)
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token."""
        from app.users.models import User
        
        token_hash = self._hash_token(refresh_token)
        
        # Find valid refresh token
        query = select(RefreshToken).where(
            RefreshToken.tenant_id == self.tenant_id,
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.execute(query)
        stored_token = result.scalar_one_or_none()
        
        if not stored_token:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Get user
        user = await self.session.get(User, stored_token.user_id)
        if not user or user.is_deleted or user.status.value != "active":
            raise AuthenticationError("User account not available")
        
        # Revoke old token
        stored_token.is_revoked = True
        stored_token.revoked_at = datetime.now(timezone.utc)
        
        # Get roles and permissions
        roles = [role.code for role in user.roles]
        permissions = set()
        for role in user.roles:
            for perm in role.permissions:
                permissions.add(perm.code)
        
        # Create new tokens
        token_data = create_token_pair(
            user_id=user.id,
            tenant_id=self.tenant_id,
            email=user.email,
            roles=roles,
            permissions=list(permissions),
        )
        
        # Store new refresh token
        await self._store_refresh_token(
            user_id=user.id,
            token=token_data["refresh_token"],
        )
        
        await self.session.commit()
        
        return TokenResponse(**token_data)
    
    async def logout(self, user_id: UUID, refresh_token: Optional[str] = None) -> bool:
        """Logout user (revoke tokens)."""
        if refresh_token:
            token_hash = self._hash_token(refresh_token)
            query = select(RefreshToken).where(
                RefreshToken.tenant_id == self.tenant_id,
                RefreshToken.token_hash == token_hash,
            )
            result = await self.session.execute(query)
            stored_token = result.scalar_one_or_none()
            if stored_token:
                stored_token.is_revoked = True
                stored_token.revoked_at = datetime.now(timezone.utc)
        else:
            # Revoke all tokens for user
            query = select(RefreshToken).where(
                RefreshToken.tenant_id == self.tenant_id,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
            result = await self.session.execute(query)
            for token in result.scalars():
                token.is_revoked = True
                token.revoked_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        return True
    
    async def change_password(
        self,
        user_id: UUID,
        data: ChangePasswordRequest,
    ) -> bool:
        """Change user password."""
        from app.users.models import User
        
        user = await self.session.get(User, user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        
        # Validate new password
        is_valid, errors = self.password_validator.validate(data.new_password)
        if not is_valid:
            raise ValidationError("Password requirements not met", {"errors": errors})
        
        # Update password
        user.password_hash = hash_password(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        
        # Revoke all refresh tokens
        await self.logout(user_id)
        
        await self.session.commit()
        return True
    
    async def _store_refresh_token(
        self,
        user_id: UUID,
        token: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Store refresh token hash."""
        from datetime import timedelta
        from app.core.config import settings
        
        refresh_token = RefreshToken(
            tenant_id=self.tenant_id,
            user_id=user_id,
            token_hash=self._hash_token(token),
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.session.add(refresh_token)
    
    async def _record_login_attempt(
        self,
        email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        is_successful: bool,
    ) -> None:
        """Record login attempt."""
        attempt = LoginAttempt(
            tenant_id=self.tenant_id,
            email=email.lower(),
            ip_address=ip_address or "unknown",
            user_agent=user_agent,
            is_successful=is_successful,
            failure_reason=None if is_successful else "invalid_credentials",
        )
        self.session.add(attempt)
    
    async def _is_locked_out(self, email: str, ip_address: Optional[str]) -> bool:
        """Check if email/IP is locked out due to failed attempts."""
        from datetime import timedelta
        
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        
        query = select(LoginAttempt).where(
            LoginAttempt.tenant_id == self.tenant_id,
            LoginAttempt.email == email.lower(),
            LoginAttempt.is_successful == False,
            LoginAttempt.created_at > cutoff,
        )
        result = await self.session.execute(query)
        failed_attempts = len(result.scalars().all())
        
        return failed_attempts >= self.MAX_LOGIN_ATTEMPTS
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
