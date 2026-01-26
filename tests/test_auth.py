"""
CUSTOS Auth Tests
"""

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, test_tenant_id: str):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "invalid@test.com", "password": "wrong"},
            headers={"X-Tenant-ID": test_tenant_id},
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_missing_tenant(self, client: AsyncClient):
        """Test login without tenant ID."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "test"},
        )
        assert response.status_code == 422  # Missing header
    
    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me endpoint without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestPasswordValidation:
    """Test password validation."""
    
    def test_password_hash(self):
        """Test password hashing."""
        from app.auth.password import hash_password, verify_password
        
        password = "SecurePass@123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)
    
    def test_password_validator(self):
        """Test password strength validator."""
        from app.auth.password import PasswordValidator
        
        validator = PasswordValidator()
        
        # Valid password
        is_valid, errors = validator.validate("StrongPass@123")
        assert is_valid
        assert len(errors) == 0
        
        # Too short
        is_valid, errors = validator.validate("Aa1!")
        assert not is_valid
        
        # No uppercase
        is_valid, errors = validator.validate("weakpass@123")
        assert not is_valid
        
        # No special char
        is_valid, errors = validator.validate("WeakPass123")
        assert not is_valid


class TestJWT:
    """Test JWT token handling."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        from uuid import uuid4
        from app.auth.jwt import create_access_token, verify_access_token
        
        user_id = uuid4()
        tenant_id = uuid4()
        
        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            email="test@test.com",
            roles=["teacher"],
            permissions=["lesson:view", "lesson:create"],
        )
        
        assert token is not None
        
        # Verify token
        payload = verify_access_token(token)
        assert payload is not None
        assert payload.sub == str(user_id)
        assert payload.email == "test@test.com"
        assert "teacher" in payload.roles
    
    def test_token_pair(self):
        """Test token pair creation."""
        from uuid import uuid4
        from app.auth.jwt import create_token_pair
        
        pair = create_token_pair(
            user_id=uuid4(),
            tenant_id=uuid4(),
            email="test@test.com",
            roles=["student"],
            permissions=[],
        )
        
        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0
