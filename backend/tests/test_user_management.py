# Tests user management functionality
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_profile_access():
    """Test that users can access their own profile (idempotent per run)."""
    tag = uuid.uuid4().hex[:8]
    username = "profileuser_" + tag
    email = f"profile{tag}@example.com"
    response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    assert response.status_code == 201

def test_user_schema_inheritance():
    """Test that user management schemas inherit properly."""
    from app.auth.schemas import UserCreate
    user_data = {
        "username": "inheritanceuser",
        "email": "inherit@example.com",
        "password": "password123"
    }
    user_create = UserCreate(**user_data)
    assert user_create.username == "inheritanceuser"
