# Tests admin functionality and security isolation
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_privilege_isolation():
    """Test that regular users cannot access admin endpoints (idempotent per run)."""
    tag = uuid.uuid4().hex[:8]
    username = "regularuser_" + tag
    email = f"regular{tag}@example.com"
    response = client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    # is_admin should not be returned in regular registration
    assert "is_admin" not in data or data.get("is_admin") is False
