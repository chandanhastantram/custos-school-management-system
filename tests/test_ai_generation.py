"""
Tests for AI-powered features including lesson plan generation and student trainer.
"""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta


@pytest.mark.asyncio
class TestAILessonPlanGeneration:
    """Test AI lesson plan generation endpoints."""
    
    async def test_generate_lesson_plan_simple(self, client: AsyncClient, teacher_token: str):
        """Test simple AI lesson plan generation (legacy endpoint)."""
        payload = {
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "grade_level": 10,
            "duration_minutes": 45
        }
        
        response = await client.post(
            "/api/v1/ai/lesson-plan",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # May return 200 or 402 if quota exceeded
        assert response.status_code in [200, 402]
        
        if response.status_code == 200:
            data = response.json()
            assert "objectives" in data or "content" in data
    
    async def test_generate_lesson_plan_advanced(
        self, 
        client: AsyncClient, 
        teacher_token: str,
        test_data: dict
    ):
        """Test advanced AI lesson plan generation with syllabus."""
        payload = {
            "class_id": str(test_data["class_id"]),
            "section_id": str(test_data.get("section_id")),
            "subject_id": str(test_data["subject_id"]),
            "syllabus_subject_id": str(test_data["syllabus_subject_id"]),
            "title": "Mathematics Annual Plan 2024",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=180)),
            "preferences": {
                "pace": "normal",
                "focus": "balanced",
                "include_revision_periods": True,
                "revision_percent": 15,
                "periods_per_week": 5
            }
        }
        
        response = await client.post(
            "/api/v1/ai/lesson-plan/generate",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # May return 201 or 402 if quota exceeded
        assert response.status_code in [201, 402]
        
        if response.status_code == 201:
            data = response.json()
            assert "job_id" in data
            assert "lesson_plan_id" in data
            assert "total_units" in data
            assert data["total_periods"] > 0
    
    async def test_list_lesson_plan_jobs(self, client: AsyncClient, teacher_token: str):
        """Test listing AI lesson plan generation jobs."""
        response = await client.get(
            "/api/v1/ai/lesson-plan/jobs",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    async def test_get_lesson_plan_job(
        self, 
        client: AsyncClient, 
        teacher_token: str,
        job_id: str
    ):
        """Test getting details of a lesson plan generation job."""
        response = await client.get(
            f"/api/v1/ai/lesson-plan/jobs/{job_id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert data["status"] in ["pending", "running", "completed", "failed"]
    
    async def test_ai_usage_tracking(self, client: AsyncClient, teacher_token: str):
        """Test AI usage statistics endpoint."""
        response = await client.get(
            "/api/v1/ai/usage",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ai_requests_used" in data
        assert "ai_requests_limit" in data
        assert "remaining" in data
        assert "percent_used" in data


@pytest.mark.asyncio
class TestAIQuestionGeneration:
    """Test AI question generation endpoints."""
    
    async def test_generate_questions(self, client: AsyncClient, teacher_token: str):
        """Test AI question generation."""
        payload = {
            "subject": "Physics",
            "topic": "Newton's Laws of Motion",
            "question_type": "mcq",
            "count": 5,
            "difficulty": "medium"
        }
        
        response = await client.post(
            "/api/v1/ai/generate-questions",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # May return 200 or 402 if quota exceeded
        assert response.status_code in [200, 402]
        
        if response.status_code == 200:
            data = response.json()
            assert "questions" in data
            assert isinstance(data["questions"], list)
            assert len(data["questions"]) <= 5


@pytest.mark.asyncio
class TestAIDoubtSolver:
    """Test AI doubt solver endpoint."""
    
    async def test_solve_doubt(self, client: AsyncClient, teacher_token: str):
        """Test AI doubt solver."""
        payload = {
            "question": "What is the difference between velocity and speed?",
            "subject": "Physics",
            "context": "Kinematics chapter"
        }
        
        response = await client.post(
            "/api/v1/ai/doubt-solver",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # May return 200 or 402 if quota exceeded
        assert response.status_code in [200, 402]
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data or "explanation" in data


@pytest.mark.asyncio
class TestAIQuotaManagement:
    """Test AI quota and rate limiting."""
    
    async def test_quota_exceeded(self, client: AsyncClient, teacher_token: str):
        """Test behavior when AI quota is exceeded."""
        # This test assumes quota might be exceeded
        # In production, you'd set up a test tenant with 0 quota
        
        payload = {
            "subject": "Test",
            "topic": "Test Topic",
            "grade_level": 10
        }
        
        response = await client.post(
            "/api/v1/ai/lesson-plan",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        # Should either succeed or return quota exceeded
        assert response.status_code in [200, 402, 429]
        
        if response.status_code == 402:
            data = response.json()
            assert "quota" in data["message"].lower() or "limit" in data["message"].lower()
    
    async def test_unauthorized_ai_access(self, client: AsyncClient):
        """Test that unauthorized requests to AI endpoints are rejected."""
        response = await client.post(
            "/api/v1/ai/lesson-plan",
            json={"subject": "Math", "topic": "Test", "grade_level": 10}
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio  
class TestAIPermissions:
    """Test AI feature permissions."""
    
    async def test_student_cannot_generate_lesson_plan(
        self, 
        client: AsyncClient, 
        student_token: str
    ):
        """Test that students cannot generate lesson plans."""
        payload = {
            "subject": "Mathematics",
            "topic": "Test",
            "grade_level": 10
        }
        
        response = await client.post(
            "/api/v1/ai/lesson-plan",
            json=payload,
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Should return 403 Forbidden due to lack of permission
        assert response.status_code == 403
