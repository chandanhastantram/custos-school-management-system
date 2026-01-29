"""
CUSTOS OpenAI Provider
"""

import json
from typing import Optional

import openai

from app.core.config import settings
from app.ai.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using OpenAI."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    
    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
    ) -> dict:
        """Generate structured JSON output."""
        system_prompt = f"""You are a helpful assistant that responds only in valid JSON.
Your response must match this schema: {json.dumps(schema)}
Respond with ONLY valid JSON, no other text."""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=0.5,
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
    
    async def generate_lesson_plan(
        self,
        subject: str,
        topic: str,
        grade_level: int,
        duration_minutes: int = 45,
    ) -> dict:
        """Generate lesson plan."""
        prompt = f"""Create a detailed lesson plan for:
Subject: {subject}
Topic: {topic}
Grade Level: {grade_level}
Duration: {duration_minutes} minutes

Include:
1. Learning objectives (3-5)
2. Introduction/Hook (5 min)
3. Main content with activities
4. Assessment questions
5. Homework assignment
6. Resources needed"""

        schema = {
            "objectives": ["list of objectives"],
            "introduction": "string",
            "content": ["list of content sections"],
            "activities": ["list of activities"],
            "assessment": ["list of questions"],
            "homework": "string",
            "resources": ["list of resources"]
        }
        
        return await self.generate_structured(prompt, schema)
    
    async def generate_questions(
        self,
        subject: str,
        topic: str,
        question_type: str,
        count: int,
        difficulty: str = "medium",
    ) -> list:
        """Generate questions."""
        prompt = f"""Generate {count} {question_type} questions about:
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

For MCQ, include 4 options with correct answer marked.
For short answer, include expected answer.
Include explanation for each answer."""

        schema = {
            "questions": [
                {
                    "question": "string",
                    "type": question_type,
                    "options": ["for MCQ only"],
                    "correct_answer": "string",
                    "explanation": "string"
                }
            ]
        }
        
        result = await self.generate_structured(prompt, schema)
        return result.get("questions", [])
    
    async def solve_doubt(
        self,
        question: str,
        subject: str,
        context: Optional[str] = None,
    ) -> dict:
        """Answer student doubt."""
        context_text = f"\nContext: {context}" if context else ""
        
        prompt = f"""A student has a doubt about {subject}:{context_text}

Question: {question}

Provide:
1. A clear, step-by-step explanation
2. Examples if helpful
3. Related concepts to review
4. Practice problems"""

        schema = {
            "answer": "string",
            "steps": ["step by step explanation"],
            "examples": ["optional examples"],
            "related_concepts": ["concepts to review"],
            "practice_problems": ["practice questions"]
        }
        
        return await self.generate_structured(prompt, schema)
    
    async def process_exam_ocr(
        self,
        image_base64: str,
        image_type: str = "image/jpeg",
        exam_context: Optional[str] = None,
    ) -> dict:
        """
        Process exam answer sheet using GPT-4 Vision.
        
        Extracts:
        - Student identifiers (name/roll number)
        - Total marks
        - Marks obtained
        - Wrong question numbers
        """
        context_text = f"\n{exam_context}" if exam_context else ""
        
        prompt = f"""Analyze this exam answer sheet or marks register image.{context_text}

Extract the following information for each student visible:
1. Student identifier (name or roll number)
2. Total marks possible
3. Marks obtained
4. List of attempted question numbers (if visible)
5. List of wrong question numbers (questions marked wrong or with deductions)

Be precise with numbers. If you cannot read something clearly, indicate low confidence."""

        schema = {
            "success": "boolean",
            "exam_title": "title if visible, else null",
            "total_students": "number of students extracted",
            "students": [
                {
                    "student_identifier": "name or roll number",
                    "total_marks": "number",
                    "marks_obtained": "number",
                    "attempted_questions": ["list of integers"],
                    "wrong_questions": ["list of integers"],
                    "confidence": "0.0 to 1.0"
                }
            ],
            "errors": ["any issues encountered"]
        }
        
        system_prompt = f"""You are an expert OCR system specialized in reading exam answer sheets and mark registers.
You must extract student results accurately.
Your response must match this schema: {json.dumps(schema)}
Respond with ONLY valid JSON, no other text."""

        # Use vision model
        vision_model = getattr(settings, 'openai_vision_model', 'gpt-4o')
        
        response = await self.client.chat.completions.create(
            model=vision_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=0.2,  # Low temperature for accuracy
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {
                "success": False,
                "exam_title": None,
                "total_students": 0,
                "students": [],
                "errors": ["Failed to parse OCR response as JSON"]
            }

