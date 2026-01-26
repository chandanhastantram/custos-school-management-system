"""
CUSTOS AI Base Module

Base classes for AI providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any
from dataclasses import dataclass


@dataclass
class AIResponse:
    """Standard AI response."""
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    raw_response: Optional[Any] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AIResponse:
        """Generate text response."""
        pass
    
    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> tuple[dict, int]:
        """Generate structured JSON response."""
        pass


class AIPromptBuilder:
    """Helper for building prompts."""
    
    @staticmethod
    def lesson_plan_prompt(
        subject: str,
        topic: str,
        grade: str,
        duration: int,
        objectives: Optional[List[str]] = None,
    ) -> str:
        """Build lesson plan generation prompt."""
        objectives_str = "\n".join(f"- {obj}" for obj in objectives) if objectives else "Based on the topic"
        
        return f"""Generate a detailed lesson plan for the following:

Subject: {subject}
Topic: {topic}
Grade/Class: {grade}
Duration: {duration} minutes

Learning Objectives:
{objectives_str}

Please provide a comprehensive lesson plan in JSON format with the following structure:
{{
    "title": "Lesson title",
    "objectives": ["objective 1", "objective 2"],
    "materials": ["material 1", "material 2"],
    "introduction": {{
        "duration_minutes": 5,
        "activity": "Description of introduction activity",
        "teacher_actions": ["action 1"],
        "student_actions": ["action 1"]
    }},
    "main_content": [
        {{
            "topic": "Subtopic name",
            "duration_minutes": 15,
            "explanation": "Detailed explanation",
            "examples": ["example 1"],
            "activities": ["activity 1"]
        }}
    ],
    "assessment": {{
        "type": "formative/summative",
        "questions": ["question 1"],
        "criteria": ["criteria 1"]
    }},
    "conclusion": {{
        "duration_minutes": 5,
        "summary": "Key takeaways",
        "homework": "Optional homework"
    }},
    "resources": ["resource 1"]
}}"""
    
    @staticmethod
    def question_generation_prompt(
        subject: str,
        topic: str,
        grade: str,
        count: int,
        question_type: str,
        difficulty: str,
        bloom_level: Optional[str] = None,
    ) -> str:
        """Build question generation prompt."""
        bloom_instruction = f"\nBloom's Level: {bloom_level}" if bloom_level else ""
        
        type_instructions = {
            "mcq": "Multiple Choice Questions with 4 options (A, B, C, D), one correct answer",
            "mcq_multiple": "Multiple Choice Questions with 4 options, multiple correct answers possible",
            "true_false": "True/False questions",
            "short_answer": "Short answer questions (1-2 sentences)",
            "long_answer": "Long answer/essay questions",
            "fill_blank": "Fill in the blank questions",
        }
        
        return f"""Generate {count} {type_instructions.get(question_type, question_type)} questions for:

Subject: {subject}
Topic: {topic}
Grade/Class: {grade}
Difficulty: {difficulty}{bloom_instruction}

Return JSON array with this structure:
[
    {{
        "question_text": "The question text",
        "question_type": "{question_type}",
        "difficulty": "{difficulty}",
        "options": [  // For MCQ only
            {{"id": "A", "text": "Option A", "is_correct": false}},
            {{"id": "B", "text": "Option B", "is_correct": true}},
            {{"id": "C", "text": "Option C", "is_correct": false}},
            {{"id": "D", "text": "Option D", "is_correct": false}}
        ],
        "correct_answer": "The correct answer",  // For non-MCQ
        "explanation": "Detailed explanation of the answer",
        "marks": 1,
        "bloom_level": "knowledge/comprehension/application/analysis/synthesis/evaluation"
    }}
]"""
    
    @staticmethod
    def doubt_solver_prompt(
        question: str,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """Build doubt solving prompt."""
        context_parts = []
        if subject:
            context_parts.append(f"Subject: {subject}")
        if topic:
            context_parts.append(f"Topic: {topic}")
        if context:
            context_parts.append(f"Context: {context}")
        
        context_str = "\n".join(context_parts) if context_parts else ""
        
        return f"""You are a helpful teacher assistant. A student has asked the following question:

{context_str}

Student's Question: {question}

Please provide:
1. A clear, age-appropriate answer
2. Step-by-step explanation if applicable
3. Related concepts they should know
4. 2-3 follow-up questions to deepen understanding

Format your response as JSON:
{{
    "answer": "Direct answer to the question",
    "explanation": "Detailed step-by-step explanation",
    "key_concepts": ["concept 1", "concept 2"],
    "related_topics": ["topic 1", "topic 2"],
    "follow_up_questions": ["question 1", "question 2"]
}}"""
