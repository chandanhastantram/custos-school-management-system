"""
CUSTOS Password Module

Password hashing and validation using bcrypt.
"""

from passlib.context import CryptContext

from app.core.config import settings


# Password context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.password_hash_rounds,
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored bcrypt hash
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if password hash needs to be updated.
    
    Args:
        hashed_password: Current password hash
    
    Returns:
        True if hash should be regenerated
    """
    return pwd_context.needs_update(hashed_password)


class PasswordValidator:
    """Password strength validator."""
    
    def __init__(
        self,
        min_length: int = 8,
        max_length: int = 128,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.special_chars = set("!@#$%^&*()_+-=[]{}|;':\",./<>?")
    
    def validate(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters")
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digit and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.require_special and not any(c in self.special_chars for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors


# Default password validator
password_validator = PasswordValidator()
