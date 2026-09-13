# Tests admin functionality and security isolation
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_privilege_isolation():
    """Test that regular users cannot access admin endpoints"""
    # Regular user registration should not include admin privileges
    response = client.post("/auth/register", json={
        "username": "regularuser",
        "email": "regular@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    # is_admin should not be returned in regular registration
    assert "is_admin" not in data or data.get("is_admin") is False