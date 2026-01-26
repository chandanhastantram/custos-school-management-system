"""
CUSTOS Academic Service

Academic structure management.
"""

from datetime import date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, DuplicateError, ValidationError
from app.models.academic import (
    AcademicYear, Class, Section, Subject, Syllabus, Topic, Lesson,
    ClassSubjectTeacher, SyllabusStatus, TopicStatus, LessonStatus
)
from app.schemas.academic import (
    AcademicYearCreate, ClassCreate, ClassUpdate, SectionCreate,
    SubjectCreate, SyllabusCreate, TopicCreate, LessonCreate,
)


class AcademicService:
    """Academic structure management service."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ==================== Academic Years ====================
    
    async def create_academic_year(self, data: AcademicYearCreate) -> AcademicYear:
        """Create academic year."""
        # If setting as current, unset others
        if data.is_current:
            query = select(AcademicYear).where(
                AcademicYear.tenant_id == self.tenant_id,
                AcademicYear.is_current == True
            )
            result = await self.session.execute(query)
            for ay in result.scalars():
                ay.is_current = False
        
        academic_year = AcademicYear(
            tenant_id=self.tenant_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            is_current=data.is_current,
        )
        self.session.add(academic_year)
        await self.session.commit()
        await self.session.refresh(academic_year)
        return academic_year
    
    async def get_academic_years(self) -> List[AcademicYear]:
        """Get all academic years."""
        query = select(AcademicYear).where(
            AcademicYear.tenant_id == self.tenant_id
        ).order_by(AcademicYear.start_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_current_academic_year(self) -> Optional[AcademicYear]:
        """Get current academic year."""
        query = select(AcademicYear).where(
            AcademicYear.tenant_id == self.tenant_id,
            AcademicYear.is_current == True
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ==================== Classes ====================
    
    async def create_class(self, data: ClassCreate) -> Class:
        """Create class."""
        # Check duplicate code
        exists = await self.session.execute(
            select(Class).where(
                Class.tenant_id == self.tenant_id,
                Class.academic_year_id == data.academic_year_id,
                Class.code == data.code
            )
        )
        if exists.scalar_one_or_none():
            raise DuplicateError("Class", "code", data.code)
        
        cls = Class(
            tenant_id=self.tenant_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            code=data.code,
            grade_level=data.grade_level,
            description=data.description,
            display_order=data.display_order,
        )
        self.session.add(cls)
        await self.session.commit()
        await self.session.refresh(cls)
        return cls
    
    async def get_classes(
        self,
        academic_year_id: Optional[UUID] = None,
    ) -> List[Class]:
        """Get all classes."""
        query = select(Class).where(
            Class.tenant_id == self.tenant_id,
            Class.is_active == True
        )
        if academic_year_id:
            query = query.where(Class.academic_year_id == academic_year_id)
        query = query.order_by(Class.display_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_class(self, class_id: UUID) -> Class:
        """Get class by ID."""
        query = select(Class).where(
            Class.tenant_id == self.tenant_id,
            Class.id == class_id
        )
        result = await self.session.execute(query)
        cls = result.scalar_one_or_none()
        if not cls:
            raise ResourceNotFoundError("Class", str(class_id))
        return cls
    
    async def update_class(self, class_id: UUID, data: ClassUpdate) -> Class:
        """Update class."""
        cls = await self.get_class(class_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cls, key, value)
        await self.session.commit()
        await self.session.refresh(cls)
        return cls
    
    async def delete_class(self, class_id: UUID) -> bool:
        """Soft delete class."""
        cls = await self.get_class(class_id)
        cls.is_active = False
        await self.session.commit()
        return True
    
    # ==================== Sections ====================
    
    async def create_section(self, data: SectionCreate) -> Section:
        """Create section."""
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
        """Get sections for a class."""
        query = select(Section).where(
            Section.tenant_id == self.tenant_id,
            Section.class_id == class_id,
            Section.is_active == True
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_section(self, section_id: UUID) -> Section:
        """Get section by ID."""
        query = select(Section).where(
            Section.tenant_id == self.tenant_id,
            Section.id == section_id
        )
        result = await self.session.execute(query)
        section = result.scalar_one_or_none()
        if not section:
            raise ResourceNotFoundError("Section", str(section_id))
        return section
    
    # ==================== Subjects ====================
    
    async def create_subject(self, data: SubjectCreate) -> Subject:
        """Create subject."""
        subject = Subject(
            tenant_id=self.tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            category=data.category,
            is_mandatory=data.is_mandatory,
            credits=data.credits,
            color=data.color,
            icon=data.icon,
        )
        self.session.add(subject)
        await self.session.commit()
        await self.session.refresh(subject)
        return subject
    
    async def get_subjects(self, category: Optional[str] = None) -> List[Subject]:
        """Get all subjects."""
        query = select(Subject).where(
            Subject.tenant_id == self.tenant_id,
            Subject.is_active == True
        )
        if category:
            query = query.where(Subject.category == category)
        query = query.order_by(Subject.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_subject(self, subject_id: UUID) -> Subject:
        """Get subject by ID."""
        query = select(Subject).where(
            Subject.tenant_id == self.tenant_id,
            Subject.id == subject_id
        )
        result = await self.session.execute(query)
        subject = result.scalar_one_or_none()
        if not subject:
            raise ResourceNotFoundError("Subject", str(subject_id))
        return subject
    
    # ==================== Teacher-Subject Assignment ====================
    
    async def assign_teacher_to_subject(
        self,
        class_id: UUID,
        subject_id: UUID,
        teacher_id: UUID,
        section_id: Optional[UUID] = None,
    ) -> ClassSubjectTeacher:
        """Assign teacher to subject for a class."""
        assignment = ClassSubjectTeacher(
            tenant_id=self.tenant_id,
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            section_id=section_id,
        )
        self.session.add(assignment)
        await self.session.commit()
        await self.session.refresh(assignment)
        return assignment
    
    async def get_teacher_assignments(self, teacher_id: UUID) -> List[ClassSubjectTeacher]:
        """Get all assignments for a teacher."""
        query = select(ClassSubjectTeacher).where(
            ClassSubjectTeacher.tenant_id == self.tenant_id,
            ClassSubjectTeacher.teacher_id == teacher_id,
            ClassSubjectTeacher.is_active == True
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ==================== Syllabus ====================
    
    async def create_syllabus(self, data: SyllabusCreate) -> Syllabus:
        """Create syllabus."""
        syllabus = Syllabus(
            tenant_id=self.tenant_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            academic_year_id=data.academic_year_id,
            title=data.title,
            description=data.description,
            total_hours=data.total_hours,
            status=SyllabusStatus.DRAFT,
        )
        self.session.add(syllabus)
        await self.session.commit()
        await self.session.refresh(syllabus)
        return syllabus
    
    async def get_syllabi(
        self,
        class_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        academic_year_id: Optional[UUID] = None,
    ) -> List[Syllabus]:
        """Get syllabi with filters."""
        query = select(Syllabus).where(Syllabus.tenant_id == self.tenant_id)
        if class_id:
            query = query.where(Syllabus.class_id == class_id)
        if subject_id:
            query = query.where(Syllabus.subject_id == subject_id)
        if academic_year_id:
            query = query.where(Syllabus.academic_year_id == academic_year_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_syllabus(self, syllabus_id: UUID) -> Syllabus:
        """Get syllabus with topics."""
        query = select(Syllabus).where(
            Syllabus.tenant_id == self.tenant_id,
            Syllabus.id == syllabus_id
        ).options(selectinload(Syllabus.topics))
        result = await self.session.execute(query)
        syllabus = result.scalar_one_or_none()
        if not syllabus:
            raise ResourceNotFoundError("Syllabus", str(syllabus_id))
        return syllabus
    
    # ==================== Topics ====================
    
    async def create_topic(self, data: TopicCreate) -> Topic:
        """Create topic."""
        topic = Topic(
            tenant_id=self.tenant_id,
            syllabus_id=data.syllabus_id,
            parent_topic_id=data.parent_topic_id,
            name=data.name,
            description=data.description,
            order=data.order,
            estimated_hours=data.estimated_hours,
            learning_objectives=data.learning_objectives,
            keywords=data.keywords,
            status=TopicStatus.NOT_STARTED,
        )
        self.session.add(topic)
        await self.session.commit()
        await self.session.refresh(topic)
        return topic
    
    async def get_topics(self, syllabus_id: UUID) -> List[Topic]:
        """Get topics for syllabus."""
        query = select(Topic).where(
            Topic.tenant_id == self.tenant_id,
            Topic.syllabus_id == syllabus_id
        ).order_by(Topic.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_topic(self, topic_id: UUID) -> Topic:
        """Get topic by ID."""
        query = select(Topic).where(
            Topic.tenant_id == self.tenant_id,
            Topic.id == topic_id
        )
        result = await self.session.execute(query)
        topic = result.scalar_one_or_none()
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        return topic
    
    async def update_topic_status(self, topic_id: UUID, status: TopicStatus) -> Topic:
        """Update topic status."""
        from datetime import datetime, timezone
        
        topic = await self.get_topic(topic_id)
        topic.status = status
        if status == TopicStatus.COMPLETED:
            topic.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(topic)
        return topic
    
    # ==================== Lessons ====================
    
    async def create_lesson(self, data: LessonCreate, teacher_id: UUID) -> Lesson:
        """Create lesson."""
        lesson = Lesson(
            tenant_id=self.tenant_id,
            topic_id=data.topic_id,
            teacher_id=teacher_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            objectives=data.objectives,
            content=data.content,
            resources=data.resources,
            activities=data.activities,
            homework=data.homework,
            scheduled_date=data.scheduled_date,
            status=LessonStatus.DRAFT,
        )
        self.session.add(lesson)
        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson
    
    async def get_lessons(
        self,
        topic_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None,
    ) -> List[Lesson]:
        """Get lessons with filters."""
        query = select(Lesson).where(Lesson.tenant_id == self.tenant_id)
        if topic_id:
            query = query.where(Lesson.topic_id == topic_id)
        if teacher_id:
            query = query.where(Lesson.teacher_id == teacher_id)
        query = query.order_by(Lesson.scheduled_date.desc().nullsfirst())
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_lesson(self, lesson_id: UUID) -> Lesson:
        """Get lesson by ID."""
        query = select(Lesson).where(
            Lesson.tenant_id == self.tenant_id,
            Lesson.id == lesson_id
        )
        result = await self.session.execute(query)
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise ResourceNotFoundError("Lesson", str(lesson_id))
        return lesson
    
    async def complete_lesson(self, lesson_id: UUID) -> Lesson:
        """Mark lesson as completed."""
        from datetime import datetime, timezone
        
        lesson = await self.get_lesson(lesson_id)
        lesson.status = LessonStatus.COMPLETED
        lesson.completed_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(lesson)
        return lesson
