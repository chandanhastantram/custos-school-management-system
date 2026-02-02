"""
CUSTOS HR & Payroll Management Models

Employees, departments, salaries, payroll, and leave management.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy import Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import TenantBaseModel


class EmployeeRole(str, Enum):
    """Employee role types."""
    TEACHER = "teacher"
    ADMIN = "admin"
    CLERK = "clerk"
    ACCOUNTANT = "accountant"
    DRIVER = "driver"
    WARDEN = "warden"
    SECURITY = "security"
    HOUSEKEEPING = "housekeeping"
    LAB_ASSISTANT = "lab_assistant"
    LIBRARIAN = "librarian"
    OTHER = "other"


class EmploymentType(str, Enum):
    """Type of employment."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"


class Gender(str, Enum):
    """Gender enum."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class ComponentType(str, Enum):
    """Salary component type."""
    EARNING = "earning"
    DEDUCTION = "deduction"


class PayrollStatus(str, Enum):
    """Payroll run status."""
    DRAFT = "draft"
    PROCESSING = "processing"
    PROCESSED = "processed"
    PAID = "paid"
    CANCELLED = "cancelled"


class LeaveStatus(str, Enum):
    """Leave application status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ============================================
# Department & Designation
# ============================================

class Department(TenantBaseModel):
    """
    Department within the school.
    
    E.g., Academic, Administration, Finance, Transport.
    """
    __tablename__ = "hr_departments"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_department_name"),
        Index("ix_hr_departments_tenant", "tenant_id", "is_active"),
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    head_employee_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )  # FK added later to avoid circular
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Designation(TenantBaseModel):
    """
    Job designation/title.
    
    E.g., Principal, Vice Principal, Senior Teacher, Clerk.
    """
    __tablename__ = "hr_designations"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_designation_name"),
        Index("ix_hr_designations_tenant", "tenant_id", "is_active"),
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # Hierarchy level
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================
# Employee
# ============================================

class Employee(TenantBaseModel):
    """
    Employee / Staff Member.
    
    Represents all school staff - teaching and non-teaching.
    """
    __tablename__ = "hr_employees"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_code", name="uq_employee_code"),
        Index("ix_hr_employees_tenant", "tenant_id", "is_active"),
        Index("ix_hr_employees_department", "department_id"),
        Index("ix_hr_employees_designation", "designation_id"),
    )
    
    # Link to system user (for teachers/staff with login access)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Basic Info
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(SQLEnum(Gender), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Contact
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Role & Position
    role: Mapped[EmployeeRole] = mapped_column(
        SQLEnum(EmployeeRole),
        default=EmployeeRole.OTHER,
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    designation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_designations.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Employment Details
    employment_type: Mapped[EmploymentType] = mapped_column(
        SQLEnum(EmploymentType),
        default=EmploymentType.FULL_TIME,
    )
    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    date_of_leaving: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Qualifications
    qualifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Documents (optional)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    documents_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Bank Details (for salary)
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department", foreign_keys=[department_id]
    )
    designation: Mapped[Optional["Designation"]] = relationship(
        "Designation", foreign_keys=[designation_id]
    )


# ============================================
# Employment Contract
# ============================================

class EmploymentContract(TenantBaseModel):
    """
    Employment Contract.
    
    Links employee to salary structure with validity dates.
    """
    __tablename__ = "hr_employment_contracts"
    
    __table_args__ = (
        Index("ix_hr_contracts_employee", "employee_id", "is_active"),
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    salary_structure_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_payroll_structures.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Base salary (override if different from structure)
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Contract terms
    probation_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notice_period_days: Mapped[int] = mapped_column(Integer, default=30)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ============================================
# Salary Components & Structure
# ============================================

class SalaryComponent(TenantBaseModel):
    """
    Salary Component.
    
    Building blocks for salary structure (earnings and deductions).
    """
    __tablename__ = "hr_salary_components"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_salary_component_name"),
        Index("ix_hr_salary_components_tenant", "tenant_id", "is_active"),
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    component_type: Mapped[ComponentType] = mapped_column(
        SQLEnum(ComponentType),
        default=ComponentType.EARNING,
    )
    
    # Calculation
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False)
    percentage_of: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "basic"
    default_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Taxation
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Display order
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PayrollStructure(TenantBaseModel):
    """
    Payroll Structure.
    
    Template for salary calculation with multiple components.
    """
    __tablename__ = "hr_payroll_structures"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_payroll_structure_name"),
        Index("ix_hr_payroll_structures_tenant", "tenant_id", "is_active"),
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Components with their values
    # Format: [{"component_id": "uuid", "value": 10000, "is_percentage": false}, ...]
    components_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Default base salary for this structure
    base_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================
# Payroll Run & Salary Slips
# ============================================

class PayrollRun(TenantBaseModel):
    """
    Payroll Run.
    
    Monthly payroll processing record.
    """
    __tablename__ = "hr_payroll_runs"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "month", "year", name="uq_payroll_run_month"),
        Index("ix_hr_payroll_runs_tenant", "tenant_id", "status"),
    )
    
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[PayrollStatus] = mapped_column(
        SQLEnum(PayrollStatus),
        default=PayrollStatus.DRAFT,
    )
    
    # Processing details
    processed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Summary
    total_employees: Mapped[int] = mapped_column(Integer, default=0)
    total_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    
    # Payment details
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SalarySlip(TenantBaseModel):
    """
    Salary Slip.
    
    Individual employee salary for a payroll run.
    """
    __tablename__ = "hr_salary_slips"
    
    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_salary_slip_employee"),
        Index("ix_hr_salary_slips_payroll", "payroll_run_id"),
        Index("ix_hr_salary_slips_employee", "employee_id"),
    )
    
    payroll_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_payroll_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Salary breakdown
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    
    # Detailed breakdown
    # Format: {"earnings": [...], "deductions": [...]}
    breakdown_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Working days / attendance
    working_days: Mapped[int] = mapped_column(Integer, default=0)
    present_days: Mapped[int] = mapped_column(Integer, default=0)
    leave_days: Mapped[int] = mapped_column(Integer, default=0)
    
    # Generation
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    # Payment
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ============================================
# Leave Management
# ============================================

class LeaveType(TenantBaseModel):
    """
    Leave Type.
    
    E.g., Casual Leave, Sick Leave, Earned Leave.
    """
    __tablename__ = "hr_leave_types"
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_leave_type_name"),
        Index("ix_hr_leave_types_tenant", "tenant_id", "is_active"),
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Annual quota
    annual_quota: Mapped[int] = mapped_column(Integer, default=0)
    
    # Carry forward
    can_carry_forward: Mapped[bool] = mapped_column(Boolean, default=False)
    max_carry_forward: Mapped[int] = mapped_column(Integer, default=0)
    
    # Encashment
    is_encashable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Rules
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    min_days_notice: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LeaveBalance(TenantBaseModel):
    """
    Leave Balance.
    
    Tracks remaining leave for each employee per leave type.
    """
    __tablename__ = "hr_leave_balances"
    
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", "year", name="uq_leave_balance"),
        Index("ix_hr_leave_balances_employee", "employee_id"),
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    leave_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_leave_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Balance tracking
    total_allocated: Mapped[int] = mapped_column(Integer, default=0)
    used_days: Mapped[int] = mapped_column(Integer, default=0)
    remaining_days: Mapped[int] = mapped_column(Integer, default=0)
    carried_forward: Mapped[int] = mapped_column(Integer, default=0)


class LeaveApplication(TenantBaseModel):
    """
    Leave Application.
    
    Employee leave request with approval workflow.
    """
    __tablename__ = "hr_leave_applications"
    
    __table_args__ = (
        Index("ix_hr_leave_applications_employee", "employee_id"),
        Index("ix_hr_leave_applications_status", "tenant_id", "status"),
    )
    
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    leave_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hr_leave_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Leave period
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Half day support
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False)
    half_day_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # first_half, second_half
    
    # Reason
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Status
    status: Mapped[LeaveStatus] = mapped_column(
        SQLEnum(LeaveStatus),
        default=LeaveStatus.PENDING,
    )
    
    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Attachments (for medical leave etc.)
    attachments_json: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
