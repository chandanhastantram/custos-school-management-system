"""
CUSTOS Academic Structure Service
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, DuplicateError
from app.academics.models.structure import AcademicYear, Class, Section
from app.academics.schemas.structure import (
    AcademicYearCreate, ClassCreate, SectionCreate,
)


class StructureService:
    """Academic structure management."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # Academic Years
    async def create_academic_year(self, data: AcademicYearCreate) -> AcademicYear:
        year = AcademicYear(
            tenant_id=self.tenant_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
        )
        
        if data.is_current:
            await self._unset_current_year()
        
        self.session.add(year)
        await self.session.commit()
        await self.session.refresh(year)
        return year
    
    async def get_academic_years(self) -> List[AcademicYear]:
        query = select(AcademicYear).where(
            AcademicYear.tenant_id == self.tenant_id,
            AcademicYear.is_deleted == False,
        ).order_by(AcademicYear.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_current_year(self) -> Optional[AcademicYear]:
        query = select(AcademicYear).where(
            AcademicYear.tenant_id == self.tenant_id,
            AcademicYear.is_current == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _unset_current_year(self):
        query = select(AcademicYear).where(
            AcademicYear.tenant_id == self.tenant_id,
            AcademicYear.is_current == True,
        )
        result = await self.session.execute(query)
        for year in result.scalars():
            year.is_current = False
    
    # Classes
    async def create_class(self, data: ClassCreate) -> Class:
        cls = Class(
            tenant_id=self.tenant_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            code=data.code,
            grade_level=data.grade_level,
            description=data.description,
        )
        self.session.add(cls)
        await self.session.commit()
        await self.session.refresh(cls)
        return cls
    
    async def get_classes(self, academic_year_id: Optional[UUID] = None) -> List[Class]:
        query = select(Class).where(
            Class.tenant_id == self.tenant_id,
            Class.is_deleted == False,
        )
        if academic_year_id:
            query = query.where(Class.academic_year_id == academic_year_id)
        query = query.order_by(Class.grade_level)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_class(self, class_id: UUID) -> Class:
        query = select(Class).where(
            Class.tenant_id == self.tenant_id,
            Class.id == class_id,
        )
        result = await self.session.execute(query)
        cls = result.scalar_one_or_none()
        if not cls:
            raise ResourceNotFoundError("Class", str(class_id))
        return cls
    
    # Sections
    async def create_section(self, data: SectionCreate) -> Section:
        section = Section(
            tenant_id=self.tenant_id,
            class_id=data.class_id,
            name=data.name,
            code=data.code,
            capacity=data.capacity,
            room_number=data.room_number,
            class_teacher_id=data.class_teacher_id,
        )
        self.session.add(section)
        await self.session.commit()
        await self.session.refresh(section)
        return section
    
    async def get_sections(self, class_id: UUID) -> List[Section]:
        query = select(Section).where(
            Section.tenant_id == self.tenant_id,
            Section.class_id == class_id,
            Section.is_deleted == False,
        ).order_by(Section.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_section(self, section_id: UUID) -> Section:
        query = select(Section).where(
            Section.tenant_id == self.tenant_id,
            Section.id == section_id,
        )
        result = await self.session.execute(query)
        section = result.scalar_one_or_none()
        if not section:
            raise ResourceNotFoundError("Section", str(section_id))
        return section
