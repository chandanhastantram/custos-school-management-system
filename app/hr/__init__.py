"""
CUSTOS HR & Payroll Management Module

Staff management, payroll processing, and leave management.
"""

from app.hr.models import (
    Department,
    Designation,
    Employee,
    EmploymentContract,
    SalaryComponent,
    PayrollStructure,
    PayrollRun,
    SalarySlip,
    LeaveType,
    LeaveBalance,
    LeaveApplication,
    EmployeeRole,
    EmploymentType,
    ComponentType,
    PayrollStatus,
    LeaveStatus,
)
from app.hr.service import HRService
from app.hr.router import router as hr_router

__all__ = [
    # Models
    "Department",
    "Designation",
    "Employee",
    "EmploymentContract",
    "SalaryComponent",
    "PayrollStructure",
    "PayrollRun",
    "SalarySlip",
    "LeaveType",
    "LeaveBalance",
    "LeaveApplication",
    # Enums
    "EmployeeRole",
    "EmploymentType",
    "ComponentType",
    "PayrollStatus",
    "LeaveStatus",
    # Service
    "HRService",
    # Router
    "hr_router",
]
