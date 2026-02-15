"""
CUSTOS Student AI Trainer Models

Database models for AI-generated quizzes and student tasks.
"""

from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class QuizDifficulty(str, Enum):
    """Quiz difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Question types."""
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"


class QuizStatus(str, Enum):
    """Quiz status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatus(str, Enum):
    """Submission status."""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"


class StudentQuiz(Base):
    """AI-generated quiz for students."""
    __tablename__ = "student_quizzes"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Quiz metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)
    syllabus_subject_id = Column(PGUUID(as_uuid=True), ForeignKey("syllabus_subjects.id"))
    topic_ids = Column(JSON)  # List of topic IDs covered
    
    # Target audience
    class_id = Column(PGUUID(as_uuid=True), ForeignKey("classes.id"))
    section_id = Column(PGUUID(as_uuid=True), ForeignKey("sections.id"), nullable=True)
    
    # Quiz settings
    difficulty = Column(String(20), default=QuizDifficulty.MEDIUM)
    total_questions = Column(Integer, nullable=False)
    total_marks = Column(Integer, nullable=False)
    time_limit_minutes = Column(Integer, nullable=True)  # NULL = no time limit
    passing_percentage = Column(Float, default=40.0)
    
    # AI generation metadata
    ai_generated = Column(Boolean, default=True)
    ai_provider = Column(String(50))
    generation_prompt = Column(Text)
    
    # Status
    status = Column(String(20), default=QuizStatus.DRAFT)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("QuizSubmission", back_populates="quiz")
    
    # Audit
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


class QuizQuestion(Base):
    """Individual question in a quiz."""
    __tablename__ = "quiz_questions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    quiz_id = Column(PGUUID(as_uuid=True), ForeignKey("student_quizzes.id"), nullable=False)
    
    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    marks = Column(Integer, default=1)
    order = Column(Integer, nullable=False)
    
    # Options (for MCQ, True/False)
    options = Column(JSON)  # [{"id": "A", "text": "Option A"}, ...]
    correct_answer = Column(JSON)  # Can be single value or array for multiple correct
    
    # Explanation
    explanation = Column(Text)
    
    # Metadata
    topic_id = Column(PGUUID(as_uuid=True), ForeignKey("syllabus_topics.id"), nullable=True)
    difficulty = Column(String(20))
    bloom_level = Column(String(50))  # Remember, Understand, Apply, Analyze, Evaluate, Create
    
    # Relationships
    quiz = relationship("StudentQuiz", back_populates="questions")
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuizSubmission(Base):
    """Student's quiz submission."""
    __tablename__ = "quiz_submissions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    quiz_id = Column(PGUUID(as_uuid=True), ForeignKey("student_quizzes.id"), nullable=False)
    student_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Submission data
    answers = Column(JSON)  # {"question_id": "answer", ...}
    status = Column(String(20), default=SubmissionStatus.IN_PROGRESS)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    
    # Grading
    score = Column(Float, nullable=True)
    max_score = Column(Integer, nullable=True)
    percentage = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    
    # Auto-grading results
    correct_answers = Column(Integer, default=0)
    incorrect_answers = Column(Integer, default=0)
    unanswered = Column(Integer, default=0)
    
    # Feedback
    feedback = Column(Text)
    graded_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    graded_at = Column(DateTime, nullable=True)
    
    # Relationships
    quiz = relationship("StudentQuiz", back_populates="submissions")
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentTask(Base):
    """AI-generated practice task for students."""
    __tablename__ = "student_tasks"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Task metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(50))  # practice, assignment, project, etc.
    
    # Content
    instructions = Column(Text)
    problems = Column(JSON)  # List of problems/exercises
    resources = Column(JSON)  # Reference materials
    
    # Target
    syllabus_subject_id = Column(PGUUID(as_uuid=True), ForeignKey("syllabus_subjects.id"))
    topic_id = Column(PGUUID(as_uuid=True), ForeignKey("syllabus_topics.id"))
    class_id = Column(PGUUID(as_uuid=True), ForeignKey("classes.id"))
    
    # Settings
    difficulty = Column(String(20))
    estimated_time_minutes = Column(Integer)
    
    # AI metadata
    ai_generated = Column(Boolean, default=True)
    ai_provider = Column(String(50))
    
    # Audit
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
