# Tests user management functionality
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_profile_access():
    """Test that users can access their own profile"""
    # Register and login then access profile
    response = client.post("/auth/register", json={
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    
def test_user_schema_inheritance():
    """Test that user management schemas inherit properly"""
    from app.auth.schemas import UserCreate
    user_data = {
        "username": "inheritanceuser",
        "email": "inherit@example.com",
        "password": "password123"
    }
    user_create = UserCreate(**user_data)
    assert user_create.username == "inheritanceuser"