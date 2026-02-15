"""
CUSTOS Student AI Trainer Schemas

Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ============================================
# Quiz Schemas
# ============================================

class QuizQuestionOption(BaseModel):
    """Quiz question option."""
    id: str
    text: str


class QuizQuestionBase(BaseModel):
    """Base quiz question schema."""
    question_text: str
    question_type: str  # mcq, true_false, short_answer, fill_blank
    marks: int = 1
    options: Optional[List[QuizQuestionOption]] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None
    bloom_level: Optional[str] = None


class QuizQuestionCreate(QuizQuestionBase):
    """Create quiz question."""
    correct_answer: Any  # Can be string, list, etc.
    topic_id: Optional[UUID] = None


class QuizQuestionResponse(QuizQuestionBase):
    """Quiz question response (without correct answer for students)."""
    id: UUID
    quiz_id: UUID
    order: int
    topic_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class QuizQuestionWithAnswer(QuizQuestionResponse):
    """Quiz question with correct answer (for teachers/grading)."""
    correct_answer: Any
    
    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str
    description: Optional[str] = None
    difficulty: str = "medium"
    time_limit_minutes: Optional[int] = None
    passing_percentage: float = 40.0


class GenerateQuizRequest(BaseModel):
    """Request to generate a quiz using AI."""
    syllabus_subject_id: UUID
    topic_ids: List[UUID]
    class_id: UUID
    section_id: Optional[UUID] = None
    
    # Quiz settings
    title: str
    difficulty: str = "medium"
    num_questions: int = Field(10, ge=1, le=50)
    question_types: List[str] = ["mcq", "true_false"]
    time_limit_minutes: Optional[int] = None
    
    # AI preferences
    focus_bloom_levels: Optional[List[str]] = None  # ["remember", "understand", "apply"]
    include_explanations: bool = True


class QuizCreate(QuizBase):
    """Create quiz manually."""
    syllabus_subject_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    questions: List[QuizQuestionCreate]


class QuizUpdate(BaseModel):
    """Update quiz."""
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_percentage: Optional[float] = None
    status: Optional[str] = None


class QuizResponse(QuizBase):
    """Quiz response."""
    id: UUID
    syllabus_subject_id: UUID
    topic_ids: Optional[List[UUID]] = None
    class_id: UUID
    section_id: Optional[UUID] = None
    total_questions: int
    total_marks: int
    status: str
    ai_generated: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizWithQuestions(QuizResponse):
    """Quiz with questions."""
    questions: List[QuizQuestionResponse]
    
    class Config:
        from_attributes = True


class GenerateQuizResponse(BaseModel):
    """Response from quiz generation."""
    quiz_id: UUID
    title: str
    total_questions: int
    total_marks: int
    difficulty: str
    ai_generated: bool


# ============================================
# Submission Schemas
# ============================================

class SubmitAnswerRequest(BaseModel):
    """Submit answer for a question."""
    question_id: UUID
    answer: Any  # Can be string, list, etc.


class StartQuizResponse(BaseModel):
    """Response when starting a quiz."""
    submission_id: UUID
    quiz_id: UUID
    started_at: datetime
    time_limit_minutes: Optional[int] = None


class SubmitQuizRequest(BaseModel):
    """Submit quiz answers."""
    answers: Dict[str, Any]  # {question_id: answer}


class QuestionResult(BaseModel):
    """Result for a single question."""
    question_id: UUID
    question_text: str
    student_answer: Any
    correct_answer: Any
    is_correct: bool
    marks_awarded: float
    max_marks: int
    explanation: Optional[str] = None


class QuizSubmissionResponse(BaseModel):
    """Quiz submission response."""
    id: UUID
    quiz_id: UUID
    student_id: UUID
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    score: Optional[float] = None
    max_score: Optional[int] = None
    percentage: Optional[float] = None
    passed: Optional[bool] = None
    
    class Config:
        from_attributes = True


class QuizResultResponse(QuizSubmissionResponse):
    """Detailed quiz result with question-wise breakdown."""
    quiz_title: str
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    question_results: List[QuestionResult]
    feedback: Optional[str] = None


# ============================================
# Task Schemas
# ============================================

class TaskProblem(BaseModel):
    """A problem in a task."""
    id: str
    problem_text: str
    hints: Optional[List[str]] = None
    difficulty: Optional[str] = None


class GenerateTaskRequest(BaseModel):
    """Request to generate practice tasks."""
    syllabus_subject_id: UUID
    topic_id: UUID
    class_id: UUID
    
    # Task settings
    title: str
    task_type: str = "practice"  # practice, assignment, project
    difficulty: str = "medium"
    num_problems: int = Field(5, ge=1, le=20)
    estimated_time_minutes: Optional[int] = None
    
    # AI preferences
    include_hints: bool = True
    include_solutions: bool = False


class TaskCreate(BaseModel):
    """Create task manually."""
    title: str
    description: Optional[str] = None
    task_type: str
    instructions: str
    problems: List[TaskProblem]
    syllabus_subject_id: UUID
    topic_id: UUID
    class_id: UUID
    difficulty: Optional[str] = None
    estimated_time_minutes: Optional[int] = None


class TaskResponse(BaseModel):
    """Task response."""
    id: UUID
    title: str
    description: Optional[str] = None
    task_type: str
    instructions: str
    problems: List[TaskProblem]
    difficulty: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    ai_generated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Analytics Schemas
# ============================================

class StudentQuizStats(BaseModel):
    """Student quiz statistics."""
    total_quizzes_taken: int
    total_quizzes_passed: int
    average_score: float
    average_percentage: float
    total_time_spent_minutes: int
    strongest_topics: List[Dict[str, Any]]
    weakest_topics: List[Dict[str, Any]]


class QuizAnalytics(BaseModel):
    """Quiz analytics for teachers."""
    quiz_id: UUID
    quiz_title: str
    total_attempts: int
    average_score: float
    average_percentage: float
    pass_rate: float
    question_difficulty_analysis: List[Dict[str, Any]]
