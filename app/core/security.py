"""
CUSTOS Security Module

Security utilities including password hashing, token generation, and encryption.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from uuid import UUID

from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.password_hash_rounds,
)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to verify against
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def generate_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Token length in bytes
    
    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(length)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate numeric verification code (e.g., for 2FA).
    
    Args:
        length: Number of digits
    
    Returns:
        Numeric string code
    """
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))


def generate_api_key() -> str:
    """
    Generate API key with prefix.
    
    Returns:
        API key string (cst_...)
    """
    return f"cst_{secrets.token_urlsafe(32)}"


def hash_token(token: str) -> str:
    """
    Create hash of token for secure storage.
    
    Args:
        token: Token to hash
    
    Returns:
        SHA-256 hash of token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_password_reset_token() -> tuple[str, str]:
    """
    Generate password reset token pair.
    
    Returns:
        Tuple of (plain_token, hashed_token)
    """
    plain_token = generate_token(48)
    hashed_token = hash_token(plain_token)
    return plain_token, hashed_token


def get_utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def get_expiry_time(minutes: int = 0, hours: int = 0, days: int = 0) -> datetime:
    """
    Calculate expiry time from now.
    
    Args:
        minutes: Minutes from now
        hours: Hours from now
        days: Days from now
    
    Returns:
        Future datetime (timezone-aware UTC)
    """
    delta = timedelta(minutes=minutes, hours=hours, days=days)
    return get_utc_now() + delta


def is_expired(expiry_time: datetime) -> bool:
    """
    Check if datetime has expired.
    
    Args:
        expiry_time: Datetime to check
    
    Returns:
        True if expired, False otherwise
    """
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    return get_utc_now() > expiry_time


class SecureData:
    """
    Utility class for handling sensitive data.
    
    Provides methods for masking and redacting sensitive information.
    """
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email address for display.
        
        Args:
            email: Full email address
        
        Returns:
            Masked email (e.g., j***@gmail.com)
        """
        if not email or '@' not in email:
            return email
        
        local, domain = email.rsplit('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        Mask phone number for display.
        
        Args:
            phone: Full phone number
        
        Returns:
            Masked phone (e.g., ***-***-1234)
        """
        if not phone or len(phone) < 4:
            return phone
        
        return '*' * (len(phone) - 4) + phone[-4:]
    
    @staticmethod
    def mask_token(token: str, visible_chars: int = 8) -> str:
        """
        Mask token showing only first and last few characters.
        
        Args:
            token: Full token
            visible_chars: Characters to show on each end
        
        Returns:
            Masked token
        """
        if not token or len(token) <= visible_chars * 2:
            return token
        
        return token[:visible_chars] + '...' + token[-visible_chars:]
    
    @staticmethod
    def redact_dict(
        data: dict,
        sensitive_keys: set[str] = None,
    ) -> dict:
        """
        Redact sensitive keys from dictionary.
        
        Args:
            data: Dictionary to redact
            sensitive_keys: Keys to redact (defaults to common patterns)
        
        Returns:
            Redacted dictionary copy
        """
        if sensitive_keys is None:
            sensitive_keys = {
                'password', 'secret', 'token', 'api_key', 'apikey',
                'authorization', 'auth', 'credential', 'private_key',
                'access_token', 'refresh_token', 'ssn', 'credit_card',
            }
        
        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = SecureData.redact_dict(value, sensitive_keys)
            else:
                redacted[key] = value
        
        return redacted


class PasswordPolicy:
    """
    Password policy validator.
    
    Enforces password strength requirements.
    """
    
    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?",
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.special_chars = set(special_chars)
    
    def validate(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digit and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not any(c in self.special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors


# Default password policy instance
password_policy = PasswordPolicy()
