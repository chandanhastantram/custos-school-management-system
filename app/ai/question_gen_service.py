"""
CUSTOS AI Question Generation Service

Generates questions from syllabus topics and saves them to QuestionBank.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, UsageLimitExceededError, ValidationError
from app.ai.models import (
    AIQuestionGenJob, 
    AIJobStatus, 
    QuestionGenDifficulty, 
    QuestionGenType,
)
from app.ai.quota_manager import AIQuotaManager
from app.ai.providers.openai import OpenAIProvider
from app.academics.models.questions import Question, QuestionType, DifficultyLevel, BloomLevel, QuestionStatus
from app.academics.models.syllabus import SyllabusTopic, Chapter, SyllabusSubject


logger = logging.getLogger("custos.ai.question_gen")


# Mapping from AI difficulty to Question difficulty
DIFFICULTY_MAP = {
    QuestionGenDifficulty.EASY: DifficultyLevel.EASY,
    QuestionGenDifficulty.MEDIUM: DifficultyLevel.MEDIUM,
    QuestionGenDifficulty.HARD: DifficultyLevel.HARD,
    QuestionGenDifficulty.MIXED: DifficultyLevel.MEDIUM,  # Default for mixed
}

# Mapping from AI question type to Question type
QUESTION_TYPE_MAP = {
    QuestionGenType.MCQ: QuestionType.MCQ,
    QuestionGenType.TRUE_FALSE: QuestionType.TRUE_FALSE,
    QuestionGenType.SHORT_ANSWER: QuestionType.SHORT_ANSWER,
    QuestionGenType.LONG_ANSWER: QuestionType.LONG_ANSWER,
    QuestionGenType.NUMERICAL: QuestionType.SHORT_ANSWER,  # Map to short answer
    QuestionGenType.FILL_BLANK: QuestionType.FILL_BLANK,
    QuestionGenType.MIXED: QuestionType.MCQ,  # Default for mixed
}


class AIQuestionGenService:
    """
    AI Question Generation Service.
    
    Generates questions from syllabus topics using AI and saves to QuestionBank.
    
    Features:
    - Quota enforcement per subscription tier
    - Topic context extraction
    - AI question generation
    - Question validation
    - Batch creation in QuestionBank
    - Job tracking with snapshots
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.provider = OpenAIProvider()
        self.quota_manager = AIQuotaManager(session, tenant_id)
    
    async def generate_questions(
        self,
        request: dict,
        teacher_id: UUID,
    ) -> dict:
        """
        Generate AI questions from a syllabus topic.
        
        Args:
            request: {
                class_id, subject_id, topic_id,
                difficulty, question_type, count
            }
            teacher_id: The requesting teacher's ID
        
        Returns:
            {job_id, status, questions_created, question_ids}
        """
        class_id = request["class_id"]
        subject_id = request["subject_id"] 
        topic_id = request["topic_id"]
        difficulty = QuestionGenDifficulty(request.get("difficulty", "mixed"))
        question_type = QuestionGenType(request.get("question_type", "mcq"))
        count = min(request.get("count", 10), 50)  # Max 50 per request
        
        # 1. Check quota
        await self._check_quota(count)
        
        # 2. Load topic context
        topic = await self._get_topic_with_context(topic_id)
        if not topic:
            raise ResourceNotFoundError("Topic", str(topic_id))
        
        # 3. Build input snapshot
        input_snapshot = self._build_input_snapshot(topic, difficulty, question_type, count)
        
        # 4. Create job record (PENDING)
        job = AIQuestionGenJob(
            tenant_id=self.tenant_id,
            requested_by=teacher_id,
            topic_id=topic_id,
            subject_id=subject_id,
            class_id=class_id,
            difficulty=difficulty,
            question_type=question_type,
            count=count,
            status=AIJobStatus.PENDING,
            input_snapshot=input_snapshot,
        )
        self.session.add(job)
        await self.session.flush()
        
        try:
            # 5. Update status to RUNNING
            job.status = AIJobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            await self.session.flush()
            
            # 6. Call AI provider
            ai_response = await self._generate_with_ai(input_snapshot)
            
            # 7. Store output snapshot
            job.output_snapshot = ai_response
            job.tokens_used = ai_response.get("tokens_used", 0)
            
            # 8. Validate and create questions
            questions = await self._create_questions(
                ai_response=ai_response,
                topic=topic,
                subject_id=subject_id,
                teacher_id=teacher_id,
                difficulty=difficulty,
                question_type=question_type,
            )
            
            # 9. Update job with results
            job.status = AIJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.questions_created = len(questions)
            job.created_question_ids = [str(q.id) for q in questions]
            
            # 10. Increment usage
            await self._increment_usage(len(questions))
            
            await self.session.commit()
            
            return {
                "job_id": str(job.id),
                "status": job.status.value,
                "questions_created": job.questions_created,
                "question_ids": job.created_question_ids,
                "tokens_used": job.tokens_used,
            }
            
        except Exception as e:
            logger.exception(f"Question generation failed: {e}")
            job.status = AIJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            raise
    
    async def _check_quota(self, count: int) -> None:
        """Check if tenant has quota for question generation."""
        await self.quota_manager.check_quota("question_gen", count=1)
        
        # Also check max questions per generation
        limits = await self.quota_manager.get_limits()
        max_per_gen = limits.get("max_questions_per_gen", 20)
        
        if count > max_per_gen:
            tier = await self.quota_manager.get_tenant_tier()
            raise UsageLimitExceededError(
                f"questions per generation ({tier.value})",
                count,
                max_per_gen,
            )
    
    async def _get_topic_with_context(self, topic_id: UUID) -> Optional[SyllabusTopic]:
        """Load topic with chapter and subject context."""
        query = (
            select(SyllabusTopic)
            .where(
                SyllabusTopic.id == topic_id,
                SyllabusTopic.tenant_id == self.tenant_id,
                SyllabusTopic.is_active == True,
            )
        )
        result = await self.session.execute(query)
        topic = result.scalar_one_or_none()
        
        # Load chapter and subject via relationships
        if topic:
            await self.session.refresh(topic, ["chapter"])
            if topic.chapter:
                await self.session.refresh(topic.chapter, ["subject"])
        
        return topic
    
    def _build_input_snapshot(
        self,
        topic: SyllabusTopic,
        difficulty: QuestionGenDifficulty,
        question_type: QuestionGenType,
        count: int,
    ) -> dict:
        """Build input snapshot for AI and auditing."""
        chapter = topic.chapter
        subject = chapter.subject if chapter else None
        
        return {
            "topic": {
                "id": str(topic.id),
                "name": topic.name,
                "description": topic.description,
                "keywords": topic.keywords,
                "learning_objectives": topic.learning_objectives,
            },
            "chapter": {
                "id": str(chapter.id) if chapter else None,
                "name": chapter.name if chapter else None,
            },
            "subject": {
                "id": str(subject.id) if subject else None,
                "name": subject.name if subject else None,
            },
            "parameters": {
                "difficulty": difficulty.value,
                "question_type": question_type.value,
                "count": count,
            },
        }
    
    async def _generate_with_ai(self, input_snapshot: dict) -> dict:
        """Call AI provider to generate questions."""
        topic = input_snapshot["topic"]
        chapter = input_snapshot["chapter"]
        subject = input_snapshot["subject"]
        params = input_snapshot["parameters"]
        
        # Build the prompt
        prompt = self._build_prompt(topic, chapter, subject, params)
        
        # Define expected schema
        schema = self._get_response_schema(params["question_type"])
        
        # Call AI
        try:
            result = await self.provider.generate_structured(prompt, schema)
            return {
                "questions": result.get("questions", []),
                "tokens_used": 0,  # Would get from response if available
            }
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            raise ValidationError(f"AI generation failed: {str(e)}")
    
    def _build_prompt(
        self,
        topic: dict,
        chapter: dict,
        subject: dict,
        params: dict,
    ) -> str:
        """Build the AI prompt for question generation."""
        difficulty = params["difficulty"]
        q_type = params["question_type"]
        count = params["count"]
        
        # Difficulty description
        difficulty_desc = {
            "easy": "basic recall and understanding questions suitable for beginners",
            "medium": "application-level questions requiring understanding of concepts",
            "hard": "analysis and synthesis questions requiring deep understanding",
            "mixed": "a mix of easy (30%), medium (50%), and hard (20%) questions",
        }
        
        # Question type instructions
        type_instructions = {
            "mcq": """Each question must have:
- question: The question text
- options: Array of 4 options labeled A, B, C, D
- correct_answer: The correct option letter (A, B, C, or D)
- explanation: Why the answer is correct""",
            
            "true_false": """Each question must have:
- question: A statement to evaluate as true or false
- correct_answer: "true" or "false"
- explanation: Why the statement is true or false""",
            
            "short_answer": """Each question must have:
- question: The question text (answer should be 1-3 sentences)
- correct_answer: The expected answer
- explanation: Additional context or marking guidance""",
            
            "long_answer": """Each question must have:
- question: The question text (answer should be a paragraph or more)
- correct_answer: Key points that should be covered
- explanation: Marking rubric or guidance""",
            
            "numerical": """Each question must have:
- question: A mathematical/numerical problem
- correct_answer: The numerical answer with units if applicable
- explanation: Step-by-step solution""",
            
            "fill_blank": """Each question must have:
- question: A sentence with _____ for the blank
- correct_answer: The word/phrase that fills the blank
- explanation: Context for the answer""",
            
            "mixed": """Generate a mix of question types. For each question include a 'type' field indicating the question type.""",
        }
        
        prompt = f"""Generate {count} high-quality {q_type.upper()} questions about:

SUBJECT: {subject.get('name', 'Unknown')}
CHAPTER: {chapter.get('name', 'Unknown')}
TOPIC: {topic.get('name', 'Unknown')}

TOPIC DESCRIPTION:
{topic.get('description', 'No description available.')}

LEARNING OBJECTIVES:
{topic.get('learning_objectives', 'Not specified.')}

KEYWORDS: {topic.get('keywords', 'None')}

DIFFICULTY LEVEL: {difficulty.upper()}
{difficulty_desc.get(difficulty, '')}

QUESTION FORMAT:
{type_instructions.get(q_type, type_instructions['mcq'])}

REQUIREMENTS:
1. Questions must be directly related to the topic
2. Questions should test understanding, not just memorization (except for easy level)
3. Language should be clear and unambiguous
4. Options for MCQ should include plausible distractors
5. Explanations should be educational
6. Avoid repetitive or overly similar questions
7. Include a 'bloom_level' field for each question (remember, understand, apply, analyze, evaluate, create)
8. Include a 'difficulty' field for each question (easy, medium, hard)

Generate exactly {count} questions."""

        return prompt
    
    def _get_response_schema(self, question_type: str) -> dict:
        """Get expected JSON schema for AI response."""
        base_question = {
            "question": "string",
            "correct_answer": "string",
            "explanation": "string",
            "bloom_level": "remember|understand|apply|analyze|evaluate|create",
            "difficulty": "easy|medium|hard",
        }
        
        if question_type == "mcq":
            base_question["options"] = [
                {"label": "A", "text": "option text"},
            ]
        
        return {
            "questions": [base_question]
        }
    
    async def _create_questions(
        self,
        ai_response: dict,
        topic: SyllabusTopic,
        subject_id: UUID,
        teacher_id: UUID,
        difficulty: QuestionGenDifficulty,
        question_type: QuestionGenType,
    ) -> List[Question]:
        """Create Question records from AI response."""
        questions = []
        ai_questions = ai_response.get("questions", [])
        
        for i, q_data in enumerate(ai_questions):
            try:
                question = self._create_single_question(
                    q_data=q_data,
                    topic=topic,
                    subject_id=subject_id,
                    teacher_id=teacher_id,
                    default_difficulty=difficulty,
                    default_type=question_type,
                    order=i,
                )
                self.session.add(question)
                questions.append(question)
            except Exception as e:
                logger.warning(f"Failed to create question {i}: {e}")
                continue
        
        await self.session.flush()
        return questions
    
    def _create_single_question(
        self,
        q_data: dict,
        topic: SyllabusTopic,
        subject_id: UUID,
        teacher_id: UUID,
        default_difficulty: QuestionGenDifficulty,
        default_type: QuestionGenType,
        order: int,
    ) -> Question:
        """Create a single Question from AI data."""
        # Parse difficulty
        q_difficulty = q_data.get("difficulty", default_difficulty.value)
        try:
            difficulty_enum = DifficultyLevel(q_difficulty)
        except ValueError:
            difficulty_enum = DIFFICULTY_MAP.get(default_difficulty, DifficultyLevel.MEDIUM)
        
        # Parse question type
        q_type = q_data.get("type", default_type.value)
        try:
            q_type_lower = q_type.lower().replace(" ", "_")
            type_enum = QuestionType(q_type_lower)
        except ValueError:
            type_enum = QUESTION_TYPE_MAP.get(default_type, QuestionType.MCQ)
        
        # Parse bloom level
        bloom_str = q_data.get("bloom_level", "understand").lower()
        try:
            bloom_enum = BloomLevel(bloom_str)
        except ValueError:
            bloom_enum = BloomLevel.UNDERSTAND
        
        # Build options for MCQ
        options = None
        if type_enum == QuestionType.MCQ and "options" in q_data:
            raw_options = q_data["options"]
            if isinstance(raw_options, list):
                options = []
                for idx, opt in enumerate(raw_options):
                    if isinstance(opt, dict):
                        options.append({
                            "label": opt.get("label", chr(65 + idx)),
                            "text": opt.get("text", str(opt)),
                        })
                    else:
                        options.append({
                            "label": chr(65 + idx),
                            "text": str(opt),
                        })
        
        # Create question
        question = Question(
            tenant_id=self.tenant_id,
            subject_id=subject_id,
            topic_id=topic.id,
            created_by=teacher_id,
            question_type=type_enum,
            difficulty=difficulty_enum,
            bloom_level=bloom_enum,
            question_text=q_data.get("question", ""),
            options=options,
            correct_answer=q_data.get("correct_answer", ""),
            answer_explanation=q_data.get("explanation", ""),
            status=QuestionStatus.PENDING_REVIEW,  # AI questions need review
            marks=1.0,
            tags=["ai_generated", topic.name.lower()[:50] if topic.name else ""],
        )
        
        return question
    
    async def _increment_usage(self, count: int) -> None:
        """Increment AI usage counters."""
        await self.quota_manager.increment_usage("question_gen", 1)
        await self.quota_manager.increment_usage("ai_requests", 1)
    
    async def list_jobs(
        self,
        teacher_id: Optional[UUID] = None,
        status: Optional[AIJobStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[AIQuestionGenJob], int]:
        """List question generation jobs."""
        query = select(AIQuestionGenJob).where(
            AIQuestionGenJob.tenant_id == self.tenant_id,
            AIQuestionGenJob.deleted_at.is_(None),
        )
        
        if teacher_id:
            query = query.where(AIQuestionGenJob.requested_by == teacher_id)
        if status:
            query = query.where(AIQuestionGenJob.status == status)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Get paginated results
        query = query.order_by(AIQuestionGenJob.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.session.execute(query)
        jobs = list(result.scalars().all())
        
        return jobs, total
    
    async def get_job(self, job_id: UUID) -> Optional[AIQuestionGenJob]:
        """Get a specific job by ID."""
        query = select(AIQuestionGenJob).where(
            AIQuestionGenJob.id == job_id,
            AIQuestionGenJob.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_usage(self) -> dict:
        """Get AI usage statistics for question generation."""
        quota_status = await self.quota_manager.get_quota_status()
        
        return {
            "tier": quota_status["tier"],
            "question_gen": {
                "used": quota_status["usage"].get("question_gen", 0),
                "limit": quota_status["limits"].get("question_gen", 0),
                "remaining": quota_status["remaining"].get("question_gen", 0),
                "percent_used": quota_status["percent_used"].get("question_gen", 0),
            },
            "max_questions_per_gen": quota_status["limits"].get("max_questions_per_gen", 20),
        }
