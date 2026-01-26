"""
CUSTOS User Models

Models for users, roles, and permissions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, Date,
    ForeignKey, Enum as SQLEnum, JSON, Table, Column,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantSoftDeleteModel, TenantBaseModel, BaseModel
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class UserStatus(str, Enum):
    """User account status."""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Gender(str, Enum):
    """Gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# User-Role association table
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"),
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    Column("tenant_id", PGUUID(as_uuid=True), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)

# Role-Permission association table
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"),
    Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)


class Permission(BaseModel):
    """
    Permission model for RBAC.
    
    System-wide permissions that can be assigned to roles.
    """
    
    __tablename__ = "permissions"
    
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )
    
    def __repr__(self) -> str:
        return f"<Permission(code='{self.code}')>"


class Role(TenantBaseModel):
    """
    Role model for RBAC.
    
    Tenant-specific roles with associated permissions.
    """
    
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    hierarchy_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Relationships
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
    
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )
    
    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', code='{self.code}')>"
    
    def has_permission(self, permission_code: str) -> bool:
        """Check if role has specific permission."""
        return any(p.code == permission_code for p in self.permissions)


class User(TenantSoftDeleteModel):
    """
    User model for all system users.
    
    Represents students, teachers, parents, and staff.
    """
    
    __tablename__ = "users"
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Profile
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    
    gender: Mapped[Optional[Gender]] = mapped_column(
        SQLEnum(Gender),
        nullable=True,
    )
    
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Address
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    is_phone_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Security
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # Supports IPv6
        nullable=True,
    )
    
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Password Reset
    reset_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Email Verification
    verification_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Preferences
    preferences: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
    )
    
    notification_settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
    )
    
    # Gamification
    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
        foreign_keys="User.tenant_id",
        lazy="selectin",
    )
    
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )
    
    # Student-specific relationship
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    
    # Teacher-specific relationship
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        "TeacherProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    
    # Parent-specific relationship
    parent_profile: Mapped[Optional["ParentProfile"]] = relationship(
        "ParentProfile",
        back_populates="user",
        uselist=False,
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE and not self.is_deleted
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if not self.locked_until:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def has_role(self, role_code: str) -> bool:
        """Check if user has specific role."""
        return any(r.code == role_code for r in self.roles)
    
    def has_permission(self, permission_code: str) -> bool:
        """Check if user has specific permission through any role."""
        for role in self.roles:
            if role.has_permission(permission_code):
                return True
        return False
    
    def get_all_permissions(self) -> set[str]:
        """Get all permission codes for user."""
        permissions = set()
        for role in self.roles:
            for perm in role.permissions:
                permissions.add(perm.code)
        return permissions
    
    def record_login(self, ip_address: Optional[str] = None) -> None:
        """Record successful login."""
        self.last_login_at = datetime.now(timezone.utc)
        self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def record_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 30) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)


from datetime import timedelta


class StudentProfile(TenantBaseModel):
    """
    Extended profile for student users.
    """
    
    __tablename__ = "student_profiles"
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Academic Info
    admission_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    admission_date: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True,
    )
    
    class_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    roll_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Guardian Info
    guardian_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    guardian_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    guardian_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    
    guardian_relation: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Medical Info
    blood_group: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
    )
    
    medical_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Transport
    uses_transport: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    transport_route: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_profile",
        lazy="selectin",
    )


class TeacherProfile(TenantBaseModel):
    """
    Extended profile for teacher users.
    """
    
    __tablename__ = "teacher_profiles"
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Employment Info
    employee_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    designation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    joining_date: Mapped[Optional[datetime]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Qualifications
    qualifications: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    specializations: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        default=list,
    )
    
    experience_years: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Class Teacher Assignment
    is_class_teacher: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    class_teacher_of_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="teacher_profile",
        lazy="selectin",
    )


class ParentProfile(TenantBaseModel):
    """
    Extended profile for parent users.
    """
    
    __tablename__ = "parent_profiles"
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Occupation
    occupation: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    workplace: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="parent_profile",
        lazy="selectin",
    )


# Parent-Student relationship (many-to-many)
parent_student_relations = Table(
    "parent_student_relations",
    Base.metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()"),
    Column("parent_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("student_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("relationship", String(50), nullable=False),  # father, mother, guardian
    Column("is_primary", Boolean, default=False),
    Column("tenant_id", PGUUID(as_uuid=True), nullable=False, index=True),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)
