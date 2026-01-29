"""
CUSTOS AI Quality Service

Handles question quality, duplicate detection, and curriculum alignment.
"""

import re
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.quality_models import (
    PromptVersion,
    PromptType,
    QuestionQualityRating,
    QuestionDuplicate,
    CurriculumAlignment,
)
from app.academics.models.questions import Question


class AIQualityService:
    """
    AI Quality Management Service.
    
    Features:
    - Prompt version management
    - Question quality ratings
    - Duplicate detection
    - Curriculum alignment scoring
    """
    
    # Similarity threshold for duplicates
    DUPLICATE_THRESHOLD = 0.85
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    # ============================================
    # Prompt Version Management
    # ============================================
    
    async def get_active_prompt(
        self,
        prompt_type: PromptType,
    ) -> Optional[PromptVersion]:
        """Get the active prompt version for a type."""
        query = select(PromptVersion).where(
            PromptVersion.tenant_id == self.tenant_id,
            PromptVersion.prompt_type == prompt_type,
            PromptVersion.is_active == True,
            PromptVersion.deleted_at.is_(None),
        ).order_by(PromptVersion.traffic_percentage.desc())
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_default_prompt(
        self,
        prompt_type: PromptType,
    ) -> Optional[PromptVersion]:
        """Get the default (system) prompt for a type."""
        query = select(PromptVersion).where(
            PromptVersion.prompt_type == prompt_type,
            PromptVersion.is_default == True,
            PromptVersion.deleted_at.is_(None),
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def record_prompt_usage(
        self,
        prompt_id: UUID,
        success: bool,
        tokens_used: int = 0,
        quality_score: float = 0.0,
    ) -> None:
        """Record usage metrics for a prompt."""
        query = select(PromptVersion).where(
            PromptVersion.id == prompt_id,
            PromptVersion.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        prompt = result.scalar_one_or_none()
        
        if prompt:
            prompt.total_uses += 1
            if success:
                prompt.success_count += 1
            else:
                prompt.failure_count += 1
            
            # Update running averages
            if tokens_used > 0:
                total = prompt.total_uses
                prompt.avg_tokens_used = (
                    (prompt.avg_tokens_used * (total - 1) + tokens_used) / total
                )
            
            if quality_score > 0:
                total = prompt.success_count
                if total > 0:
                    prompt.avg_quality_score = (
                        (prompt.avg_quality_score * (total - 1) + quality_score) / total
                    )
            
            await self.session.flush()
    
    # ============================================
    # Question Quality Ratings
    # ============================================
    
    async def rate_question(
        self,
        question_id: UUID,
        teacher_id: UUID,
        accuracy: int,
        clarity: int,
        difficulty_appropriate: int,
        curriculum_aligned: int,
        feedback: Optional[str] = None,
        gen_job_id: Optional[UUID] = None,
    ) -> QuestionQualityRating:
        """Rate an AI-generated question."""
        # Calculate overall score
        overall = (accuracy + clarity + difficulty_appropriate + curriculum_aligned) / 4.0
        
        rating = QuestionQualityRating(
            tenant_id=self.tenant_id,
            question_id=question_id,
            teacher_id=teacher_id,
            accuracy_score=accuracy,
            clarity_score=clarity,
            difficulty_appropriate=difficulty_appropriate,
            curriculum_aligned=curriculum_aligned,
            overall_score=overall,
            feedback=feedback,
            is_approved=overall >= 3.0,
            is_flagged=overall < 2.0,
            gen_job_id=gen_job_id,
        )
        
        self.session.add(rating)
        await self.session.flush()
        
        return rating
    
    async def get_question_ratings(
        self,
        question_id: UUID,
    ) -> List[QuestionQualityRating]:
        """Get all ratings for a question."""
        query = select(QuestionQualityRating).where(
            QuestionQualityRating.question_id == question_id,
            QuestionQualityRating.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_avg_rating(
        self,
        question_id: UUID,
    ) -> float:
        """Get average rating for a question."""
        query = select(func.avg(QuestionQualityRating.overall_score)).where(
            QuestionQualityRating.question_id == question_id,
            QuestionQualityRating.deleted_at.is_(None),
        )
        result = await self.session.scalar(query)
        return result or 0.0
    
    # ============================================
    # Duplicate Detection
    # ============================================
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
        return text
    
    def _word_set(self, text: str) -> set:
        """Convert text to word set."""
        return set(self._normalize_text(text).split())
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    async def check_duplicate(
        self,
        question_text: str,
        topic_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
    ) -> List[Tuple[UUID, float]]:
        """
        Check if a question is a duplicate of existing questions.
        
        Returns list of (question_id, similarity_score) for potential duplicates.
        """
        # Build query
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.deleted_at.is_(None),
        )
        
        if topic_id:
            query = query.where(Question.topic_id == topic_id)
        if subject_id:
            query = query.where(Question.subject_id == subject_id)
        
        result = await self.session.execute(query)
        existing = result.scalars().all()
        
        # Compare with existing questions
        new_words = self._word_set(question_text)
        duplicates = []
        
        for q in existing:
            existing_words = self._word_set(q.question_text)
            similarity = self._jaccard_similarity(new_words, existing_words)
            
            if similarity >= self.DUPLICATE_THRESHOLD:
                duplicates.append((q.id, similarity))
        
        # Sort by similarity descending
        duplicates.sort(key=lambda x: x[1], reverse=True)
        
        return duplicates
    
    async def record_duplicate(
        self,
        original_id: UUID,
        duplicate_id: UUID,
        similarity: float,
    ) -> QuestionDuplicate:
        """Record a detected duplicate."""
        dup = QuestionDuplicate(
            tenant_id=self.tenant_id,
            original_question_id=original_id,
            duplicate_question_id=duplicate_id,
            similarity_score=similarity,
            detected_by="system",
        )
        self.session.add(dup)
        await self.session.flush()
        return dup
    
    async def get_duplicates(
        self,
        question_id: UUID,
    ) -> List[QuestionDuplicate]:
        """Get duplicate records for a question."""
        query = select(QuestionDuplicate).where(
            (QuestionDuplicate.original_question_id == question_id) |
            (QuestionDuplicate.duplicate_question_id == question_id),
            QuestionDuplicate.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ============================================
    # Curriculum Alignment
    # ============================================
    
    async def calculate_alignment(
        self,
        question_id: UUID,
        topic_id: UUID,
    ) -> CurriculumAlignment:
        """
        Calculate curriculum alignment for a question.
        """
        from app.academics.models.syllabus import SyllabusTopic
        
        # Get question
        q_query = select(Question).where(Question.id == question_id)
        q_result = await self.session.execute(q_query)
        question = q_result.scalar_one_or_none()
        
        # Get topic
        t_query = select(SyllabusTopic).where(SyllabusTopic.id == topic_id)
        t_result = await self.session.execute(t_query)
        topic = t_result.scalar_one_or_none()
        
        if not question or not topic:
            return None
        
        # Calculate content match
        q_words = self._word_set(question.question_text)
        t_words = self._word_set(topic.name + " " + (topic.description or ""))
        content_match = self._jaccard_similarity(q_words, t_words)
        
        # Calculate keyword coverage
        keywords = []
        if hasattr(topic, 'keywords') and topic.keywords:
            keywords = topic.keywords if isinstance(topic.keywords, list) else []
        
        keyword_coverage = 0.0
        if keywords:
            matched = sum(1 for kw in keywords if kw.lower() in question.question_text.lower())
            keyword_coverage = matched / len(keywords)
        
        # Bloom level match (simplified)
        bloom_match = 0.5  # Default middle value
        if hasattr(topic, 'bloom_level') and hasattr(question, 'bloom_level'):
            if topic.bloom_level == question.bloom_level:
                bloom_match = 1.0
        
        # Overall alignment
        overall = (content_match * 0.4 + keyword_coverage * 0.3 + bloom_match * 0.3)
        
        alignment = CurriculumAlignment(
            tenant_id=self.tenant_id,
            question_id=question_id,
            topic_id=topic_id,
            content_match=content_match,
            bloom_level_match=bloom_match,
            keyword_coverage=keyword_coverage,
            overall_alignment=overall,
            is_aligned=overall >= 0.5,
            needs_review=overall < 0.3,
        )
        
        self.session.add(alignment)
        await self.session.flush()
        
        return alignment
    
    async def get_alignment(
        self,
        question_id: UUID,
    ) -> Optional[CurriculumAlignment]:
        """Get alignment record for a question."""
        query = select(CurriculumAlignment).where(
            CurriculumAlignment.question_id == question_id,
            CurriculumAlignment.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    # ============================================
    # Batch Operations
    # ============================================
    
    async def scan_for_duplicates(
        self,
        topic_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> int:
        """Scan and record duplicates among questions."""
        query = select(Question).where(
            Question.tenant_id == self.tenant_id,
            Question.deleted_at.is_(None),
        )
        
        if topic_id:
            query = query.where(Question.topic_id == topic_id)
        
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        questions = list(result.scalars().all())
        
        duplicates_found = 0
        
        for i, q1 in enumerate(questions):
            q1_words = self._word_set(q1.question_text)
            
            for q2 in questions[i+1:]:
                q2_words = self._word_set(q2.question_text)
                similarity = self._jaccard_similarity(q1_words, q2_words)
                
                if similarity >= self.DUPLICATE_THRESHOLD:
                    await self.record_duplicate(q1.id, q2.id, similarity)
                    duplicates_found += 1
        
        await self.session.flush()
        return duplicates_found
