"""
CUSTOS HR & Payroll Schemas

Pydantic schemas for HR API.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.hr.models import (
    EmployeeRole, EmploymentType, Gender, ComponentType,
    PayrollStatus, LeaveStatus,
)


# ============================================
# Department Schemas
# ============================================

class DepartmentCreate(BaseModel):
    """Schema for creating a department."""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    head_employee_id: Optional[UUID] = None


class DepartmentUpdate(BaseModel):
    """Schema for updating a department."""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    head_employee_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    """Schema for department response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    head_employee_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime


# ============================================
# Designation Schemas
# ============================================

class DesignationCreate(BaseModel):
    """Schema for creating a designation."""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    level: int = Field(1, ge=1)
    description: Optional[str] = None


class DesignationUpdate(BaseModel):
    """Schema for updating a designation."""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    level: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DesignationResponse(BaseModel):
    """Schema for designation response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    level: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


# ============================================
# Employee Schemas
# ============================================

class EmployeeCreate(BaseModel):
    """Schema for creating an employee."""
    user_id: Optional[UUID] = None
    employee_code: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    role: EmployeeRole = EmployeeRole.OTHER
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    date_of_joining: date
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee."""
    user_id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    role: Optional[EmployeeRole] = None
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    employment_type: Optional[EmploymentType] = None
    date_of_leaving: Optional[date] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    bank_name: Optional[str] = Field(None, max_length=200)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_ifsc: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Schema for employee response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    employee_code: str
    first_name: str
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: EmployeeRole
    department_id: Optional[UUID] = None
    designation_id: Optional[UUID] = None
    employment_type: EmploymentType
    date_of_joining: date
    date_of_leaving: Optional[date] = None
    qualifications: Optional[str] = None
    experience_years: Optional[int] = None
    is_active: bool
    created_at: datetime
    
    # Denormalized
    department_name: Optional[str] = None
    designation_name: Optional[str] = None


class EmployeeListItem(BaseModel):
    """Schema for listing employees."""
    id: UUID
    employee_code: str
    first_name: str
    last_name: Optional[str] = None
    role: EmployeeRole
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    is_active: bool


class EmployeeProfile(BaseModel):
    """Detailed employee profile (self-view)."""
    id: UUID
    employee_code: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: EmployeeRole
    department_name: Optional[str] = None
    designation_name: Optional[str] = None
    date_of_joining: date
    employment_type: EmploymentType


# ============================================
# Salary Component Schemas
# ============================================

class SalaryComponentCreate(BaseModel):
    """Schema for creating a salary component."""
    name: str = Field(..., max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    component_type: ComponentType = ComponentType.EARNING
    is_percentage: bool = False
    percentage_of: Optional[str] = Field(None, max_length=50)
    default_value: float = 0
    is_taxable: bool = True
    display_order: int = 0


class SalaryComponentUpdate(BaseModel):
    """Schema for updating a salary component."""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    component_type: Optional[ComponentType] = None
    is_percentage: Optional[bool] = None
    percentage_of: Optional[str] = Field(None, max_length=50)
    default_value: Optional[float] = None
    is_taxable: Optional[bool] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class SalaryComponentResponse(BaseModel):
    """Schema for salary component response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    component_type: ComponentType
    is_percentage: bool
    percentage_of: Optional[str] = None
    default_value: float
    is_taxable: bool
    display_order: int
    is_active: bool


# ============================================
# Payroll Structure Schemas
# ============================================

class StructureComponent(BaseModel):
    """Component within a payroll structure."""
    component_id: UUID
    value: float
    is_percentage: bool = False


class PayrollStructureCreate(BaseModel):
    """Schema for creating a payroll structure."""
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    base_salary: float = 0
    components: List[StructureComponent] = []


class PayrollStructureUpdate(BaseModel):
    """Schema for updating a payroll structure."""
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    base_salary: Optional[float] = None
    components: Optional[List[StructureComponent]] = None
    is_active: Optional[bool] = None


class PayrollStructureResponse(BaseModel):
    """Schema for payroll structure response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    base_salary: float
    components_json: Optional[list] = None
    is_active: bool
    created_at: datetime


# ============================================
# Employment Contract Schemas
# ============================================

class EmploymentContractCreate(BaseModel):
    """Schema for creating an employment contract."""
    employee_id: UUID
    salary_structure_id: Optional[UUID] = None
    start_date: date
    end_date: Optional[date] = None
    base_salary: Optional[float] = None
    probation_end_date: Optional[date] = None
    notice_period_days: int = 30
    notes: Optional[str] = None


class EmploymentContractResponse(BaseModel):
    """Schema for employment contract response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    employee_id: UUID
    salary_structure_id: Optional[UUID] = None
    start_date: date
    end_date: Optional[date] = None
    base_salary: Optional[float] = None
    probation_end_date: Optional[date] = None
    notice_period_days: int
    is_active: bool
    created_at: datetime


# ============================================
# Payroll Run Schemas
# ============================================

class PayrollRunCreate(BaseModel):
    """Schema for creating/initiating a payroll run."""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    notes: Optional[str] = None


class PayrollRunProcess(BaseModel):
    """Schema for processing a payroll run."""
    payroll_run_id: UUID


class PayrollRunResponse(BaseModel):
    """Schema for payroll run response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    month: int
    year: int
    status: PayrollStatus
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    total_employees: int
    total_gross: float
    total_deductions: float
    total_net: float
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# ============================================
# Salary Slip Schemas
# ============================================

class SalarySlipResponse(BaseModel):
    """Schema for salary slip response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    basic_salary: float
    gross_salary: float
    total_deductions: float
    net_salary: float
    breakdown_json: Optional[dict] = None
    working_days: int
    present_days: int
    leave_days: int
    generated_at: datetime
    is_paid: bool
    paid_at: Optional[datetime] = None
    
    # Denormalized
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None


# ============================================
# Leave Type Schemas
# ============================================

class LeaveTypeCreate(BaseModel):
    """Schema for creating a leave type."""
    name: str = Field(..., max_length=100)
    code: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    annual_quota: int = Field(0, ge=0)
    can_carry_forward: bool = False
    max_carry_forward: int = 0
    is_encashable: bool = False
    requires_approval: bool = True
    min_days_notice: int = 0


class LeaveTypeUpdate(BaseModel):
    """Schema for updating a leave type."""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    annual_quota: Optional[int] = Field(None, ge=0)
    can_carry_forward: Optional[bool] = None
    max_carry_forward: Optional[int] = None
    is_encashable: Optional[bool] = None
    requires_approval: Optional[bool] = None
    min_days_notice: Optional[int] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(BaseModel):
    """Schema for leave type response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    annual_quota: int
    can_carry_forward: bool
    max_carry_forward: int
    is_encashable: bool
    requires_approval: bool
    min_days_notice: int
    is_active: bool


# ============================================
# Leave Balance Schemas
# ============================================

class LeaveBalanceResponse(BaseModel):
    """Schema for leave balance response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    employee_id: UUID
    leave_type_id: UUID
    year: int
    total_allocated: int
    used_days: int
    remaining_days: int
    carried_forward: int
    
    # Denormalized
    leave_type_name: Optional[str] = None


# ============================================
# Leave Application Schemas
# ============================================

class LeaveApplicationCreate(BaseModel):
    """Schema for applying for leave."""
    leave_type_id: UUID
    from_date: date
    to_date: date
    is_half_day: bool = False
    half_day_type: Optional[str] = Field(None, max_length=20)
    reason: str


class LeaveApplicationApprove(BaseModel):
    """Schema for approving/rejecting leave."""
    application_id: UUID
    action: str = Field(..., pattern="^(approve|reject)$")
    rejection_reason: Optional[str] = None


class LeaveApplicationResponse(BaseModel):
    """Schema for leave application response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    employee_id: UUID
    leave_type_id: UUID
    from_date: date
    to_date: date
    total_days: int
    is_half_day: bool
    half_day_type: Optional[str] = None
    reason: str
    status: LeaveStatus
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    # Denormalized
    employee_name: Optional[str] = None
    leave_type_name: Optional[str] = None
