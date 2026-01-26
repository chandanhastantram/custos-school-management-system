"""
CUSTOS AI Package
"""

from app.ai.base import AIProvider, AIResponse, AIPromptBuilder
from app.ai.openai_provider import OpenAIProvider, get_ai_provider
from app.ai.lesson_generator import LessonGenerator
from app.ai.question_generator import QuestionGenerator
from app.ai.doubt_solver import DoubtSolver

__all__ = [
    "AIProvider",
    "AIResponse",
    "AIPromptBuilder",
    "OpenAIProvider",
    "get_ai_provider",
    "LessonGenerator",
    "QuestionGenerator",
    "DoubtSolver",
]
