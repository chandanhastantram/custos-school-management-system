"""
Tests for Lesson Plans API endpoints.
"""

import pytest
from uuid import uuid4
from datetime import date, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestLessonPlansAPI:
    """Test Lesson Plans CRUD operations."""
    
    async def test_create_lesson_plan(self, client: AsyncClient, teacher_token: str, test_data: dict):
        """Test creating a lesson plan."""
        payload = {
            "subject_id": str(test_data["subject_id"]),
            "topic": "Introduction to Algebra",
            "objectives": [
                "Understand basic algebraic concepts",
                "Solve simple equations"
            ],
            "activities": [
                "Lecture on variables",
                "Practice problems"
            ],
            "resources": ["Textbook Chapter 1", "Online videos"],
            "scheduled_date": str(date.today() + timedelta(days=7))
        }
        
        response = await client.post(
            "/api/v1/academics/lesson-plans",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "Introduction to Algebra"
        assert len(data["objectives"]) == 2
        assert "id" in data
    
    async def test_list_lesson_plans(self, client: AsyncClient, teacher_token: str):
        """Test listing lesson plans."""
        response = await client.get(
            "/api/v1/academics/lesson-plans",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
    
    async def test_get_lesson_plan(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str):
        """Test getting a specific lesson plan."""
        response = await client.get(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lesson_plan_id
        assert "topic" in data
        assert "units" in data
    
    async def test_update_lesson_plan(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str):
        """Test updating a lesson plan."""
        payload = {
            "topic": "Advanced Algebra Concepts",
            "objectives": ["Master quadratic equations"]
        }
        
        response = await client.patch(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Advanced Algebra Concepts"
    
    async def test_delete_lesson_plan(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str):
        """Test deleting a lesson plan."""
        response = await client.delete(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert get_response.status_code == 404
    
    async def test_activate_lesson_plan(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str):
        """Test activating a draft lesson plan."""
        response = await client.post(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}/activate",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
    
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that unauthorized requests are rejected."""
        response = await client.get("/api/v1/academics/lesson-plans")
        assert response.status_code == 401
    
    async def test_create_lesson_plan_validation(self, client: AsyncClient, teacher_token: str):
        """Test validation on lesson plan creation."""
        # Missing required fields
        payload = {
            "topic": "Test Topic"
            # Missing subject_id, objectives, etc.
        }
        
        response = await client.post(
            "/api/v1/academics/lesson-plans",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestLessonPlanUnits:
    """Test Lesson Plan Units operations."""
    
    async def test_add_unit_to_plan(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str, test_data: dict):
        """Test adding a unit to a lesson plan."""
        payload = {
            "topic_id": str(test_data["topic_id"]),
            "estimated_periods": 3,
            "notes": "Introduction to the topic"
        }
        
        response = await client.post(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}/units",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["estimated_periods"] == 3
        assert "id" in data
    
    async def test_list_plan_units(self, client: AsyncClient, teacher_token: str, lesson_plan_id: str):
        """Test listing units for a lesson plan."""
        response = await client.get(
            f"/api/v1/academics/lesson-plans/{lesson_plan_id}/units",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_update_unit(self, client: AsyncClient, teacher_token: str, unit_id: str):
        """Test updating a unit."""
        payload = {
            "estimated_periods": 5,
            "notes": "Extended coverage needed"
        }
        
        response = await client.patch(
            f"/api/v1/academics/lesson-plans/units/{unit_id}",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["estimated_periods"] == 5
    
    async def test_delete_unit(self, client: AsyncClient, teacher_token: str, unit_id: str):
        """Test deleting a unit."""
        response = await client.delete(
            f"/api/v1/academics/lesson-plans/units/{unit_id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 204


@pytest.mark.asyncio
class TestTeachingProgress:
    """Test Teaching Progress tracking."""
    
    async def test_record_progress(self, client: AsyncClient, teacher_token: str, unit_id: str):
        """Test recording teaching progress."""
        payload = {
            "date": str(date.today()),
            "periods_taught": 2,
            "notes": "Covered first half of the topic",
            "completion_percentage": 50
        }
        
        response = await client.post(
            f"/api/v1/academics/lesson-plans/units/{unit_id}/progress",
            json=payload,
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["periods_taught"] == 2
        assert data["completion_percentage"] == 50
    
    async def test_list_progress(self, client: AsyncClient, teacher_token: str, unit_id: str):
        """Test listing progress entries."""
        response = await client.get(
            f"/api/v1/academics/lesson-plans/units/{unit_id}/progress",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
