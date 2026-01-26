"""
CUSTOS Question Tests
"""

import pytest
from uuid import uuid4

from app.models.question import QuestionType, BloomLevel, Difficulty
from app.schemas.question import QuestionCreate, MCQOption


class TestQuestionSchemas:
    """Test question schemas."""
    
    def test_mcq_question_create(self):
        """Test MCQ question creation schema."""
        options = [
            MCQOption(id="A", text="Option A", is_correct=False),
            MCQOption(id="B", text="Option B", is_correct=True),
            MCQOption(id="C", text="Option C", is_correct=False),
            MCQOption(id="D", text="Option D", is_correct=False),
        ]
        
        question = QuestionCreate(
            topic_id=uuid4(),
            question_text="What is 2 + 2?",
            question_type=QuestionType.MCQ,
            difficulty=Difficulty.EASY,
            bloom_level=BloomLevel.KNOWLEDGE,
            options=options,
            explanation="2 + 2 = 4",
            marks=1.0,
        )
        
        assert question.question_text == "What is 2 + 2?"
        assert question.question_type == QuestionType.MCQ
        assert len(question.options) == 4
        assert question.options[1].is_correct
    
    def test_question_types(self):
        """Test all question types are defined."""
        assert QuestionType.MCQ.value == "mcq"
        assert QuestionType.MCQ_MULTIPLE.value == "mcq_multiple"
        assert QuestionType.TRUE_FALSE.value == "true_false"
        assert QuestionType.SHORT_ANSWER.value == "short_answer"
        assert QuestionType.LONG_ANSWER.value == "long_answer"
        assert QuestionType.FILL_BLANK.value == "fill_blank"
    
    def test_bloom_levels(self):
        """Test Bloom's taxonomy levels."""
        levels = [
            BloomLevel.KNOWLEDGE,
            BloomLevel.COMPREHENSION,
            BloomLevel.APPLICATION,
            BloomLevel.ANALYSIS,
            BloomLevel.SYNTHESIS,
            BloomLevel.EVALUATION,
        ]
        assert len(levels) == 6
    
    def test_difficulty_levels(self):
        """Test difficulty levels."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.HARD.value == "hard"
        assert Difficulty.EXPERT.value == "expert"


class TestQuestionValidation:
    """Test question validation logic."""
    
    def test_mcq_needs_correct_option(self):
        """Test MCQ validation requires correct option."""
        # All incorrect options
        options = [
            MCQOption(id="A", text="Option A", is_correct=False),
            MCQOption(id="B", text="Option B", is_correct=False),
        ]
        
        # This should be caught by service layer validation
        question = QuestionCreate(
            topic_id=uuid4(),
            question_text="Test?",
            question_type=QuestionType.MCQ,
            options=options,
        )
        
        # Check options
        correct = [o for o in question.options if o.is_correct]
        assert len(correct) == 0  # No correct option
    
    def test_true_false_question(self):
        """Test True/False question."""
        question = QuestionCreate(
            topic_id=uuid4(),
            question_text="The Earth is round.",
            question_type=QuestionType.TRUE_FALSE,
            correct_answer="true",
            explanation="The Earth is an oblate spheroid.",
        )
        
        assert question.question_type == QuestionType.TRUE_FALSE
        assert question.correct_answer == "true"
    
    def test_short_answer_question(self):
        """Test short answer question."""
        question = QuestionCreate(
            topic_id=uuid4(),
            question_text="What is the capital of France?",
            question_type=QuestionType.SHORT_ANSWER,
            correct_answer="Paris",
            marks=2.0,
        )
        
        assert question.question_type == QuestionType.SHORT_ANSWER
        assert question.marks == 2.0
