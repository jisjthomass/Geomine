import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch

# Setup dummy secret key for testing before importing anything else
os.environ["JWT_SECRET_KEY"] = "dummy-test-key-12345"

from main import app
from auth.security import get_password_hash, verify_password, create_access_token
from auth.schemas import AuthenticatedUser
from datetime import timedelta
import time
import jwt
from auth.security import SECRET_KEY, ALGORITHM

client = TestClient(app)

def test_password_hashing():
    password = "supersecretpassword"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_creation_and_expiry():
    data = {"sub": "testuser"}
    
    # Test valid token
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "role" not in decoded
    
    # Test expiry
    expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, SECRET_KEY, algorithms=[ALGORITHM])

@patch('auth.routes.authenticate_user')
def test_login_success_username(mock_authenticate_user):
    mock_authenticate_user.return_value = AuthenticatedUser(id=1, username="testuser", email="test@example.com", is_active=True)
    response = client.post("/api/auth/login", json={"identifier": "testuser", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@patch('auth.routes.authenticate_user')
def test_login_success_email(mock_authenticate_user):
    mock_authenticate_user.return_value = AuthenticatedUser(id=1, username="testuser", email="test@example.com", is_active=True)
    response = client.post("/api/auth/login", json={"identifier": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

@patch('auth.routes.authenticate_user')
def test_login_invalid_credentials(mock_authenticate_user):
    mock_authenticate_user.return_value = None
    response = client.post("/api/auth/login", json={"identifier": "testuser", "password": "wrongpassword"})
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

@patch('auth.dependencies.get_user')
def test_protected_route_with_valid_token(mock_get_user):
    mock_get_user.return_value = AuthenticatedUser(id=1, username="testuser", email="test@example.com", is_active=True)
    token = create_access_token({"sub": "testuser"})
    
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

@patch('auth.dependencies.get_user')
def test_inactive_user_cannot_access(mock_get_user):
    mock_get_user.return_value = AuthenticatedUser(id=1, username="inactive_user", email="inactive@example.com", is_active=False)
    token = create_access_token({"sub": "inactive_user"})
    
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"

# REGISTRATION TESTS
@patch('auth.routes.register_user')
def test_successful_registration(mock_register_user):
    mock_register_user.return_value = {"success": True, "error": None, "status": 201}
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "validpassword"
    })
    assert response.status_code == 201
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    assert response.json()["message"] == "User registered successfully"

@patch('auth.routes.register_user')
def test_duplicate_username_rejection(mock_register_user):
    mock_register_user.return_value = {"success": False, "error": "Username already exists", "status": 409}
    response = client.post("/api/auth/register", json={
        "username": "existinguser",
        "email": "new@example.com",
        "password": "validpassword"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already exists"

@patch('auth.routes.register_user')
def test_duplicate_email_rejection(mock_register_user):
    mock_register_user.return_value = {"success": False, "error": "Email already exists", "status": 409}
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "existing@example.com",
        "password": "validpassword"
    })
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already exists"

def test_invalid_email_rejection():
    # pydantic EmailStr validation will fail before route logic
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "not-an-email",
        "password": "validpassword"
    })
    assert response.status_code == 422

def test_password_too_short():
    response = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "short"
    })
    assert response.status_code == 422
    assert "at least 8 characters" in response.json()["detail"]

def test_registration_does_not_expose_password_or_hash():
    with patch('auth.routes.register_user') as mock_register_user:
        mock_register_user.return_value = {"success": True, "error": None, "status": 201}
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "validpassword"
        })
        assert response.status_code == 201
        content = response.text
        assert "password" not in content
        assert "hash" not in content

def test_public_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert "ONLINE" in response.json()["status"]
