"""
CUSTOS Syllabus Repository

Data access layer for syllabus entities.
"""

from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ResourceNotFoundError, DuplicateError
from app.academics.models.syllabus import (
    Board, ClassLevel, SyllabusSubject, Chapter, SyllabusTopic, TopicWeightage,
)


class SyllabusRepository:
    """Repository for syllabus CRUD operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ========================================
    # Board CRUD
    # ========================================
    
    async def create_board(self, **data) -> Board:
        """Create a new board."""
        # Check for duplicates
        existing = await self._get_board_by_code(data.get("code"))
        if existing:
            raise DuplicateError("Board", "code", data.get("code"))
        
        board = Board(tenant_id=self.tenant_id, **data)
        self.session.add(board)
        await self.session.commit()
        await self.session.refresh(board)
        return board
    
    async def get_board(self, board_id: UUID) -> Board:
        """Get board by ID."""
        query = select(Board).where(
            Board.tenant_id == self.tenant_id,
            Board.id == board_id,
            Board.is_deleted == False,
        )
        result = await self.session.execute(query)
        board = result.scalar_one_or_none()
        if not board:
            raise ResourceNotFoundError("Board", str(board_id))
        return board
    
    async def get_board_with_levels(self, board_id: UUID) -> Board:
        """Get board with class levels loaded."""
        query = select(Board).where(
            Board.tenant_id == self.tenant_id,
            Board.id == board_id,
            Board.is_deleted == False,
        ).options(selectinload(Board.class_levels))
        result = await self.session.execute(query)
        board = result.scalar_one_or_none()
        if not board:
            raise ResourceNotFoundError("Board", str(board_id))
        return board
    
    async def list_boards(
        self,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 50,
    ) -> Tuple[List[Board], int]:
        """List boards with pagination."""
        query = select(Board).where(
            Board.tenant_id == self.tenant_id,
            Board.is_deleted == False,
        )
        
        if is_active is not None:
            query = query.where(Board.is_active == is_active)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(Board.display_order, Board.name).offset(skip).limit(size)
        result = await self.session.execute(query)
        
        return list(result.scalars().all()), total
    
    async def update_board(self, board_id: UUID, **data) -> Board:
        """Update a board."""
        board = await self.get_board(board_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(board, key, value)
        
        board.version += 1
        await self.session.commit()
        await self.session.refresh(board)
        return board
    
    async def delete_board(self, board_id: UUID) -> None:
        """Soft delete a board."""
        board = await self.get_board(board_id)
        board.soft_delete()
        await self.session.commit()
    
    async def _get_board_by_code(self, code: str) -> Optional[Board]:
        """Get board by code."""
        query = select(Board).where(
            Board.tenant_id == self.tenant_id,
            Board.code == code,
            Board.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ========================================
    # ClassLevel CRUD
    # ========================================
    
    async def create_class_level(self, **data) -> ClassLevel:
        """Create a new class level."""
        # Verify board exists
        await self.get_board(data["board_id"])
        
        level = ClassLevel(tenant_id=self.tenant_id, **data)
        self.session.add(level)
        await self.session.commit()
        await self.session.refresh(level)
        return level
    
    async def get_class_level(self, level_id: UUID) -> ClassLevel:
        """Get class level by ID."""
        query = select(ClassLevel).where(
            ClassLevel.tenant_id == self.tenant_id,
            ClassLevel.id == level_id,
            ClassLevel.is_deleted == False,
        )
        result = await self.session.execute(query)
        level = result.scalar_one_or_none()
        if not level:
            raise ResourceNotFoundError("ClassLevel", str(level_id))
        return level
    
    async def get_class_level_with_subjects(self, level_id: UUID) -> ClassLevel:
        """Get class level with subjects loaded."""
        query = select(ClassLevel).where(
            ClassLevel.tenant_id == self.tenant_id,
            ClassLevel.id == level_id,
            ClassLevel.is_deleted == False,
        ).options(selectinload(ClassLevel.subjects))
        result = await self.session.execute(query)
        level = result.scalar_one_or_none()
        if not level:
            raise ResourceNotFoundError("ClassLevel", str(level_id))
        return level
    
    async def list_class_levels(
        self,
        board_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[ClassLevel]:
        """List class levels."""
        query = select(ClassLevel).where(
            ClassLevel.tenant_id == self.tenant_id,
            ClassLevel.is_deleted == False,
        )
        
        if board_id:
            query = query.where(ClassLevel.board_id == board_id)
        if is_active is not None:
            query = query.where(ClassLevel.is_active == is_active)
        
        query = query.order_by(ClassLevel.grade_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_class_level(self, level_id: UUID, **data) -> ClassLevel:
        """Update a class level."""
        level = await self.get_class_level(level_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(level, key, value)
        
        await self.session.commit()
        await self.session.refresh(level)
        return level
    
    async def delete_class_level(self, level_id: UUID) -> None:
        """Soft delete a class level."""
        level = await self.get_class_level(level_id)
        level.soft_delete()
        await self.session.commit()
    
    # ========================================
    # Subject CRUD
    # ========================================
    
    async def create_subject(self, **data) -> SyllabusSubject:
        """Create a new subject."""
        await self.get_class_level(data["class_level_id"])
        
        subject = SyllabusSubject(tenant_id=self.tenant_id, **data)
        self.session.add(subject)
        await self.session.commit()
        await self.session.refresh(subject)
        return subject
    
    async def get_subject(self, subject_id: UUID) -> SyllabusSubject:
        """Get subject by ID."""
        query = select(SyllabusSubject).where(
            SyllabusSubject.tenant_id == self.tenant_id,
            SyllabusSubject.id == subject_id,
            SyllabusSubject.is_deleted == False,
        )
        result = await self.session.execute(query)
        subject = result.scalar_one_or_none()
        if not subject:
            raise ResourceNotFoundError("Subject", str(subject_id))
        return subject
    
    async def get_subject_with_chapters(self, subject_id: UUID) -> SyllabusSubject:
        """Get subject with chapters and topics loaded."""
        query = select(SyllabusSubject).where(
            SyllabusSubject.tenant_id == self.tenant_id,
            SyllabusSubject.id == subject_id,
            SyllabusSubject.is_deleted == False,
        ).options(
            selectinload(SyllabusSubject.chapters).selectinload(Chapter.topics)
        )
        result = await self.session.execute(query)
        subject = result.scalar_one_or_none()
        if not subject:
            raise ResourceNotFoundError("Subject", str(subject_id))
        return subject
    
    async def list_subjects(
        self,
        class_level_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> List[SyllabusSubject]:
        """List subjects."""
        query = select(SyllabusSubject).where(
            SyllabusSubject.tenant_id == self.tenant_id,
            SyllabusSubject.is_deleted == False,
        )
        
        if class_level_id:
            query = query.where(SyllabusSubject.class_level_id == class_level_id)
        if is_active is not None:
            query = query.where(SyllabusSubject.is_active == is_active)
        if category:
            query = query.where(SyllabusSubject.category == category)
        
        query = query.order_by(SyllabusSubject.display_order, SyllabusSubject.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_subject(self, subject_id: UUID, **data) -> SyllabusSubject:
        """Update a subject."""
        subject = await self.get_subject(subject_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(subject, key, value)
        
        subject.version += 1
        await self.session.commit()
        await self.session.refresh(subject)
        return subject
    
    async def delete_subject(self, subject_id: UUID) -> None:
        """Soft delete a subject."""
        subject = await self.get_subject(subject_id)
        subject.soft_delete()
        await self.session.commit()
    
    async def recalculate_subject_hours(self, subject_id: UUID) -> None:
        """Recalculate total hours from chapters."""
        query = select(func.sum(Chapter.estimated_hours)).where(
            Chapter.subject_id == subject_id,
            Chapter.is_deleted == False,
        )
        result = await self.session.execute(query)
        total = result.scalar() or 0
        
        await self.session.execute(
            update(SyllabusSubject).where(
                SyllabusSubject.id == subject_id
            ).values(total_hours=total)
        )
        await self.session.commit()
    
    # ========================================
    # Chapter CRUD
    # ========================================
    
    async def create_chapter(self, **data) -> Chapter:
        """Create a new chapter."""
        await self.get_subject(data["subject_id"])
        
        chapter = Chapter(tenant_id=self.tenant_id, **data)
        self.session.add(chapter)
        await self.session.commit()
        await self.session.refresh(chapter)
        return chapter
    
    async def get_chapter(self, chapter_id: UUID) -> Chapter:
        """Get chapter by ID."""
        query = select(Chapter).where(
            Chapter.tenant_id == self.tenant_id,
            Chapter.id == chapter_id,
            Chapter.is_deleted == False,
        )
        result = await self.session.execute(query)
        chapter = result.scalar_one_or_none()
        if not chapter:
            raise ResourceNotFoundError("Chapter", str(chapter_id))
        return chapter
    
    async def get_chapter_with_topics(self, chapter_id: UUID) -> Chapter:
        """Get chapter with topics loaded."""
        query = select(Chapter).where(
            Chapter.tenant_id == self.tenant_id,
            Chapter.id == chapter_id,
            Chapter.is_deleted == False,
        ).options(selectinload(Chapter.topics))
        result = await self.session.execute(query)
        chapter = result.scalar_one_or_none()
        if not chapter:
            raise ResourceNotFoundError("Chapter", str(chapter_id))
        return chapter
    
    async def list_chapters(
        self,
        subject_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[Chapter]:
        """List chapters for a subject."""
        query = select(Chapter).where(
            Chapter.tenant_id == self.tenant_id,
            Chapter.subject_id == subject_id,
            Chapter.is_deleted == False,
        )
        
        if is_active is not None:
            query = query.where(Chapter.is_active == is_active)
        
        query = query.order_by(Chapter.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_chapter(self, chapter_id: UUID, **data) -> Chapter:
        """Update a chapter."""
        chapter = await self.get_chapter(chapter_id)
        
        for key, value in data.items():
            if value is not None:
                setattr(chapter, key, value)
        
        await self.session.commit()
        await self.session.refresh(chapter)
        
        # Recalculate subject hours
        await self.recalculate_subject_hours(chapter.subject_id)
        
        return chapter
    
    async def delete_chapter(self, chapter_id: UUID) -> None:
        """Soft delete a chapter."""
        chapter = await self.get_chapter(chapter_id)
        subject_id = chapter.subject_id
        chapter.soft_delete()
        await self.session.commit()
        await self.recalculate_subject_hours(subject_id)
    
    async def reorder_chapters(self, subject_id: UUID, chapter_ids: List[UUID]) -> None:
        """Reorder chapters."""
        for order, chapter_id in enumerate(chapter_ids):
            await self.session.execute(
                update(Chapter).where(
                    Chapter.id == chapter_id
                ).values(order=order)
            )
        await self.session.commit()
    
    async def recalculate_chapter_hours(self, chapter_id: UUID) -> None:
        """Recalculate chapter hours from topics."""
        query = select(func.sum(SyllabusTopic.estimated_hours)).where(
            SyllabusTopic.chapter_id == chapter_id,
            SyllabusTopic.is_deleted == False,
        )
        result = await self.session.execute(query)
        total = result.scalar() or 0
        
        await self.session.execute(
            update(Chapter).where(
                Chapter.id == chapter_id
            ).values(estimated_hours=total)
        )
        await self.session.commit()
    
    # ========================================
    # Topic CRUD
    # ========================================
    
    async def create_topic(self, **data) -> SyllabusTopic:
        """Create a new topic."""
        chapter = await self.get_chapter(data["chapter_id"])
        
        topic = SyllabusTopic(tenant_id=self.tenant_id, **data)
        self.session.add(topic)
        await self.session.commit()
        await self.session.refresh(topic)
        
        # Recalculate hours
        await self.recalculate_chapter_hours(chapter.id)
        await self.recalculate_subject_hours(chapter.subject_id)
        
        return topic
    
    async def create_topics_bulk(self, chapter_id: UUID, topics: List[dict]) -> List[SyllabusTopic]:
        """Create multiple topics at once."""
        chapter = await self.get_chapter(chapter_id)
        
        created = []
        for idx, topic_data in enumerate(topics):
            topic = SyllabusTopic(
                tenant_id=self.tenant_id,
                chapter_id=chapter_id,
                order=topic_data.get("order", idx),
                **{k: v for k, v in topic_data.items() if k != "order"},
            )
            self.session.add(topic)
            created.append(topic)
        
        await self.session.commit()
        
        # Refresh all
        for topic in created:
            await self.session.refresh(topic)
        
        # Recalculate hours
        await self.recalculate_chapter_hours(chapter_id)
        await self.recalculate_subject_hours(chapter.subject_id)
        
        return created
    
    async def get_topic(self, topic_id: UUID) -> SyllabusTopic:
        """Get topic by ID."""
        query = select(SyllabusTopic).where(
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.id == topic_id,
            SyllabusTopic.is_deleted == False,
        )
        result = await self.session.execute(query)
        topic = result.scalar_one_or_none()
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        return topic
    
    async def list_topics(
        self,
        chapter_id: UUID,
        is_active: Optional[bool] = None,
    ) -> List[SyllabusTopic]:
        """List topics for a chapter."""
        query = select(SyllabusTopic).where(
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.chapter_id == chapter_id,
            SyllabusTopic.is_deleted == False,
        )
        
        if is_active is not None:
            query = query.where(SyllabusTopic.is_active == is_active)
        
        query = query.order_by(SyllabusTopic.order)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_topic(self, topic_id: UUID, **data) -> SyllabusTopic:
        """Update a topic."""
        topic = await self.get_topic(topic_id)
        old_hours = topic.estimated_hours
        
        for key, value in data.items():
            if value is not None:
                setattr(topic, key, value)
        
        await self.session.commit()
        await self.session.refresh(topic)
        
        # Recalculate if hours changed
        if data.get("estimated_hours") and data["estimated_hours"] != old_hours:
            chapter = await self.get_chapter(topic.chapter_id)
            await self.recalculate_chapter_hours(topic.chapter_id)
            await self.recalculate_subject_hours(chapter.subject_id)
        
        return topic
    
    async def delete_topic(self, topic_id: UUID) -> None:
        """Soft delete a topic."""
        topic = await self.get_topic(topic_id)
        chapter_id = topic.chapter_id
        topic.soft_delete()
        await self.session.commit()
        
        chapter = await self.get_chapter(chapter_id)
        await self.recalculate_chapter_hours(chapter_id)
        await self.recalculate_subject_hours(chapter.subject_id)
    
    async def reorder_topics(self, chapter_id: UUID, topic_ids: List[UUID]) -> None:
        """Reorder topics."""
        for order, topic_id in enumerate(topic_ids):
            await self.session.execute(
                update(SyllabusTopic).where(
                    SyllabusTopic.id == topic_id
                ).values(order=order)
            )
        await self.session.commit()
    
    # ========================================
    # TopicWeightage CRUD
    # ========================================
    
    async def create_weightage(self, **data) -> TopicWeightage:
        """Create topic weightage."""
        await self.get_topic(data["topic_id"])
        
        weightage = TopicWeightage(tenant_id=self.tenant_id, **data)
        self.session.add(weightage)
        await self.session.commit()
        await self.session.refresh(weightage)
        return weightage
    
    async def get_weightages(self, topic_id: UUID) -> List[TopicWeightage]:
        """Get weightages for a topic."""
        query = select(TopicWeightage).where(
            TopicWeightage.tenant_id == self.tenant_id,
            TopicWeightage.topic_id == topic_id,
            TopicWeightage.is_deleted == False,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_weightage(self, weightage_id: UUID, **data) -> TopicWeightage:
        """Update topic weightage."""
        query = select(TopicWeightage).where(
            TopicWeightage.tenant_id == self.tenant_id,
            TopicWeightage.id == weightage_id,
        )
        result = await self.session.execute(query)
        weightage = result.scalar_one_or_none()
        if not weightage:
            raise ResourceNotFoundError("TopicWeightage", str(weightage_id))
        
        for key, value in data.items():
            if value is not None:
                setattr(weightage, key, value)
        
        await self.session.commit()
        await self.session.refresh(weightage)
        return weightage
    
    async def delete_weightage(self, weightage_id: UUID) -> None:
        """Delete topic weightage."""
        query = select(TopicWeightage).where(
            TopicWeightage.tenant_id == self.tenant_id,
            TopicWeightage.id == weightage_id,
        )
        result = await self.session.execute(query)
        weightage = result.scalar_one_or_none()
        if weightage:
            weightage.soft_delete()
            await self.session.commit()
