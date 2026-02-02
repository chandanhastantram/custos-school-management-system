"""
CUSTOS HR & Payroll Router

API endpoints for HR management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission, require_role
from app.users.rbac import Permission, SystemRole
from app.hr.service import HRService
from app.hr.models import EmployeeRole, PayrollStatus, LeaveStatus
from app.hr.schemas import (
    # Department
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    # Designation
    DesignationCreate, DesignationUpdate, DesignationResponse,
    # Employee
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListItem, EmployeeProfile,
    # Salary Component
    SalaryComponentCreate, SalaryComponentUpdate, SalaryComponentResponse,
    # Payroll Structure
    PayrollStructureCreate, PayrollStructureUpdate, PayrollStructureResponse,
    # Contract
    EmploymentContractCreate, EmploymentContractResponse,
    # Payroll Run
    PayrollRunCreate, PayrollRunResponse,
    # Salary Slip
    SalarySlipResponse,
    # Leave Type
    LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse,
    # Leave Balance
    LeaveBalanceResponse,
    # Leave Application
    LeaveApplicationCreate, LeaveApplicationApprove, LeaveApplicationResponse,
)


router = APIRouter(tags=["HR"])


# ============================================
# Department Management
# ============================================

@router.post("/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Create a new department."""
    service = HRService(db, user.tenant_id)
    dept = await service.create_department(data)
    return DepartmentResponse.model_validate(dept)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """List all departments."""
    service = HRService(db, user.tenant_id)
    depts = await service.list_departments(active_only)
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: UUID,
    data: DepartmentUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Update a department."""
    service = HRService(db, user.tenant_id)
    dept = await service.update_department(dept_id, data)
    return DepartmentResponse.model_validate(dept)


# ============================================
# Designation Management
# ============================================

@router.post("/designations", response_model=DesignationResponse, status_code=201)
async def create_designation(
    data: DesignationCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Create a new designation."""
    service = HRService(db, user.tenant_id)
    desig = await service.create_designation(data)
    return DesignationResponse.model_validate(desig)


@router.get("/designations", response_model=List[DesignationResponse])
async def list_designations(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """List all designations."""
    service = HRService(db, user.tenant_id)
    desigs = await service.list_designations(active_only)
    return [DesignationResponse.model_validate(d) for d in desigs]


@router.patch("/designations/{desig_id}", response_model=DesignationResponse)
async def update_designation(
    desig_id: UUID,
    data: DesignationUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Update a designation."""
    service = HRService(db, user.tenant_id)
    desig = await service.update_designation(desig_id, data)
    return DesignationResponse.model_validate(desig)


# ============================================
# Employee Management
# ============================================

@router.post("/employees", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Create a new employee."""
    service = HRService(db, user.tenant_id)
    employee = await service.create_employee(data)
    
    return EmployeeResponse(
        id=employee.id,
        tenant_id=employee.tenant_id,
        user_id=employee.user_id,
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        gender=employee.gender,
        date_of_birth=employee.date_of_birth,
        email=employee.email,
        phone=employee.phone,
        role=employee.role,
        department_id=employee.department_id,
        designation_id=employee.designation_id,
        employment_type=employee.employment_type,
        date_of_joining=employee.date_of_joining,
        date_of_leaving=employee.date_of_leaving,
        qualifications=employee.qualifications,
        experience_years=employee.experience_years,
        is_active=employee.is_active,
        created_at=employee.created_at,
        department_name=employee.department.name if employee.department else None,
        designation_name=employee.designation.name if employee.designation else None,
    )


@router.get("/employees", response_model=List[EmployeeListItem])
async def list_employees(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    department_id: Optional[UUID] = None,
    role: Optional[EmployeeRole] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """List all employees."""
    service = HRService(db, user.tenant_id)
    employees, _ = await service.list_employees(active_only, department_id, role, page, size)
    
    return [
        EmployeeListItem(
            id=e.id,
            employee_code=e.employee_code,
            first_name=e.first_name,
            last_name=e.last_name,
            role=e.role,
            department_name=e.department.name if e.department else None,
            designation_name=e.designation.name if e.designation else None,
            is_active=e.is_active,
        )
        for e in employees
    ]


@router.get("/employees/{emp_id}", response_model=EmployeeResponse)
async def get_employee(
    emp_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Get an employee by ID."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee(emp_id)
    
    return EmployeeResponse(
        id=employee.id,
        tenant_id=employee.tenant_id,
        user_id=employee.user_id,
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        gender=employee.gender,
        date_of_birth=employee.date_of_birth,
        email=employee.email,
        phone=employee.phone,
        role=employee.role,
        department_id=employee.department_id,
        designation_id=employee.designation_id,
        employment_type=employee.employment_type,
        date_of_joining=employee.date_of_joining,
        date_of_leaving=employee.date_of_leaving,
        qualifications=employee.qualifications,
        experience_years=employee.experience_years,
        is_active=employee.is_active,
        created_at=employee.created_at,
        department_name=employee.department.name if employee.department else None,
        designation_name=employee.designation.name if employee.designation else None,
    )


@router.patch("/employees/{emp_id}", response_model=EmployeeResponse)
async def update_employee(
    emp_id: UUID,
    data: EmployeeUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Update an employee."""
    service = HRService(db, user.tenant_id)
    employee = await service.update_employee(emp_id, data)
    
    return EmployeeResponse(
        id=employee.id,
        tenant_id=employee.tenant_id,
        user_id=employee.user_id,
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        gender=employee.gender,
        date_of_birth=employee.date_of_birth,
        email=employee.email,
        phone=employee.phone,
        role=employee.role,
        department_id=employee.department_id,
        designation_id=employee.designation_id,
        employment_type=employee.employment_type,
        date_of_joining=employee.date_of_joining,
        date_of_leaving=employee.date_of_leaving,
        qualifications=employee.qualifications,
        experience_years=employee.experience_years,
        is_active=employee.is_active,
        created_at=employee.created_at,
        department_name=employee.department.name if employee.department else None,
        designation_name=employee.designation.name if employee.designation else None,
    )


@router.delete("/employees/{emp_id}")
async def delete_employee(
    emp_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Delete an employee (soft delete)."""
    service = HRService(db, user.tenant_id)
    await service.delete_employee(emp_id)
    return {"success": True, "message": "Employee deleted"}


# ============================================
# Self-Service: My Profile
# ============================================

@router.get("/my-profile", response_model=EmployeeProfile)
async def get_my_profile(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's employee profile."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    return EmployeeProfile(
        id=employee.id,
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        email=employee.email,
        phone=employee.phone,
        role=employee.role,
        department_name=employee.department.name if employee.department else None,
        designation_name=employee.designation.name if employee.designation else None,
        date_of_joining=employee.date_of_joining,
        employment_type=employee.employment_type,
    )


# ============================================
# Salary Components
# ============================================

@router.post("/salary-components", response_model=SalaryComponentResponse, status_code=201)
async def create_salary_component(
    data: SalaryComponentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Create a salary component."""
    service = HRService(db, user.tenant_id)
    component = await service.create_salary_component(data)
    return SalaryComponentResponse.model_validate(component)


@router.get("/salary-components", response_model=List[SalaryComponentResponse])
async def list_salary_components(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.PAYROLL_VIEW)),
):
    """List all salary components."""
    service = HRService(db, user.tenant_id)
    components = await service.list_salary_components(active_only)
    return [SalaryComponentResponse.model_validate(c) for c in components]


@router.patch("/salary-components/{comp_id}", response_model=SalaryComponentResponse)
async def update_salary_component(
    comp_id: UUID,
    data: SalaryComponentUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Update a salary component."""
    service = HRService(db, user.tenant_id)
    component = await service.update_salary_component(comp_id, data)
    return SalaryComponentResponse.model_validate(component)


# ============================================
# Payroll Structures
# ============================================

@router.post("/payroll-structures", response_model=PayrollStructureResponse, status_code=201)
async def create_payroll_structure(
    data: PayrollStructureCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Create a payroll structure."""
    service = HRService(db, user.tenant_id)
    structure = await service.create_payroll_structure(data)
    return PayrollStructureResponse.model_validate(structure)


@router.get("/payroll-structures", response_model=List[PayrollStructureResponse])
async def list_payroll_structures(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
    _=Depends(require_permission(Permission.PAYROLL_VIEW)),
):
    """List all payroll structures."""
    service = HRService(db, user.tenant_id)
    structures = await service.list_payroll_structures(active_only)
    return [PayrollStructureResponse.model_validate(s) for s in structures]


@router.patch("/payroll-structures/{struct_id}", response_model=PayrollStructureResponse)
async def update_payroll_structure(
    struct_id: UUID,
    data: PayrollStructureUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Update a payroll structure."""
    service = HRService(db, user.tenant_id)
    structure = await service.update_payroll_structure(struct_id, data)
    return PayrollStructureResponse.model_validate(structure)


# ============================================
# Employment Contracts
# ============================================

@router.post("/contracts", response_model=EmploymentContractResponse, status_code=201)
async def create_contract(
    data: EmploymentContractCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Create an employment contract."""
    service = HRService(db, user.tenant_id)
    contract = await service.create_contract(data)
    return EmploymentContractResponse.model_validate(contract)


@router.get("/employees/{emp_id}/contract", response_model=EmploymentContractResponse)
async def get_employee_contract(
    emp_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Get active contract for an employee."""
    service = HRService(db, user.tenant_id)
    contract = await service.get_active_contract(emp_id)
    
    if not contract:
        raise HTTPException(status_code=404, detail="No active contract found")
    
    return EmploymentContractResponse.model_validate(contract)


# ============================================
# Payroll Run
# ============================================

@router.post("/payroll/run", response_model=PayrollRunResponse, status_code=201)
async def create_payroll_run(
    data: PayrollRunCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Create a new payroll run (draft)."""
    service = HRService(db, user.tenant_id)
    payroll = await service.create_payroll_run(data)
    return PayrollRunResponse.model_validate(payroll)


@router.post("/payroll/{payroll_id}/process", response_model=PayrollRunResponse)
async def process_payroll(
    payroll_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Process a payroll run and generate salary slips."""
    service = HRService(db, user.tenant_id)
    payroll = await service.process_payroll(payroll_id, user.id)
    return PayrollRunResponse.model_validate(payroll)


@router.post("/payroll/{payroll_id}/mark-paid", response_model=PayrollRunResponse)
async def mark_payroll_paid(
    payroll_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    payment_reference: Optional[str] = None,
    _=Depends(require_permission(Permission.PAYROLL_RUN)),
):
    """Mark a processed payroll as paid."""
    service = HRService(db, user.tenant_id)
    payroll = await service.mark_payroll_paid(payroll_id, payment_reference)
    return PayrollRunResponse.model_validate(payroll)


@router.get("/payroll/{month}/{year}", response_model=PayrollRunResponse)
async def get_payroll_run(
    month: int,
    year: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_VIEW)),
):
    """Get payroll run for a specific month."""
    service = HRService(db, user.tenant_id)
    payroll = await service.get_payroll_run(month, year)
    
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    
    return PayrollRunResponse.model_validate(payroll)


@router.get("/payroll", response_model=List[PayrollRunResponse])
async def list_payroll_runs(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    year: Optional[int] = None,
    status: Optional[PayrollStatus] = None,
    _=Depends(require_permission(Permission.PAYROLL_VIEW)),
):
    """List all payroll runs."""
    service = HRService(db, user.tenant_id)
    payrolls = await service.list_payroll_runs(year, status)
    return [PayrollRunResponse.model_validate(p) for p in payrolls]


# ============================================
# Salary Slips
# ============================================

@router.get("/payroll/{payroll_id}/slips", response_model=List[SalarySlipResponse])
async def get_payroll_slips(
    payroll_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.PAYROLL_VIEW)),
):
    """Get all salary slips for a payroll run."""
    service = HRService(db, user.tenant_id)
    slips = await service.get_salary_slips(payroll_id)
    
    # Get payroll for month/year
    payroll = await service.get_payroll_run_by_id(payroll_id)
    
    result = []
    for s in slips:
        employee = await service.get_employee(s.employee_id)
        result.append(SalarySlipResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            payroll_run_id=s.payroll_run_id,
            employee_id=s.employee_id,
            basic_salary=float(s.basic_salary),
            gross_salary=float(s.gross_salary),
            total_deductions=float(s.total_deductions),
            net_salary=float(s.net_salary),
            breakdown_json=s.breakdown_json,
            working_days=s.working_days,
            present_days=s.present_days,
            leave_days=s.leave_days,
            generated_at=s.generated_at,
            is_paid=s.is_paid,
            paid_at=s.paid_at,
            employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
            employee_code=employee.employee_code,
            month=payroll.month,
            year=payroll.year,
        ))
    
    return result


@router.get("/my-salary-slips", response_model=List[SalarySlipResponse])
async def get_my_salary_slips(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    year: Optional[int] = None,
):
    """Get current user's salary slips."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    slips = await service.get_employee_salary_slips(employee.id, year)
    
    return [
        SalarySlipResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            payroll_run_id=s.payroll_run_id,
            employee_id=s.employee_id,
            basic_salary=float(s.basic_salary),
            gross_salary=float(s.gross_salary),
            total_deductions=float(s.total_deductions),
            net_salary=float(s.net_salary),
            breakdown_json=s.breakdown_json,
            working_days=s.working_days,
            present_days=s.present_days,
            leave_days=s.leave_days,
            generated_at=s.generated_at,
            is_paid=s.is_paid,
            paid_at=s.paid_at,
            employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
            employee_code=employee.employee_code,
        )
        for s in slips
    ]


# ============================================
# Leave Types
# ============================================

@router.post("/leave-types", response_model=LeaveTypeResponse, status_code=201)
async def create_leave_type(
    data: LeaveTypeCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Create a leave type."""
    service = HRService(db, user.tenant_id)
    leave_type = await service.create_leave_type(data)
    return LeaveTypeResponse.model_validate(leave_type)


@router.get("/leave-types", response_model=List[LeaveTypeResponse])
async def list_leave_types(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
):
    """List all leave types."""
    service = HRService(db, user.tenant_id)
    leave_types = await service.list_leave_types(active_only)
    return [LeaveTypeResponse.model_validate(lt) for lt in leave_types]


@router.patch("/leave-types/{type_id}", response_model=LeaveTypeResponse)
async def update_leave_type(
    type_id: UUID,
    data: LeaveTypeUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.HR_MANAGE)),
):
    """Update a leave type."""
    service = HRService(db, user.tenant_id)
    leave_type = await service.update_leave_type(type_id, data)
    return LeaveTypeResponse.model_validate(leave_type)


# ============================================
# Leave Applications
# ============================================

@router.post("/leaves/apply", response_model=LeaveApplicationResponse, status_code=201)
async def apply_leave(
    data: LeaveApplicationCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Apply for leave."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    application = await service.apply_leave(employee.id, data)
    
    leave_type = await service.get_leave_type(application.leave_type_id)
    
    return LeaveApplicationResponse(
        id=application.id,
        tenant_id=application.tenant_id,
        employee_id=application.employee_id,
        leave_type_id=application.leave_type_id,
        from_date=application.from_date,
        to_date=application.to_date,
        total_days=application.total_days,
        is_half_day=application.is_half_day,
        half_day_type=application.half_day_type,
        reason=application.reason,
        status=application.status,
        approved_by=application.approved_by,
        approved_at=application.approved_at,
        rejection_reason=application.rejection_reason,
        created_at=application.created_at,
        employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
        leave_type_name=leave_type.name,
    )


@router.get("/leaves/my", response_model=List[LeaveApplicationResponse])
async def get_my_leaves(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get current user's leave applications."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    applications = await service.get_employee_leaves(employee.id)
    
    result = []
    for a in applications:
        leave_type = await service.get_leave_type(a.leave_type_id)
        result.append(LeaveApplicationResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            employee_id=a.employee_id,
            leave_type_id=a.leave_type_id,
            from_date=a.from_date,
            to_date=a.to_date,
            total_days=a.total_days,
            is_half_day=a.is_half_day,
            half_day_type=a.half_day_type,
            reason=a.reason,
            status=a.status,
            approved_by=a.approved_by,
            approved_at=a.approved_at,
            rejection_reason=a.rejection_reason,
            created_at=a.created_at,
            employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
            leave_type_name=leave_type.name,
        ))
    
    return result


@router.get("/leaves/my-balance", response_model=List[LeaveBalanceResponse])
async def get_my_leave_balance(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    year: int = Query(..., ge=2020),
):
    """Get current user's leave balance."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Initialize if needed
    await service.initialize_leave_balances(employee.id, year)
    
    balances = await service.get_all_leave_balances(employee.id, year)
    
    result = []
    for b in balances:
        leave_type = await service.get_leave_type(b.leave_type_id)
        result.append(LeaveBalanceResponse(
            id=b.id,
            employee_id=b.employee_id,
            leave_type_id=b.leave_type_id,
            year=b.year,
            total_allocated=b.total_allocated,
            used_days=b.used_days,
            remaining_days=b.remaining_days,
            carried_forward=b.carried_forward,
            leave_type_name=leave_type.name,
        ))
    
    return result


@router.post("/leaves/{app_id}/cancel")
async def cancel_leave(
    app_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a leave application."""
    service = HRService(db, user.tenant_id)
    employee = await service.get_employee_by_user_id(user.id)
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    await service.cancel_leave(app_id, employee.id)
    return {"success": True, "message": "Leave application cancelled"}


# ============================================
# Leave Approval
# ============================================

@router.get("/leaves/pending", response_model=List[LeaveApplicationResponse])
async def get_pending_leaves(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    _=Depends(require_permission(Permission.LEAVE_APPROVE)),
):
    """Get all pending leave applications."""
    service = HRService(db, user.tenant_id)
    applications, _ = await service.list_leave_applications(
        status=LeaveStatus.PENDING, page=page, size=size
    )
    
    result = []
    for a in applications:
        employee = await service.get_employee(a.employee_id)
        leave_type = await service.get_leave_type(a.leave_type_id)
        result.append(LeaveApplicationResponse(
            id=a.id,
            tenant_id=a.tenant_id,
            employee_id=a.employee_id,
            leave_type_id=a.leave_type_id,
            from_date=a.from_date,
            to_date=a.to_date,
            total_days=a.total_days,
            is_half_day=a.is_half_day,
            half_day_type=a.half_day_type,
            reason=a.reason,
            status=a.status,
            approved_by=a.approved_by,
            approved_at=a.approved_at,
            rejection_reason=a.rejection_reason,
            created_at=a.created_at,
            employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
            leave_type_name=leave_type.name,
        ))
    
    return result


@router.post("/leaves/approve", response_model=LeaveApplicationResponse)
async def approve_leave(
    data: LeaveApplicationApprove,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.LEAVE_APPROVE)),
):
    """Approve or reject a leave application."""
    service = HRService(db, user.tenant_id)
    application = await service.approve_leave(data, user.id)
    
    employee = await service.get_employee(application.employee_id)
    leave_type = await service.get_leave_type(application.leave_type_id)
    
    return LeaveApplicationResponse(
        id=application.id,
        tenant_id=application.tenant_id,
        employee_id=application.employee_id,
        leave_type_id=application.leave_type_id,
        from_date=application.from_date,
        to_date=application.to_date,
        total_days=application.total_days,
        is_half_day=application.is_half_day,
        half_day_type=application.half_day_type,
        reason=application.reason,
        status=application.status,
        approved_by=application.approved_by,
        approved_at=application.approved_at,
        rejection_reason=application.rejection_reason,
        created_at=application.created_at,
        employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
        leave_type_name=leave_type.name,
    )
