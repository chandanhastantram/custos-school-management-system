"""
CUSTOS Syllabus Router

API endpoints for syllabus management.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import CurrentUser, require_permission
from app.users.rbac import Permission
from app.academics.services.syllabus_service import SyllabusService
from app.academics.schemas.syllabus import (
    BoardCreate, BoardUpdate, BoardResponse, BoardWithLevels,
    ClassLevelCreate, ClassLevelUpdate, ClassLevelResponse, ClassLevelWithSubjects,
    SubjectCreate, SubjectUpdate, SubjectResponse, SubjectWithChapters,
    ChapterCreate, ChapterUpdate, ChapterResponse, ChapterWithTopics,
    TopicCreate, TopicUpdate, TopicResponse, BulkTopicCreate,
    TopicWeightageCreate, TopicWeightageUpdate, TopicWeightageResponse,
    ReorderRequest,
)


router = APIRouter(tags=["Syllabus"])


# ============================================
# Board Endpoints
# ============================================

@router.get("/boards", response_model=dict)
async def list_boards(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List all boards."""
    service = SyllabusService(db, user.tenant_id)
    boards, total = await service.list_boards(is_active, page, size)
    return {
        "items": boards,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/boards", response_model=BoardResponse, status_code=201)
async def create_board(
    data: BoardCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create a new board."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_board(data)


@router.get("/boards/{board_id}", response_model=BoardWithLevels)
async def get_board(
    board_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_levels: bool = True,
):
    """Get board by ID."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_board(board_id, include_levels)


@router.patch("/boards/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: UUID,
    data: BoardUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update a board."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_board(board_id, data)


@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete a board."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_board(board_id)


# ============================================
# ClassLevel Endpoints
# ============================================

@router.get("/class-levels", response_model=List[ClassLevelResponse])
async def list_class_levels(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    board_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
):
    """List class levels."""
    service = SyllabusService(db, user.tenant_id)
    return await service.list_class_levels(board_id, is_active)


@router.post("/class-levels", response_model=ClassLevelResponse, status_code=201)
async def create_class_level(
    data: ClassLevelCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create a new class level."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_class_level(data)


@router.get("/class-levels/{level_id}", response_model=ClassLevelWithSubjects)
async def get_class_level(
    level_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_subjects: bool = True,
):
    """Get class level by ID."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_class_level(level_id, include_subjects)


@router.patch("/class-levels/{level_id}", response_model=ClassLevelResponse)
async def update_class_level(
    level_id: UUID,
    data: ClassLevelUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update a class level."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_class_level(level_id, data)


@router.delete("/class-levels/{level_id}", status_code=204)
async def delete_class_level(
    level_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete a class level."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_class_level(level_id)


# ============================================
# Subject Endpoints
# ============================================

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    class_level_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
):
    """List subjects."""
    service = SyllabusService(db, user.tenant_id)
    return await service.list_subjects(class_level_id, is_active, category)


@router.post("/subjects", response_model=SubjectResponse, status_code=201)
async def create_subject(
    data: SubjectCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create a new subject."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_subject(data)


@router.get("/subjects/{subject_id}", response_model=SubjectWithChapters)
async def get_subject(
    subject_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_chapters: bool = True,
):
    """Get subject by ID with chapters."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_subject(subject_id, include_chapters)


@router.patch("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    data: SubjectUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update a subject."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_subject(subject_id, data)


@router.delete("/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete a subject."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_subject(subject_id)


# ============================================
# Chapter Endpoints
# ============================================

@router.get("/subjects/{subject_id}/chapters", response_model=List[ChapterResponse])
async def list_chapters(
    subject_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = None,
):
    """List chapters for a subject."""
    service = SyllabusService(db, user.tenant_id)
    return await service.list_chapters(subject_id, is_active)


@router.post("/chapters", response_model=ChapterResponse, status_code=201)
async def create_chapter(
    data: ChapterCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create a new chapter."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_chapter(data)


@router.get("/chapters/{chapter_id}", response_model=ChapterWithTopics)
async def get_chapter(
    chapter_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    include_topics: bool = True,
):
    """Get chapter by ID with topics."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_chapter(chapter_id, include_topics)


@router.patch("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: UUID,
    data: ChapterUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update a chapter."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_chapter(chapter_id, data)


@router.delete("/chapters/{chapter_id}", status_code=204)
async def delete_chapter(
    chapter_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete a chapter."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_chapter(chapter_id)


@router.post("/subjects/{subject_id}/chapters/reorder", status_code=204)
async def reorder_chapters(
    subject_id: UUID,
    data: ReorderRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Reorder chapters in a subject."""
    service = SyllabusService(db, user.tenant_id)
    await service.reorder_chapters(subject_id, data.items)


# ============================================
# Topic Endpoints
# ============================================

@router.get("/chapters/{chapter_id}/topics", response_model=List[TopicResponse])
async def list_topics(
    chapter_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    is_active: Optional[bool] = None,
):
    """List topics for a chapter."""
    service = SyllabusService(db, user.tenant_id)
    return await service.list_topics(chapter_id, is_active)


@router.post("/topics", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create a new topic."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_topic(data)


@router.post("/topics/bulk", response_model=List[TopicResponse], status_code=201)
async def create_topics_bulk(
    data: BulkTopicCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create multiple topics at once."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_topics_bulk(data)


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get topic by ID."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_topic(topic_id)


@router.patch("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    data: TopicUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update a topic."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_topic(topic_id, data)


@router.delete("/topics/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete a topic."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_topic(topic_id)


@router.post("/chapters/{chapter_id}/topics/reorder", status_code=204)
async def reorder_topics(
    chapter_id: UUID,
    data: ReorderRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Reorder topics in a chapter."""
    service = SyllabusService(db, user.tenant_id)
    await service.reorder_topics(chapter_id, data.items)


# ============================================
# Topic Weightage Endpoints
# ============================================

@router.get("/topics/{topic_id}/weightages", response_model=List[TopicWeightageResponse])
async def list_weightages(
    topic_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """List weightages for a topic."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_weightages(topic_id)


@router.post("/weightages", response_model=TopicWeightageResponse, status_code=201)
async def create_weightage(
    data: TopicWeightageCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_CREATE)),
):
    """Create topic weightage."""
    service = SyllabusService(db, user.tenant_id)
    return await service.create_weightage(data)


@router.patch("/weightages/{weightage_id}", response_model=TopicWeightageResponse)
async def update_weightage(
    weightage_id: UUID,
    data: TopicWeightageUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_UPDATE)),
):
    """Update topic weightage."""
    service = SyllabusService(db, user.tenant_id)
    return await service.update_weightage(weightage_id, data)


@router.delete("/weightages/{weightage_id}", status_code=204)
async def delete_weightage(
    weightage_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission(Permission.SYLLABUS_DELETE)),
):
    """Delete topic weightage."""
    service = SyllabusService(db, user.tenant_id)
    await service.delete_weightage(weightage_id)


# ============================================
# Full Syllabus & Stats
# ============================================

@router.get("/full/{board_id}")
async def get_full_syllabus(
    board_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete syllabus tree for a board.
    
    Returns full hierarchy: Board → ClassLevels → Subjects → Chapters → Topics
    """
    service = SyllabusService(db, user.tenant_id)
    return await service.get_full_syllabus(board_id)


@router.get("/stats")
async def get_syllabus_stats(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    board_id: Optional[UUID] = None,
):
    """Get syllabus statistics."""
    service = SyllabusService(db, user.tenant_id)
    return await service.get_syllabus_stats(board_id)
