"""
CUSTOS Syllabus Service

Business logic for syllabus management.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.academics.repositories.syllabus_repo import SyllabusRepository
from app.academics.models.syllabus import (
    Board, ClassLevel, SyllabusSubject, Chapter, SyllabusTopic, TopicWeightage,
)
from app.academics.schemas.syllabus import (
    BoardCreate, BoardUpdate,
    ClassLevelCreate, ClassLevelUpdate,
    SubjectCreate, SubjectUpdate,
    ChapterCreate, ChapterUpdate,
    TopicCreate, TopicUpdate, BulkTopicCreate,
    TopicWeightageCreate, TopicWeightageUpdate,
)


class SyllabusService:
    """
    Syllabus management service.
    
    Handles:
    - Board management
    - ClassLevel management
    - Subject management
    - Chapter management
    - Topic management
    - Weightage management
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = SyllabusRepository(session, tenant_id)
    
    # ========================================
    # Board Operations
    # ========================================
    
    async def create_board(self, data: BoardCreate) -> Board:
        """Create a new board."""
        return await self.repo.create_board(**data.model_dump())
    
    async def get_board(self, board_id: UUID, include_levels: bool = False) -> Board:
        """Get board by ID."""
        if include_levels:
            return await self.repo.get_board_with_levels(board_id)
        return await self.repo.get_board(board_id)
    
    async def list_boards(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Board], int]:
        """List boards."""
        return await self.repo.list_boards(is_active, page, size)
    
    async def update_board(self, board_id: UUID, data: BoardUpdate) -> Board:
        """Update a board."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_board(board_id, **update_data)
    
    async def delete_board(self, board_id: UUID) -> None:
        """Delete a board."""
        await self.repo.delete_board(board_id)
    
    # ========================================
    # ClassLevel Operations
    # ========================================
    
    async def create_class_level(self, data: ClassLevelCreate) -> ClassLevel:
        """Create a new class level."""
        return await self.repo.create_class_level(**data.model_dump())
    
    async def get_class_level(
        self, 
        level_id: UUID, 
        include_subjects: bool = False,
    ) -> ClassLevel:
        """Get class level by ID."""
        if include_subjects:
            return await self.repo.get_class_level_with_subjects(level_id)
        return await self.repo.get_class_level(level_id)
    
    async def list_class_levels(
        self,
        board_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[ClassLevel]:
        """List class levels."""
        return await self.repo.list_class_levels(board_id, is_active)
    
    async def update_class_level(self, level_id: UUID, data: ClassLevelUpdate) -> ClassLevel:
        """Update a class level."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_class_level(level_id, **update_data)
    
    async def delete_class_level(self, level_id: UUID) -> None:
        """Delete a class level."""
        await self.repo.delete_class_level(level_id)
    
    # ========================================
    # Subject Operations
    # ========================================
    
    async def create_subject(self, data: SubjectCreate) -> SyllabusSubject:
        """Create a new subject."""
        return await self.repo.create_subject(**data.model_dump())
    
    async def get_subject(
        self, 
        subject_id: UUID, 
        include_chapters: bool = False,
    ) -> SyllabusSubject:
        """Get subject by ID."""
        if include_chapters:
            return await self.repo.get_subject_with_chapters(subject_id)
        return await self.repo.get_subject(subject_id)
    
    async def list_subjects(
        self,
        class_level_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> List[SyllabusSubject]:
        """List subjects."""
        return await self.repo.list_subjects(class_level_id, is_active, category)
    
    async def update_subject(self, subject_id: UUID, data: SubjectUpdate) -> SyllabusSubject:
        """Update a subject."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_subject(subject_id, **update_data)
    
    async def delete_subject(self, subject_id: UUID) -> None:
        """Delete a subject."""
        await self.repo.delete_subject(subject_id)
    
    # ========================================
    # Chapter Operations
    # ========================================
    
    async def create_chapter(self, data: ChapterCreate) -> Chapter:
        """Create a new chapter."""
        return await self.repo.create_chapter(**data.model_dump())
    
    async def get_chapter(
        self, 
        chapter_id: UUID, 
        include_topics: bool = False,
    ) -> Chapter:
        """Get chapter by ID."""
        if include_topics:
            return await self.repo.get_chapter_with_topics(chapter_id)
        return await self.repo.get_chapter(chapter_id)
    
    async def list_chapters(
        self,
        subject_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[Chapter]:
        """List chapters for a subject."""
        return await self.repo.list_chapters(subject_id, is_active)
    
    async def update_chapter(self, chapter_id: UUID, data: ChapterUpdate) -> Chapter:
        """Update a chapter."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_chapter(chapter_id, **update_data)
    
    async def delete_chapter(self, chapter_id: UUID) -> None:
        """Delete a chapter."""
        await self.repo.delete_chapter(chapter_id)
    
    async def reorder_chapters(self, subject_id: UUID, chapter_ids: List[UUID]) -> None:
        """Reorder chapters."""
        await self.repo.reorder_chapters(subject_id, chapter_ids)
    
    # ========================================
    # Topic Operations
    # ========================================
    
    async def create_topic(self, data: TopicCreate) -> SyllabusTopic:
        """Create a new topic."""
        return await self.repo.create_topic(**data.model_dump())
    
    async def create_topics_bulk(self, data: BulkTopicCreate) -> List[SyllabusTopic]:
        """Create multiple topics at once."""
        topics_data = [t.model_dump() for t in data.topics]
        return await self.repo.create_topics_bulk(data.chapter_id, topics_data)
    
    async def get_topic(self, topic_id: UUID) -> SyllabusTopic:
        """Get topic by ID."""
        return await self.repo.get_topic(topic_id)
    
    async def list_topics(
        self,
        chapter_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[SyllabusTopic]:
        """List topics for a chapter."""
        return await self.repo.list_topics(chapter_id, is_active)
    
    async def update_topic(self, topic_id: UUID, data: TopicUpdate) -> SyllabusTopic:
        """Update a topic."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_topic(topic_id, **update_data)
    
    async def delete_topic(self, topic_id: UUID) -> None:
        """Delete a topic."""
        await self.repo.delete_topic(topic_id)
    
    async def reorder_topics(self, chapter_id: UUID, topic_ids: List[UUID]) -> None:
        """Reorder topics."""
        await self.repo.reorder_topics(chapter_id, topic_ids)
    
    # ========================================
    # Weightage Operations
    # ========================================
    
    async def create_weightage(self, data: TopicWeightageCreate) -> TopicWeightage:
        """Create topic weightage."""
        return await self.repo.create_weightage(**data.model_dump())
    
    async def get_weightages(self, topic_id: UUID) -> List[TopicWeightage]:
        """Get weightages for a topic."""
        return await self.repo.get_weightages(topic_id)
    
    async def update_weightage(
        self, 
        weightage_id: UUID, 
        data: TopicWeightageUpdate,
    ) -> TopicWeightage:
        """Update topic weightage."""
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update_weightage(weightage_id, **update_data)
    
    async def delete_weightage(self, weightage_id: UUID) -> None:
        """Delete topic weightage."""
        await self.repo.delete_weightage(weightage_id)
    
    # ========================================
    # Full Syllabus View
    # ========================================
    
    async def get_full_syllabus(self, board_id: UUID) -> dict:
        """
        Get complete syllabus tree for a board.
        
        Returns hierarchical structure:
        Board → ClassLevels → Subjects → Chapters → Topics
        """
        board = await self.repo.get_board_with_levels(board_id)
        
        result = {
            "board": board,
            "class_levels": [],
        }
        
        for level in board.class_levels:
            if level.is_deleted:
                continue
            
            level_with_subjects = await self.repo.get_class_level_with_subjects(level.id)
            level_data = {
                "level": level_with_subjects,
                "subjects": [],
            }
            
            for subject in level_with_subjects.subjects:
                if subject.is_deleted:
                    continue
                
                subject_with_chapters = await self.repo.get_subject_with_chapters(subject.id)
                level_data["subjects"].append(subject_with_chapters)
            
            result["class_levels"].append(level_data)
        
        return result
    
    async def get_syllabus_stats(self, board_id: Optional[UUID] = None) -> dict:
        """
        Get syllabus statistics.
        """
        from sqlalchemy import select, func
        
        stats = {
            "total_boards": 0,
            "total_class_levels": 0,
            "total_subjects": 0,
            "total_chapters": 0,
            "total_topics": 0,
            "total_hours": 0,
        }
        
        # Count boards
        query = select(func.count()).select_from(Board).where(
            Board.tenant_id == self.tenant_id,
            Board.is_deleted == False,
        )
        if board_id:
            query = query.where(Board.id == board_id)
        stats["total_boards"] = (await self.session.execute(query)).scalar() or 0
        
        # Count class levels
        query = select(func.count()).select_from(ClassLevel).where(
            ClassLevel.tenant_id == self.tenant_id,
            ClassLevel.is_deleted == False,
        )
        stats["total_class_levels"] = (await self.session.execute(query)).scalar() or 0
        
        # Count subjects
        query = select(func.count()).select_from(SyllabusSubject).where(
            SyllabusSubject.tenant_id == self.tenant_id,
            SyllabusSubject.is_deleted == False,
        )
        stats["total_subjects"] = (await self.session.execute(query)).scalar() or 0
        
        # Count chapters
        query = select(func.count()).select_from(Chapter).where(
            Chapter.tenant_id == self.tenant_id,
            Chapter.is_deleted == False,
        )
        stats["total_chapters"] = (await self.session.execute(query)).scalar() or 0
        
        # Count topics
        query = select(func.count()).select_from(SyllabusTopic).where(
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.is_deleted == False,
        )
        stats["total_topics"] = (await self.session.execute(query)).scalar() or 0
        
        # Sum hours
        query = select(func.sum(SyllabusSubject.total_hours)).where(
            SyllabusSubject.tenant_id == self.tenant_id,
            SyllabusSubject.is_deleted == False,
        )
        stats["total_hours"] = (await self.session.execute(query)).scalar() or 0
        
        return stats
