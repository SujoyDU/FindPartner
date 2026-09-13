# Tests authentication functionality without admin privileges
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.schemas import UserCreate, UserOut

client = TestClient(app)

def test_user_registration_without_admin_privileges():
    """Test that users can register without admin privileges"""
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "is_admin" not in data or data.get("is_admin") is False

def test_user_schema_validation():
    """Test that UserCreate schema works correctly"""
    user_data = {
        "username": "schemauser",
        "email": "schema@example.com",
        "password": "password123"
    }
    user_create = UserCreate(**user_data)
    assert user_create.username == "schemauser"
    assert not hasattr(user_create, 'is_admin')  # is_admin should not exist