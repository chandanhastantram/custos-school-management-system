"""
CUSTOS Student AI Trainer Service

AI-powered service for generating quizzes and practice tasks from syllabus.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.ai.providers.openai import OpenAIProvider
from app.ai.student_trainer_models import (
    StudentQuiz, QuizQuestion, QuizSubmission, StudentTask,
    QuizDifficulty, QuestionType, QuizStatus, SubmissionStatus
)
from app.ai.student_trainer_schemas import (
    GenerateQuizRequest, GenerateQuizResponse, QuizCreate,
    QuizWithQuestions, QuizQuestionCreate, QuizQuestionWithAnswer,
    StartQuizResponse, SubmitQuizRequest, QuizResultResponse,
    QuestionResult, GenerateTaskRequest, TaskResponse,
    StudentQuizStats, QuizAnalytics
)
from app.academics.models.syllabus import SyllabusSubject, SyllabusTopic


class StudentAITrainerService:
    """
    AI Trainer Service for Students.
    
    Features:
    - Analyze syllabus topics
    - Generate quizzes with various question types
    - Auto-grade submissions
    - Generate practice tasks
    - Track student progress
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.ai_provider = OpenAIProvider()
    
    # ============================================
    # Syllabus Analysis
    # ============================================
    
    async def analyze_syllabus(self, syllabus_subject_id: UUID) -> Dict[str, Any]:
        """
        Analyze syllabus and extract topics for quiz generation.
        
        Returns structured data about topics, learning objectives, and difficulty.
        """
        # Get syllabus topics
        query = select(SyllabusTopic).where(
            SyllabusTopic.syllabus_subject_id == syllabus_subject_id,
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.is_deleted == False
        ).order_by(SyllabusTopic.order)
        
        result = await self.session.execute(query)
        topics = result.scalars().all()
        
        if not topics:
            raise ResourceNotFoundError("Syllabus topics", syllabus_subject_id)
        
        # Structure topics for AI analysis
        topics_data = [
            {
                "id": str(topic.id),
                "name": topic.name,
                "description": topic.description,
                "order": topic.order
            }
            for topic in topics
        ]
        
        # Use AI to analyze and categorize
        prompt = f"""Analyze these syllabus topics and provide:
1. Difficulty level for each topic (easy/medium/hard)
2. Key learning objectives
3. Suggested question types for assessment

Topics:
{json.dumps(topics_data, indent=2)}

Return a JSON object with analysis for each topic."""
        
        schema = {
            "topics": [
                {
                    "topic_id": "UUID",
                    "difficulty": "easy|medium|hard",
                    "learning_objectives": ["objective1", "objective2"],
                    "suggested_question_types": ["mcq", "true_false", "short_answer"],
                    "bloom_levels": ["remember", "understand", "apply"]
                }
            ]
        }
        
        analysis = await self.ai_provider.generate_structured(prompt, schema)
        
        return {
            "syllabus_subject_id": str(syllabus_subject_id),
            "total_topics": len(topics),
            "topics": topics_data,
            "ai_analysis": analysis
        }
    
    # ============================================
    # Quiz Generation
    # ============================================
    
    async def generate_quiz(
        self,
        teacher_id: UUID,
        request: GenerateQuizRequest
    ) -> GenerateQuizResponse:
        """
        Generate a quiz using AI based on syllabus topics.
        """
        # Get topic information
        topics = await self._get_topics(request.topic_ids)
        
        if not topics:
            raise ValidationError("No valid topics found")
        
        # Build AI prompt
        topics_text = "\n".join([
            f"- {t['name']}: {t.get('description', 'No description')}"
            for t in topics
        ])
        
        question_types_text = ", ".join(request.question_types)
        bloom_levels_text = ", ".join(request.focus_bloom_levels) if request.focus_bloom_levels else "all levels"
        
        prompt = f"""Generate {request.num_questions} quiz questions for students.

Topics to cover:
{topics_text}

Requirements:
- Difficulty: {request.difficulty}
- Question types: {question_types_text}
- Bloom's taxonomy levels: {bloom_levels_text}
- Include explanations: {request.include_explanations}

Create diverse, educational questions that test understanding."""
        
        # Define schema for AI response
        schema = {
            "questions": [
                {
                    "question_text": "string",
                    "question_type": "mcq|true_false|short_answer|fill_blank",
                    "options": [{"id": "A", "text": "option text"}],  # For MCQ
                    "correct_answer": "string or array",
                    "explanation": "string",
                    "marks": "integer",
                    "difficulty": "easy|medium|hard",
                    "bloom_level": "remember|understand|apply|analyze|evaluate|create",
                    "topic_index": "integer (0-based)"
                }
            ]
        }
        
        # Generate questions using AI
        ai_response = await self.ai_provider.generate_structured(prompt, schema)
        
        # Create quiz in database
        total_marks = sum(q.get("marks", 1) for q in ai_response.get("questions", []))
        
        quiz = StudentQuiz(
            tenant_id=self.tenant_id,
            title=request.title,
            description=f"AI-generated quiz covering {len(topics)} topics",
            syllabus_subject_id=request.syllabus_subject_id,
            topic_ids=[str(tid) for tid in request.topic_ids],
            class_id=request.class_id,
            section_id=request.section_id,
            difficulty=request.difficulty,
            total_questions=len(ai_response.get("questions", [])),
            total_marks=total_marks,
            time_limit_minutes=request.time_limit_minutes,
            ai_generated=True,
            ai_provider="openai",
            generation_prompt=prompt[:1000],  # Store truncated prompt
            status=QuizStatus.DRAFT,
            created_by=teacher_id
        )
        
        self.session.add(quiz)
        await self.session.flush()
        
        # Create questions
        for idx, q_data in enumerate(ai_response.get("questions", [])):
            topic_idx = q_data.get("topic_index", 0)
            topic_id = topics[topic_idx]["id"] if topic_idx < len(topics) else None
            
            question = QuizQuestion(
                tenant_id=self.tenant_id,
                quiz_id=quiz.id,
                question_text=q_data["question_text"],
                question_type=q_data["question_type"],
                marks=q_data.get("marks", 1),
                order=idx + 1,
                options=q_data.get("options"),
                correct_answer=q_data["correct_answer"],
                explanation=q_data.get("explanation"),
                topic_id=UUID(topic_id) if topic_id else None,
                difficulty=q_data.get("difficulty", request.difficulty),
                bloom_level=q_data.get("bloom_level")
            )
            self.session.add(question)
        
        await self.session.commit()
        
        return GenerateQuizResponse(
            quiz_id=quiz.id,
            title=quiz.title,
            total_questions=quiz.total_questions,
            total_marks=quiz.total_marks,
            difficulty=quiz.difficulty,
            ai_generated=True
        )
    
    async def create_quiz_manual(
        self,
        teacher_id: UUID,
        data: QuizCreate
    ) -> QuizWithQuestions:
        """Create a quiz manually (without AI)."""
        total_marks = sum(q.marks for q in data.questions)
        
        quiz = StudentQuiz(
            tenant_id=self.tenant_id,
            title=data.title,
            description=data.description,
            syllabus_subject_id=data.syllabus_subject_id,
            class_id=data.class_id,
            section_id=data.section_id,
            difficulty=data.difficulty,
            total_questions=len(data.questions),
            total_marks=total_marks,
            time_limit_minutes=data.time_limit_minutes,
            passing_percentage=data.passing_percentage,
            ai_generated=False,
            status=QuizStatus.DRAFT,
            created_by=teacher_id
        )
        
        self.session.add(quiz)
        await self.session.flush()
        
        # Create questions
        for idx, q_data in enumerate(data.questions):
            question = QuizQuestion(
                tenant_id=self.tenant_id,
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                question_type=q_data.question_type,
                marks=q_data.marks,
                order=idx + 1,
                options=q_data.options,
                correct_answer=q_data.correct_answer,
                explanation=q_data.explanation,
                topic_id=q_data.topic_id,
                difficulty=q_data.difficulty,
                bloom_level=q_data.bloom_level
            )
            self.session.add(question)
        
        await self.session.commit()
        await self.session.refresh(quiz)
        
        return QuizWithQuestions.model_validate(quiz)
    
    async def publish_quiz(self, quiz_id: UUID) -> None:
        """Publish a quiz to make it available to students."""
        quiz = await self._get_quiz(quiz_id)
        quiz.status = QuizStatus.PUBLISHED
        quiz.published_at = datetime.utcnow()
        await self.session.commit()
    
    # ============================================
    # Quiz Taking & Submission
    # ============================================
    
    async def start_quiz(
        self,
        student_id: UUID,
        quiz_id: UUID
    ) -> StartQuizResponse:
        """Start a quiz attempt for a student."""
        quiz = await self._get_quiz(quiz_id)
        
        if quiz.status != QuizStatus.PUBLISHED:
            raise ValidationError("Quiz is not published")
        
        # Create submission
        submission = QuizSubmission(
            tenant_id=self.tenant_id,
            quiz_id=quiz_id,
            student_id=student_id,
            status=SubmissionStatus.IN_PROGRESS,
            max_score=quiz.total_marks,
            answers={}
        )
        
        self.session.add(submission)
        await self.session.commit()
        
        return StartQuizResponse(
            submission_id=submission.id,
            quiz_id=quiz_id,
            started_at=submission.started_at,
            time_limit_minutes=quiz.time_limit_minutes
        )
    
    async def submit_quiz(
        self,
        submission_id: UUID,
        student_id: UUID,
        request: SubmitQuizRequest
    ) -> QuizResultResponse:
        """Submit quiz answers and auto-grade."""
        submission = await self._get_submission(submission_id)
        
        if submission.student_id != student_id:
            raise ValidationError("Not authorized")
        
        if submission.status != SubmissionStatus.IN_PROGRESS:
            raise ValidationError("Quiz already submitted")
        
        # Get quiz and questions
        quiz = await self._get_quiz(submission.quiz_id)
        questions = await self._get_quiz_questions(quiz.id)
        
        # Auto-grade
        results = []
        total_score = 0
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0
        
        for question in questions:
            q_id = str(question.id)
            student_answer = request.answers.get(q_id)
            
            if student_answer is None:
                unanswered_count += 1
                is_correct = False
                marks_awarded = 0
            else:
                is_correct = self._check_answer(
                    student_answer,
                    question.correct_answer,
                    question.question_type
                )
                marks_awarded = question.marks if is_correct else 0
                
                if is_correct:
                    correct_count += 1
                else:
                    incorrect_count += 1
            
            total_score += marks_awarded
            
            results.append(QuestionResult(
                question_id=question.id,
                question_text=question.question_text,
                student_answer=student_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
                max_marks=question.marks,
                explanation=question.explanation
            ))
        
        # Calculate percentage and pass/fail
        percentage = (total_score / quiz.total_marks * 100) if quiz.total_marks > 0 else 0
        passed = percentage >= quiz.passing_percentage
        
        # Update submission
        submission.answers = request.answers
        submission.status = SubmissionStatus.GRADED
        submission.submitted_at = datetime.utcnow()
        submission.time_taken_seconds = int((datetime.utcnow() - submission.started_at).total_seconds())
        submission.score = total_score
        submission.percentage = percentage
        submission.passed = passed
        submission.correct_answers = correct_count
        submission.incorrect_answers = incorrect_count
        submission.unanswered = unanswered_count
        
        await self.session.commit()
        
        return QuizResultResponse(
            id=submission.id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            student_id=student_id,
            status=submission.status,
            started_at=submission.started_at,
            submitted_at=submission.submitted_at,
            time_taken_seconds=submission.time_taken_seconds,
            score=total_score,
            max_score=quiz.total_marks,
            percentage=percentage,
            passed=passed,
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            unanswered=unanswered_count,
            question_results=results
        )
    
    # ============================================
    # Practice Tasks Generation
    # ============================================
    
    async def generate_task(
        self,
        teacher_id: UUID,
        request: GenerateTaskRequest
    ) -> TaskResponse:
        """Generate practice tasks using AI."""
        # Get topic info
        topic = await self._get_topic(request.topic_id)
        
        prompt = f"""Generate {request.num_problems} practice problems for students.

Topic: {topic['name']}
Description: {topic.get('description', 'N/A')}
Difficulty: {request.difficulty}
Task Type: {request.task_type}

Create diverse problems that help students practice and understand the topic.
{"Include hints for each problem." if request.include_hints else ""}
{"Include solutions." if request.include_solutions else ""}"""
        
        schema = {
            "instructions": "string",
            "problems": [
                {
                    "id": "string",
                    "problem_text": "string",
                    "hints": ["hint1", "hint2"],
                    "solution": "string (if requested)",
                    "difficulty": "easy|medium|hard"
                }
            ]
        }
        
        ai_response = await self.ai_provider.generate_structured(prompt, schema)
        
        # Create task
        task = StudentTask(
            tenant_id=self.tenant_id,
            title=request.title,
            description=f"AI-generated {request.task_type} for {topic['name']}",
            task_type=request.task_type,
            instructions=ai_response.get("instructions", ""),
            problems=ai_response.get("problems", []),
            syllabus_subject_id=request.syllabus_subject_id,
            topic_id=request.topic_id,
            class_id=request.class_id,
            difficulty=request.difficulty,
            estimated_time_minutes=request.estimated_time_minutes,
            ai_generated=True,
            ai_provider="openai",
            created_by=teacher_id
        )
        
        self.session.add(task)
        await self.session.commit()
        
        return TaskResponse.model_validate(task)
    
    # ============================================
    # Helper Methods
    # ============================================
    
    async def _get_topics(self, topic_ids: List[UUID]) -> List[Dict]:
        """Get topic information."""
        query = select(SyllabusTopic).where(
            SyllabusTopic.id.in_(topic_ids),
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.is_deleted == False
        )
        result = await self.session.execute(query)
        topics = result.scalars().all()
        
        return [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description
            }
            for t in topics
        ]
    
    async def _get_topic(self, topic_id: UUID) -> Dict:
        """Get single topic."""
        query = select(SyllabusTopic).where(
            SyllabusTopic.id == topic_id,
            SyllabusTopic.tenant_id == self.tenant_id,
            SyllabusTopic.is_deleted == False
        )
        result = await self.session.execute(query)
        topic = result.scalar_one_or_none()
        
        if not topic:
            raise ResourceNotFoundError("Topic", topic_id)
        
        return {
            "id": str(topic.id),
            "name": topic.name,
            "description": topic.description
        }
    
    async def _get_quiz(self, quiz_id: UUID) -> StudentQuiz:
        """Get quiz by ID."""
        query = select(StudentQuiz).where(
            StudentQuiz.id == quiz_id,
            StudentQuiz.tenant_id == self.tenant_id,
            StudentQuiz.deleted_at.is_(None)
        )
        result = await self.session.execute(query)
        quiz = result.scalar_one_or_none()
        
        if not quiz:
            raise ResourceNotFoundError("Quiz", quiz_id)
        
        return quiz
    
    async def _get_quiz_questions(self, quiz_id: UUID) -> List[QuizQuestion]:
        """Get all questions for a quiz."""
        query = select(QuizQuestion).where(
            QuizQuestion.quiz_id == quiz_id,
            QuizQuestion.tenant_id == self.tenant_id
        ).order_by(QuizQuestion.order)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def _get_submission(self, submission_id: UUID) -> QuizSubmission:
        """Get submission by ID."""
        query = select(QuizSubmission).where(
            QuizSubmission.id == submission_id,
            QuizSubmission.tenant_id == self.tenant_id
        )
        result = await self.session.execute(query)
        submission = result.scalar_one_or_none()
        
        if not submission:
            raise ResourceNotFoundError("Submission", submission_id)
        
        return submission
    
    def _check_answer(
        self,
        student_answer: Any,
        correct_answer: Any,
        question_type: str
    ) -> bool:
        """Check if student answer is correct."""
        if question_type == QuestionType.MCQ:
            return str(student_answer).strip().upper() == str(correct_answer).strip().upper()
        
        elif question_type == QuestionType.TRUE_FALSE:
            return str(student_answer).lower() == str(correct_answer).lower()
        
        elif question_type == QuestionType.SHORT_ANSWER:
            # Case-insensitive comparison, strip whitespace
            return str(student_answer).strip().lower() == str(correct_answer).strip().lower()
        
        elif question_type == QuestionType.FILL_BLANK:
            # Similar to short answer
            return str(student_answer).strip().lower() == str(correct_answer).strip().lower()
        
        return False
