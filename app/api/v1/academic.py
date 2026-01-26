"""
CUSTOS Academic API Endpoints

Academic structure management routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth import AuthUser, TenantCtx, require_permissions, Permission
from app.services.academic_service import AcademicService
from app.schemas.academic import (
    AcademicYearCreate, AcademicYearResponse,
    ClassCreate, ClassUpdate, ClassResponse,
    SectionCreate, SectionResponse,
    SubjectCreate, SubjectResponse,
    SyllabusCreate, SyllabusResponse,
    TopicCreate, TopicResponse,
    LessonCreate, LessonResponse,
)
from app.schemas.common import SuccessResponse
from app.models.academic import TopicStatus


router = APIRouter(prefix="/academic", tags=["Academic"])


# ==================== Academic Years ====================

@router.get("/years", response_model=list[AcademicYearResponse])
async def list_academic_years(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """List all academic years."""
    service = AcademicService(db, ctx.tenant_id)
    years = await service.get_academic_years()
    return [AcademicYearResponse.model_validate(y) for y in years]


@router.post("/years", response_model=AcademicYearResponse)
async def create_academic_year(
    data: AcademicYearCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.TENANT_UPDATE)),
):
    """Create academic year."""
    service = AcademicService(db, ctx.tenant_id)
    year = await service.create_academic_year(data)
    return AcademicYearResponse.model_validate(year)


@router.get("/years/current", response_model=AcademicYearResponse)
async def get_current_academic_year(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get current academic year."""
    service = AcademicService(db, ctx.tenant_id)
    year = await service.get_current_academic_year()
    if not year:
        return SuccessResponse(success=False, message="No current academic year set")
    return AcademicYearResponse.model_validate(year)


# ==================== Classes ====================

@router.get("/classes", response_model=list[ClassResponse])
async def list_classes(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    academic_year_id: Optional[UUID] = None,
):
    """List all classes."""
    service = AcademicService(db, ctx.tenant_id)
    classes = await service.get_classes(academic_year_id)
    return [ClassResponse.model_validate(c) for c in classes]


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    data: ClassCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CLASS_CREATE)),
):
    """Create class."""
    service = AcademicService(db, ctx.tenant_id)
    cls = await service.create_class(data)
    return ClassResponse.model_validate(cls)


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get class by ID."""
    service = AcademicService(db, ctx.tenant_id)
    cls = await service.get_class(class_id)
    return ClassResponse.model_validate(cls)


@router.put("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: UUID,
    data: ClassUpdate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CLASS_UPDATE)),
):
    """Update class."""
    service = AcademicService(db, ctx.tenant_id)
    cls = await service.update_class(class_id, data)
    return ClassResponse.model_validate(cls)


@router.delete("/classes/{class_id}", response_model=SuccessResponse)
async def delete_class(
    class_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CLASS_DELETE)),
):
    """Delete class."""
    service = AcademicService(db, ctx.tenant_id)
    await service.delete_class(class_id)
    return SuccessResponse(message="Class deleted")


# ==================== Sections ====================

@router.get("/classes/{class_id}/sections", response_model=list[SectionResponse])
async def list_sections(
    class_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """List sections for a class."""
    service = AcademicService(db, ctx.tenant_id)
    sections = await service.get_sections(class_id)
    return [SectionResponse.model_validate(s) for s in sections]


@router.post("/sections", response_model=SectionResponse)
async def create_section(
    data: SectionCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.CLASS_CREATE)),
):
    """Create section."""
    service = AcademicService(db, ctx.tenant_id)
    section = await service.create_section(data)
    return SectionResponse.model_validate(section)


@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get section by ID."""
    service = AcademicService(db, ctx.tenant_id)
    section = await service.get_section(section_id)
    return SectionResponse.model_validate(section)


# ==================== Subjects ====================

@router.get("/subjects", response_model=list[SubjectResponse])
async def list_subjects(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
):
    """List all subjects."""
    service = AcademicService(db, ctx.tenant_id)
    subjects = await service.get_subjects(category)
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.post("/subjects", response_model=SubjectResponse)
async def create_subject(
    data: SubjectCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.SUBJECT_CREATE)),
):
    """Create subject."""
    service = AcademicService(db, ctx.tenant_id)
    subject = await service.create_subject(data)
    return SubjectResponse.model_validate(subject)


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get subject by ID."""
    service = AcademicService(db, ctx.tenant_id)
    subject = await service.get_subject(subject_id)
    return SubjectResponse.model_validate(subject)


# ==================== Teacher Assignment ====================

@router.post("/assign-teacher")
async def assign_teacher_to_subject(
    class_id: UUID,
    subject_id: UUID,
    teacher_id: UUID,
    section_id: Optional[UUID] = None,
    ctx: TenantCtx = None,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.TEACHER_UPDATE)),
):
    """Assign teacher to subject for a class."""
    service = AcademicService(db, ctx.tenant_id)
    assignment = await service.assign_teacher_to_subject(
        class_id=class_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        section_id=section_id,
    )
    return {"id": str(assignment.id), "message": "Teacher assigned"}


@router.get("/teacher/{teacher_id}/assignments")
async def get_teacher_assignments(
    teacher_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get all subject assignments for a teacher."""
    service = AcademicService(db, ctx.tenant_id)
    assignments = await service.get_teacher_assignments(teacher_id)
    return {"assignments": assignments}


# ==================== Syllabus ====================

@router.get("/syllabus", response_model=list[SyllabusResponse])
async def list_syllabi(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    academic_year_id: Optional[UUID] = None,
):
    """List syllabi with filters."""
    service = AcademicService(db, ctx.tenant_id)
    syllabi = await service.get_syllabi(class_id, subject_id, academic_year_id)
    return [SyllabusResponse.model_validate(s) for s in syllabi]


@router.post("/syllabus", response_model=SyllabusResponse)
async def create_syllabus(
    data: SyllabusCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.SYLLABUS_CREATE)),
):
    """Create syllabus."""
    service = AcademicService(db, ctx.tenant_id)
    syllabus = await service.create_syllabus(data)
    return SyllabusResponse.model_validate(syllabus)


@router.get("/syllabus/{syllabus_id}", response_model=SyllabusResponse)
async def get_syllabus(
    syllabus_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get syllabus with topics."""
    service = AcademicService(db, ctx.tenant_id)
    syllabus = await service.get_syllabus(syllabus_id)
    return SyllabusResponse.model_validate(syllabus)


# ==================== Topics ====================

@router.get("/syllabus/{syllabus_id}/topics", response_model=list[TopicResponse])
async def list_topics(
    syllabus_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """List topics for syllabus."""
    service = AcademicService(db, ctx.tenant_id)
    topics = await service.get_topics(syllabus_id)
    return [TopicResponse.model_validate(t) for t in topics]


@router.post("/topics", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.SYLLABUS_UPDATE)),
):
    """Create topic."""
    service = AcademicService(db, ctx.tenant_id)
    topic = await service.create_topic(data)
    return TopicResponse.model_validate(topic)


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get topic by ID."""
    service = AcademicService(db, ctx.tenant_id)
    topic = await service.get_topic(topic_id)
    return TopicResponse.model_validate(topic)


@router.patch("/topics/{topic_id}/status", response_model=TopicResponse)
async def update_topic_status(
    topic_id: UUID,
    status: TopicStatus,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.SYLLABUS_UPDATE)),
):
    """Update topic status."""
    service = AcademicService(db, ctx.tenant_id)
    topic = await service.update_topic_status(topic_id, status)
    return TopicResponse.model_validate(topic)


# ==================== Lessons ====================

@router.get("/lessons", response_model=list[LessonResponse])
async def list_lessons(
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    topic_id: Optional[UUID] = None,
    teacher_id: Optional[UUID] = None,
):
    """List lessons with filters."""
    service = AcademicService(db, ctx.tenant_id)
    lessons = await service.get_lessons(topic_id, teacher_id)
    return [LessonResponse.model_validate(l) for l in lessons]


@router.post("/lessons", response_model=LessonResponse)
async def create_lesson(
    data: LessonCreate,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.LESSON_CREATE)),
):
    """Create lesson."""
    service = AcademicService(db, ctx.tenant_id)
    lesson = await service.create_lesson(data, ctx.user.user_id)
    return LessonResponse.model_validate(lesson)


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
):
    """Get lesson by ID."""
    service = AcademicService(db, ctx.tenant_id)
    lesson = await service.get_lesson(lesson_id)
    return LessonResponse.model_validate(lesson)


@router.post("/lessons/{lesson_id}/complete", response_model=LessonResponse)
async def complete_lesson(
    lesson_id: UUID,
    ctx: TenantCtx,
    db: AsyncSession = Depends(get_db),
    _: AuthUser = Depends(require_permissions(Permission.LESSON_UPDATE)),
):
    """Mark lesson as completed."""
    service = AcademicService(db, ctx.tenant_id)
    lesson = await service.complete_lesson(lesson_id)
    return LessonResponse.model_validate(lesson)
