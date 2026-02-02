"""
CUSTOS HR & Payroll Service

Business logic for HR operations.
"""

from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.hr.models import (
    Department, Designation, Employee, EmploymentContract,
    SalaryComponent, PayrollStructure, PayrollRun, SalarySlip,
    LeaveType, LeaveBalance, LeaveApplication,
    EmployeeRole, EmploymentType, ComponentType, PayrollStatus, LeaveStatus,
)
from app.hr.schemas import (
    DepartmentCreate, DepartmentUpdate,
    DesignationCreate, DesignationUpdate,
    EmployeeCreate, EmployeeUpdate,
    SalaryComponentCreate, SalaryComponentUpdate,
    PayrollStructureCreate, PayrollStructureUpdate, StructureComponent,
    EmploymentContractCreate,
    PayrollRunCreate,
    LeaveTypeCreate, LeaveTypeUpdate,
    LeaveApplicationCreate, LeaveApplicationApprove,
)


class HRService:
    """Service for HR & Payroll operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Department Management
    # ============================================
    
    async def create_department(self, data: DepartmentCreate) -> Department:
        """Create a new department."""
        existing = await self._get_department_by_name(data.name)
        if existing:
            raise ValidationError(f"Department '{data.name}' already exists")
        
        dept = Department(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            head_employee_id=data.head_employee_id,
        )
        
        self.session.add(dept)
        await self.session.commit()
        await self.session.refresh(dept)
        return dept
    
    async def update_department(self, dept_id: UUID, data: DepartmentUpdate) -> Department:
        """Update a department."""
        dept = await self.get_department(dept_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dept, key, value)
        
        await self.session.commit()
        await self.session.refresh(dept)
        return dept
    
    async def get_department(self, dept_id: UUID) -> Department:
        """Get a department by ID."""
        query = select(Department).where(
            Department.tenant_id == self.tenant_id,
            Department.id == dept_id,
        )
        result = await self.session.execute(query)
        dept = result.scalar_one_or_none()
        
        if not dept:
            raise ResourceNotFoundError("Department", str(dept_id))
        return dept
    
    async def _get_department_by_name(self, name: str) -> Optional[Department]:
        """Get department by name."""
        query = select(Department).where(
            Department.tenant_id == self.tenant_id,
            Department.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_departments(self, active_only: bool = True) -> List[Department]:
        """List all departments."""
        query = select(Department).where(
            Department.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.where(Department.is_active == True)
        query = query.order_by(Department.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Designation Management
    # ============================================
    
    async def create_designation(self, data: DesignationCreate) -> Designation:
        """Create a new designation."""
        existing = await self._get_designation_by_name(data.name)
        if existing:
            raise ValidationError(f"Designation '{data.name}' already exists")
        
        desig = Designation(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            level=data.level,
            description=data.description,
        )
        
        self.session.add(desig)
        await self.session.commit()
        await self.session.refresh(desig)
        return desig
    
    async def update_designation(self, desig_id: UUID, data: DesignationUpdate) -> Designation:
        """Update a designation."""
        desig = await self.get_designation(desig_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(desig, key, value)
        
        await self.session.commit()
        await self.session.refresh(desig)
        return desig
    
    async def get_designation(self, desig_id: UUID) -> Designation:
        """Get a designation by ID."""
        query = select(Designation).where(
            Designation.tenant_id == self.tenant_id,
            Designation.id == desig_id,
        )
        result = await self.session.execute(query)
        desig = result.scalar_one_or_none()
        
        if not desig:
            raise ResourceNotFoundError("Designation", str(desig_id))
        return desig
    
    async def _get_designation_by_name(self, name: str) -> Optional[Designation]:
        """Get designation by name."""
        query = select(Designation).where(
            Designation.tenant_id == self.tenant_id,
            Designation.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_designations(self, active_only: bool = True) -> List[Designation]:
        """List all designations."""
        query = select(Designation).where(
            Designation.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.where(Designation.is_active == True)
        query = query.order_by(Designation.level, Designation.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Employee Management
    # ============================================
    
    async def create_employee(self, data: EmployeeCreate) -> Employee:
        """Create a new employee."""
        # Check for duplicate employee code
        existing = await self._get_employee_by_code(data.employee_code)
        if existing:
            raise ValidationError(f"Employee code '{data.employee_code}' already exists")
        
        employee = Employee(
            tenant_id=self.tenant_id,
            user_id=data.user_id,
            employee_code=data.employee_code,
            first_name=data.first_name,
            last_name=data.last_name,
            gender=data.gender,
            date_of_birth=data.date_of_birth,
            email=data.email,
            phone=data.phone,
            alternate_phone=data.alternate_phone,
            address=data.address,
            role=data.role,
            department_id=data.department_id,
            designation_id=data.designation_id,
            employment_type=data.employment_type,
            date_of_joining=data.date_of_joining,
            qualifications=data.qualifications,
            experience_years=data.experience_years,
            bank_name=data.bank_name,
            bank_account_number=data.bank_account_number,
            bank_ifsc=data.bank_ifsc,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            emergency_contact_relation=data.emergency_contact_relation,
            notes=data.notes,
        )
        
        self.session.add(employee)
        await self.session.commit()
        await self.session.refresh(employee)
        return employee
    
    async def update_employee(self, emp_id: UUID, data: EmployeeUpdate) -> Employee:
        """Update an employee."""
        employee = await self.get_employee(emp_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(employee, key, value)
        
        await self.session.commit()
        await self.session.refresh(employee)
        return employee
    
    async def get_employee(self, emp_id: UUID) -> Employee:
        """Get an employee by ID."""
        query = select(Employee).where(
            Employee.tenant_id == self.tenant_id,
            Employee.id == emp_id,
            Employee.deleted_at.is_(None),
        ).options(
            selectinload(Employee.department),
            selectinload(Employee.designation),
        )
        result = await self.session.execute(query)
        employee = result.scalar_one_or_none()
        
        if not employee:
            raise ResourceNotFoundError("Employee", str(emp_id))
        return employee
    
    async def get_employee_by_user_id(self, user_id: UUID) -> Optional[Employee]:
        """Get employee by linked user ID."""
        query = select(Employee).where(
            Employee.tenant_id == self.tenant_id,
            Employee.user_id == user_id,
            Employee.deleted_at.is_(None),
        ).options(
            selectinload(Employee.department),
            selectinload(Employee.designation),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_employee_by_code(self, code: str) -> Optional[Employee]:
        """Get employee by code."""
        query = select(Employee).where(
            Employee.tenant_id == self.tenant_id,
            Employee.employee_code == code,
            Employee.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_employees(
        self,
        active_only: bool = True,
        department_id: Optional[UUID] = None,
        role: Optional[EmployeeRole] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Employee], int]:
        """List employees with filters."""
        query = select(Employee).where(
            Employee.tenant_id == self.tenant_id,
            Employee.deleted_at.is_(None),
        )
        
        if active_only:
            query = query.where(Employee.is_active == True)
        if department_id:
            query = query.where(Employee.department_id == department_id)
        if role:
            query = query.where(Employee.role == role)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.options(
            selectinload(Employee.department),
            selectinload(Employee.designation),
        ).order_by(Employee.first_name).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def delete_employee(self, emp_id: UUID) -> None:
        """Soft delete an employee."""
        employee = await self.get_employee(emp_id)
        employee.deleted_at = datetime.now(timezone.utc)
        employee.is_active = False
        await self.session.commit()
    
    # ============================================
    # Salary Components
    # ============================================
    
    async def create_salary_component(self, data: SalaryComponentCreate) -> SalaryComponent:
        """Create a salary component."""
        existing = await self._get_component_by_name(data.name)
        if existing:
            raise ValidationError(f"Salary component '{data.name}' already exists")
        
        component = SalaryComponent(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            component_type=data.component_type,
            is_percentage=data.is_percentage,
            percentage_of=data.percentage_of,
            default_value=Decimal(str(data.default_value)),
            is_taxable=data.is_taxable,
            display_order=data.display_order,
        )
        
        self.session.add(component)
        await self.session.commit()
        await self.session.refresh(component)
        return component
    
    async def update_salary_component(
        self, comp_id: UUID, data: SalaryComponentUpdate
    ) -> SalaryComponent:
        """Update a salary component."""
        component = await self.get_salary_component(comp_id)
        
        update_data = data.model_dump(exclude_unset=True)
        if "default_value" in update_data:
            update_data["default_value"] = Decimal(str(update_data["default_value"]))
        
        for key, value in update_data.items():
            setattr(component, key, value)
        
        await self.session.commit()
        await self.session.refresh(component)
        return component
    
    async def get_salary_component(self, comp_id: UUID) -> SalaryComponent:
        """Get a salary component by ID."""
        query = select(SalaryComponent).where(
            SalaryComponent.tenant_id == self.tenant_id,
            SalaryComponent.id == comp_id,
        )
        result = await self.session.execute(query)
        component = result.scalar_one_or_none()
        
        if not component:
            raise ResourceNotFoundError("SalaryComponent", str(comp_id))
        return component
    
    async def _get_component_by_name(self, name: str) -> Optional[SalaryComponent]:
        """Get component by name."""
        query = select(SalaryComponent).where(
            SalaryComponent.tenant_id == self.tenant_id,
            SalaryComponent.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_salary_components(self, active_only: bool = True) -> List[SalaryComponent]:
        """List all salary components."""
        query = select(SalaryComponent).where(
            SalaryComponent.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.where(SalaryComponent.is_active == True)
        query = query.order_by(SalaryComponent.display_order, SalaryComponent.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Payroll Structure
    # ============================================
    
    async def create_payroll_structure(self, data: PayrollStructureCreate) -> PayrollStructure:
        """Create a payroll structure."""
        existing = await self._get_structure_by_name(data.name)
        if existing:
            raise ValidationError(f"Payroll structure '{data.name}' already exists")
        
        # Convert components to JSON format
        components_json = [
            {
                "component_id": str(c.component_id),
                "value": c.value,
                "is_percentage": c.is_percentage,
            }
            for c in data.components
        ]
        
        structure = PayrollStructure(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            base_salary=Decimal(str(data.base_salary)),
            components_json=components_json,
        )
        
        self.session.add(structure)
        await self.session.commit()
        await self.session.refresh(structure)
        return structure
    
    async def update_payroll_structure(
        self, struct_id: UUID, data: PayrollStructureUpdate
    ) -> PayrollStructure:
        """Update a payroll structure."""
        structure = await self.get_payroll_structure(struct_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "base_salary" in update_data:
            update_data["base_salary"] = Decimal(str(update_data["base_salary"]))
        
        if "components" in update_data:
            update_data["components_json"] = [
                {
                    "component_id": str(c["component_id"]),
                    "value": c["value"],
                    "is_percentage": c.get("is_percentage", False),
                }
                for c in update_data.pop("components")
            ]
        
        for key, value in update_data.items():
            setattr(structure, key, value)
        
        await self.session.commit()
        await self.session.refresh(structure)
        return structure
    
    async def get_payroll_structure(self, struct_id: UUID) -> PayrollStructure:
        """Get a payroll structure by ID."""
        query = select(PayrollStructure).where(
            PayrollStructure.tenant_id == self.tenant_id,
            PayrollStructure.id == struct_id,
        )
        result = await self.session.execute(query)
        structure = result.scalar_one_or_none()
        
        if not structure:
            raise ResourceNotFoundError("PayrollStructure", str(struct_id))
        return structure
    
    async def _get_structure_by_name(self, name: str) -> Optional[PayrollStructure]:
        """Get structure by name."""
        query = select(PayrollStructure).where(
            PayrollStructure.tenant_id == self.tenant_id,
            PayrollStructure.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_payroll_structures(self, active_only: bool = True) -> List[PayrollStructure]:
        """List all payroll structures."""
        query = select(PayrollStructure).where(
            PayrollStructure.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.where(PayrollStructure.is_active == True)
        query = query.order_by(PayrollStructure.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Employment Contract
    # ============================================
    
    async def create_contract(self, data: EmploymentContractCreate) -> EmploymentContract:
        """Create an employment contract."""
        # Validate employee exists
        await self.get_employee(data.employee_id)
        
        # Deactivate any existing active contracts
        existing_query = select(EmploymentContract).where(
            EmploymentContract.employee_id == data.employee_id,
            EmploymentContract.is_active == True,
        )
        result = await self.session.execute(existing_query)
        for contract in result.scalars().all():
            contract.is_active = False
            contract.end_date = data.start_date
        
        contract = EmploymentContract(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            salary_structure_id=data.salary_structure_id,
            start_date=data.start_date,
            end_date=data.end_date,
            base_salary=Decimal(str(data.base_salary)) if data.base_salary else None,
            probation_end_date=data.probation_end_date,
            notice_period_days=data.notice_period_days,
            notes=data.notes,
        )
        
        self.session.add(contract)
        await self.session.commit()
        await self.session.refresh(contract)
        return contract
    
    async def get_active_contract(self, employee_id: UUID) -> Optional[EmploymentContract]:
        """Get active contract for an employee."""
        query = select(EmploymentContract).where(
            EmploymentContract.employee_id == employee_id,
            EmploymentContract.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ============================================
    # Payroll Run
    # ============================================
    
    async def create_payroll_run(self, data: PayrollRunCreate) -> PayrollRun:
        """Create a new payroll run (draft)."""
        # Check for existing payroll run
        existing = await self._get_payroll_run(data.month, data.year)
        if existing:
            raise ValidationError(f"Payroll run for {data.month}/{data.year} already exists")
        
        payroll = PayrollRun(
            tenant_id=self.tenant_id,
            month=data.month,
            year=data.year,
            status=PayrollStatus.DRAFT,
            notes=data.notes,
        )
        
        self.session.add(payroll)
        await self.session.commit()
        await self.session.refresh(payroll)
        return payroll
    
    async def process_payroll(self, payroll_id: UUID, processed_by: UUID) -> PayrollRun:
        """Process a payroll run and generate salary slips."""
        payroll = await self.get_payroll_run_by_id(payroll_id)
        
        if payroll.status != PayrollStatus.DRAFT:
            raise ValidationError("Only draft payroll runs can be processed")
        
        payroll.status = PayrollStatus.PROCESSING
        await self.session.commit()
        
        # Get all active employees
        employees, _ = await self.list_employees(active_only=True, page=1, size=1000)
        
        total_gross = Decimal("0")
        total_deductions = Decimal("0")
        total_net = Decimal("0")
        
        for employee in employees:
            # Get active contract
            contract = await self.get_active_contract(employee.id)
            
            if not contract:
                continue
            
            # Calculate salary
            slip = await self._generate_salary_slip(
                payroll, employee, contract
            )
            
            total_gross += slip.gross_salary
            total_deductions += slip.total_deductions
            total_net += slip.net_salary
        
        # Update payroll run
        payroll.status = PayrollStatus.PROCESSED
        payroll.processed_by = processed_by
        payroll.processed_at = datetime.now(timezone.utc)
        payroll.total_employees = len(employees)
        payroll.total_gross = total_gross
        payroll.total_deductions = total_deductions
        payroll.total_net = total_net
        
        await self.session.commit()
        await self.session.refresh(payroll)
        return payroll
    
    async def _generate_salary_slip(
        self,
        payroll: PayrollRun,
        employee: Employee,
        contract: EmploymentContract,
    ) -> SalarySlip:
        """Generate salary slip for an employee."""
        # Get salary structure
        structure = None
        if contract.salary_structure_id:
            structure = await self.get_payroll_structure(contract.salary_structure_id)
        
        # Calculate base salary
        base_salary = contract.base_salary or (structure.base_salary if structure else Decimal("0"))
        
        earnings = []
        deductions = []
        total_earnings = Decimal("0")
        total_deductions = Decimal("0")
        
        # Process components from structure
        if structure and structure.components_json:
            components = await self.list_salary_components(active_only=True)
            comp_map = {str(c.id): c for c in components}
            
            for comp_data in structure.components_json:
                comp_id = comp_data.get("component_id")
                if comp_id not in comp_map:
                    continue
                
                component = comp_map[comp_id]
                value = Decimal(str(comp_data.get("value", 0)))
                
                # Calculate percentage if applicable
                if comp_data.get("is_percentage"):
                    value = base_salary * value / Decimal("100")
                
                if component.component_type == ComponentType.EARNING:
                    earnings.append({
                        "name": component.name,
                        "amount": float(value),
                    })
                    total_earnings += value
                else:
                    deductions.append({
                        "name": component.name,
                        "amount": float(value),
                    })
                    total_deductions += value
        
        gross_salary = base_salary + total_earnings
        net_salary = gross_salary - total_deductions
        
        # TODO: Calculate working days from attendance
        working_days = 26
        present_days = 26
        leave_days = 0
        
        slip = SalarySlip(
            tenant_id=self.tenant_id,
            payroll_run_id=payroll.id,
            employee_id=employee.id,
            basic_salary=base_salary,
            gross_salary=gross_salary,
            total_deductions=total_deductions,
            net_salary=net_salary,
            breakdown_json={
                "earnings": earnings,
                "deductions": deductions,
            },
            working_days=working_days,
            present_days=present_days,
            leave_days=leave_days,
            generated_at=datetime.now(timezone.utc),
        )
        
        self.session.add(slip)
        return slip
    
    async def get_payroll_run_by_id(self, payroll_id: UUID) -> PayrollRun:
        """Get payroll run by ID."""
        query = select(PayrollRun).where(
            PayrollRun.tenant_id == self.tenant_id,
            PayrollRun.id == payroll_id,
        )
        result = await self.session.execute(query)
        payroll = result.scalar_one_or_none()
        
        if not payroll:
            raise ResourceNotFoundError("PayrollRun", str(payroll_id))
        return payroll
    
    async def _get_payroll_run(self, month: int, year: int) -> Optional[PayrollRun]:
        """Get payroll run by month/year."""
        query = select(PayrollRun).where(
            PayrollRun.tenant_id == self.tenant_id,
            PayrollRun.month == month,
            PayrollRun.year == year,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_payroll_run(self, month: int, year: int) -> Optional[PayrollRun]:
        """Get payroll run for a month."""
        return await self._get_payroll_run(month, year)
    
    async def list_payroll_runs(
        self,
        year: Optional[int] = None,
        status: Optional[PayrollStatus] = None,
    ) -> List[PayrollRun]:
        """List payroll runs."""
        query = select(PayrollRun).where(
            PayrollRun.tenant_id == self.tenant_id,
        )
        
        if year:
            query = query.where(PayrollRun.year == year)
        if status:
            query = query.where(PayrollRun.status == status)
        
        query = query.order_by(PayrollRun.year.desc(), PayrollRun.month.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def mark_payroll_paid(
        self, payroll_id: UUID, payment_reference: Optional[str] = None
    ) -> PayrollRun:
        """Mark payroll as paid."""
        payroll = await self.get_payroll_run_by_id(payroll_id)
        
        if payroll.status != PayrollStatus.PROCESSED:
            raise ValidationError("Only processed payroll can be marked as paid")
        
        payroll.status = PayrollStatus.PAID
        payroll.paid_at = datetime.now(timezone.utc)
        payroll.payment_reference = payment_reference
        
        # Mark all salary slips as paid
        slip_query = select(SalarySlip).where(
            SalarySlip.payroll_run_id == payroll_id,
        )
        result = await self.session.execute(slip_query)
        for slip in result.scalars().all():
            slip.is_paid = True
            slip.paid_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(payroll)
        return payroll
    
    # ============================================
    # Salary Slips
    # ============================================
    
    async def get_salary_slips(self, payroll_id: UUID) -> List[SalarySlip]:
        """Get all salary slips for a payroll run."""
        query = select(SalarySlip).where(
            SalarySlip.payroll_run_id == payroll_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_employee_salary_slips(
        self, employee_id: UUID, year: Optional[int] = None
    ) -> List[SalarySlip]:
        """Get salary slips for an employee."""
        query = select(SalarySlip).where(
            SalarySlip.employee_id == employee_id,
        )
        
        if year:
            # Join with PayrollRun to filter by year
            query = query.join(PayrollRun).where(PayrollRun.year == year)
        
        query = query.order_by(SalarySlip.generated_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Leave Types
    # ============================================
    
    async def create_leave_type(self, data: LeaveTypeCreate) -> LeaveType:
        """Create a leave type."""
        existing = await self._get_leave_type_by_name(data.name)
        if existing:
            raise ValidationError(f"Leave type '{data.name}' already exists")
        
        leave_type = LeaveType(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            annual_quota=data.annual_quota,
            can_carry_forward=data.can_carry_forward,
            max_carry_forward=data.max_carry_forward,
            is_encashable=data.is_encashable,
            requires_approval=data.requires_approval,
            min_days_notice=data.min_days_notice,
        )
        
        self.session.add(leave_type)
        await self.session.commit()
        await self.session.refresh(leave_type)
        return leave_type
    
    async def update_leave_type(self, type_id: UUID, data: LeaveTypeUpdate) -> LeaveType:
        """Update a leave type."""
        leave_type = await self.get_leave_type(type_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(leave_type, key, value)
        
        await self.session.commit()
        await self.session.refresh(leave_type)
        return leave_type
    
    async def get_leave_type(self, type_id: UUID) -> LeaveType:
        """Get a leave type by ID."""
        query = select(LeaveType).where(
            LeaveType.tenant_id == self.tenant_id,
            LeaveType.id == type_id,
        )
        result = await self.session.execute(query)
        leave_type = result.scalar_one_or_none()
        
        if not leave_type:
            raise ResourceNotFoundError("LeaveType", str(type_id))
        return leave_type
    
    async def _get_leave_type_by_name(self, name: str) -> Optional[LeaveType]:
        """Get leave type by name."""
        query = select(LeaveType).where(
            LeaveType.tenant_id == self.tenant_id,
            LeaveType.name == name,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def list_leave_types(self, active_only: bool = True) -> List[LeaveType]:
        """List all leave types."""
        query = select(LeaveType).where(
            LeaveType.tenant_id == self.tenant_id,
        )
        if active_only:
            query = query.where(LeaveType.is_active == True)
        query = query.order_by(LeaveType.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Leave Balance
    # ============================================
    
    async def get_leave_balance(
        self, employee_id: UUID, leave_type_id: UUID, year: int
    ) -> Optional[LeaveBalance]:
        """Get leave balance for employee."""
        query = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_leave_balances(
        self, employee_id: UUID, year: int
    ) -> List[LeaveBalance]:
        """Get all leave balances for an employee."""
        query = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def initialize_leave_balances(self, employee_id: UUID, year: int) -> None:
        """Initialize leave balances for an employee for a year."""
        leave_types = await self.list_leave_types()
        
        for lt in leave_types:
            existing = await self.get_leave_balance(employee_id, lt.id, year)
            if not existing:
                balance = LeaveBalance(
                    tenant_id=self.tenant_id,
                    employee_id=employee_id,
                    leave_type_id=lt.id,
                    year=year,
                    total_allocated=lt.annual_quota,
                    used_days=0,
                    remaining_days=lt.annual_quota,
                    carried_forward=0,
                )
                self.session.add(balance)
        
        await self.session.commit()
    
    # ============================================
    # Leave Applications
    # ============================================
    
    async def apply_leave(
        self, employee_id: UUID, data: LeaveApplicationCreate
    ) -> LeaveApplication:
        """Apply for leave."""
        # Validate leave type exists
        leave_type = await self.get_leave_type(data.leave_type_id)
        
        # Calculate total days
        total_days = (data.to_date - data.from_date).days + 1
        if data.is_half_day:
            total_days = 0.5
        
        # Check leave balance
        year = data.from_date.year
        balance = await self.get_leave_balance(employee_id, data.leave_type_id, year)
        
        if not balance:
            # Initialize balances if not exists
            await self.initialize_leave_balances(employee_id, year)
            balance = await self.get_leave_balance(employee_id, data.leave_type_id, year)
        
        if balance and balance.remaining_days < total_days:
            raise ValidationError(
                f"Insufficient leave balance. Available: {balance.remaining_days}, Requested: {total_days}"
            )
        
        # Check for overlapping applications
        overlap = await self._check_leave_overlap(
            employee_id, data.from_date, data.to_date
        )
        if overlap:
            raise ValidationError("Leave dates overlap with an existing application")
        
        application = LeaveApplication(
            tenant_id=self.tenant_id,
            employee_id=employee_id,
            leave_type_id=data.leave_type_id,
            from_date=data.from_date,
            to_date=data.to_date,
            total_days=int(total_days),
            is_half_day=data.is_half_day,
            half_day_type=data.half_day_type,
            reason=data.reason,
            status=LeaveStatus.PENDING,
        )
        
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application
    
    async def _check_leave_overlap(
        self, employee_id: UUID, from_date: date, to_date: date
    ) -> bool:
        """Check for overlapping leave applications."""
        query = select(LeaveApplication).where(
            LeaveApplication.employee_id == employee_id,
            LeaveApplication.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            or_(
                and_(
                    LeaveApplication.from_date <= from_date,
                    LeaveApplication.to_date >= from_date,
                ),
                and_(
                    LeaveApplication.from_date <= to_date,
                    LeaveApplication.to_date >= to_date,
                ),
                and_(
                    LeaveApplication.from_date >= from_date,
                    LeaveApplication.to_date <= to_date,
                ),
            ),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def approve_leave(
        self, data: LeaveApplicationApprove, approved_by: UUID
    ) -> LeaveApplication:
        """Approve or reject a leave application."""
        application = await self.get_leave_application(data.application_id)
        
        if application.status != LeaveStatus.PENDING:
            raise ValidationError("Only pending applications can be approved/rejected")
        
        if data.action == "approve":
            application.status = LeaveStatus.APPROVED
            application.approved_by = approved_by
            application.approved_at = datetime.now(timezone.utc)
            
            # Decrement leave balance
            year = application.from_date.year
            balance = await self.get_leave_balance(
                application.employee_id, application.leave_type_id, year
            )
            if balance:
                balance.used_days += application.total_days
                balance.remaining_days = balance.total_allocated - balance.used_days
        else:
            application.status = LeaveStatus.REJECTED
            application.approved_by = approved_by
            application.approved_at = datetime.now(timezone.utc)
            application.rejection_reason = data.rejection_reason
        
        await self.session.commit()
        await self.session.refresh(application)
        return application
    
    async def get_leave_application(self, app_id: UUID) -> LeaveApplication:
        """Get a leave application by ID."""
        query = select(LeaveApplication).where(
            LeaveApplication.tenant_id == self.tenant_id,
            LeaveApplication.id == app_id,
        )
        result = await self.session.execute(query)
        application = result.scalar_one_or_none()
        
        if not application:
            raise ResourceNotFoundError("LeaveApplication", str(app_id))
        return application
    
    async def list_leave_applications(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[LeaveStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[LeaveApplication], int]:
        """List leave applications."""
        query = select(LeaveApplication).where(
            LeaveApplication.tenant_id == self.tenant_id,
        )
        
        if employee_id:
            query = query.where(LeaveApplication.employee_id == employee_id)
        if status:
            query = query.where(LeaveApplication.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Pagination
        skip = (page - 1) * size
        query = query.order_by(
            LeaveApplication.created_at.desc()
        ).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_employee_leaves(self, employee_id: UUID) -> List[LeaveApplication]:
        """Get all leave applications for an employee."""
        applications, _ = await self.list_leave_applications(employee_id=employee_id)
        return applications
    
    async def cancel_leave(self, app_id: UUID, employee_id: UUID) -> LeaveApplication:
        """Cancel a leave application."""
        application = await self.get_leave_application(app_id)
        
        if application.employee_id != employee_id:
            raise ValidationError("Cannot cancel another employee's leave")
        
        if application.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
            raise ValidationError("Cannot cancel this leave application")
        
        # If approved, restore balance
        if application.status == LeaveStatus.APPROVED:
            year = application.from_date.year
            balance = await self.get_leave_balance(
                application.employee_id, application.leave_type_id, year
            )
            if balance:
                balance.used_days -= application.total_days
                balance.remaining_days = balance.total_allocated - balance.used_days
        
        application.status = LeaveStatus.CANCELLED
        await self.session.commit()
        await self.session.refresh(application)
        return application
