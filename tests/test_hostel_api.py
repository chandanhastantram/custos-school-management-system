"""
Sample API Tests for Hostel Module

Demonstrates testing patterns for CUSTOS backend.
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_hostel(client: AsyncClient, auth_headers: dict):
    """Test creating a new hostel."""
    hostel_data = {
        "name": "Boys Hostel A",
        "code": "BHA",
        "gender": "male",
        "total_capacity": 100,
        "address": "123 Campus Road",
        "is_active": True
    }
    
    response = await client.post(
        "/api/v1/hostel/hostels",
        json=hostel_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == hostel_data["name"]
    assert data["code"] == hostel_data["code"]
    assert "id" in data


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_hostels(client: AsyncClient, auth_headers: dict):
    """Test listing hostels."""
    response = await client.get(
        "/api/v1/hostel/hostels",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_hostel_unauthorized(client: AsyncClient):
    """Test creating hostel without authorization fails."""
    hostel_data = {
        "name": "Test Hostel",
        "code": "TH",
        "gender": "male",
        "total_capacity": 50
    }
    
    response = await client.post(
        "/api/v1/hostel/hostels",
        json=hostel_data
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.api
@pytest.mark.asyncio
async def test_create_room(client: AsyncClient, auth_headers: dict):
    """Test creating a room in a hostel."""
    # First create a hostel
    hostel_data = {
        "name": "Test Hostel",
        "code": "TH",
        "gender": "male",
        "total_capacity": 100
    }
    
    hostel_response = await client.post(
        "/api/v1/hostel/hostels",
        json=hostel_data,
        headers=auth_headers
    )
    hostel_id = hostel_response.json()["id"]
    
    # Create a room
    room_data = {
        "hostel_id": hostel_id,
        "room_number": "101",
        "floor": 1,
        "capacity": 4,
        "is_active": True
    }
    
    response = await client.post(
        "/api/v1/hostel/rooms",
        json=room_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["room_number"] == room_data["room_number"]
    assert data["hostel_id"] == hostel_id


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_hostel_occupancy(client: AsyncClient, auth_headers: dict):
    """Test getting hostel occupancy status."""
    response = await client.get(
        "/api/v1/hostel/occupancy",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
