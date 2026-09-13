import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, engine
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_register_duplicate_email():
    response = client.post("/api/auth/register", json={
        "username": "testuser2",
        "email": "test@example.com",  # duplicate email
        "password": "testpassword"
    })
    assert response.status_code == 400

def test_login_user():
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user():
    # First register a user
    client.post("/api/auth/register", json={
        "username": "testuser3",
        "email": "test3@example.com",
        "password": "testpassword"
    })
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "testuser3",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]
    
    # Use token to access protected endpoint
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser3"