import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from db.database import get_db, Base, engine
from db.models import User
from app.auth.utils import get_password_hash

client = TestClient(app)

# Create test database tables
Base.metadata.create_all(bind=engine)

def test_get_all_users_unauthorized():
    """Test that non-admin users cannot access admin routes"""
    response = client.get("/admin/users")
    assert response.status_code == 403

def test_update_user_role_unauthorized():
    """Test that non-admin users cannot update user roles"""
    response = client.patch("/admin/users/1/role", json={"is_admin": True})
    assert response.status_code == 403

def test_get_all_users_authorized():
    """Test that admin can access /admin/users"""
    # This would require a proper admin login to test
    pass

def test_update_user_role_authorized():
    """Test that admin can update user roles"""
    # This would require a proper admin login to test  
    pass
