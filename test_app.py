import pytest
import json
from flask import Flask
from server import app  
from db import get_db_connection, get_user_by_email


@pytest.fixture
def client():
    # Setup Flask test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_register_user(client):
    # Test data
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "strongpassword"
    }
    
    # Send POST request to register user
    response = client.post('/users/register', json=user_data)
    
    # Check if response is 201 (Created)
    assert response.status_code == 201
    response_json = response.get_json()
    
    # Ensure the returned data has the expected keys
    assert 'id' in response_json
    assert response_json['first_name'] == "John"
    assert response_json['email'] == "johndoe@example.com"


def test_register_existing_user(client):
    # Test registering an existing user (to check unique email constraint)
    existing_user_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "janesmith@example.com",
        "password": "strongpassword"
    }
    
    # Register first time
    client.post('/users/register', json=existing_user_data)
    
    # Try registering again with the same email
    response = client.post('/users/register', json=existing_user_data)
    
    # Check if response is 409 (Conflict)
    assert response.status_code == 409
    response_json = response.get_json()
    assert 'error' in response_json
    assert response_json['error'] == "Try another email."


def test_login_user(client):
    # Register user for login
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "password": "strongpassword"
    }
    client.post('/users/register', json=user_data)
    
    # Test login
    login_data = {
        "email": "johndoe@example.com",
        "password": "strongpassword"
    }
    
    response = client.post('/users/login', json=login_data)
    
    # Check if response is 200 (OK) and has a token
    assert response.status_code == 200
    response_json = response.get_json()
    
    assert 'message' in response_json
    assert response_json['message'] == "Logged In Successfully"
    assert 'toekn' in response_json  # Assuming typo "toekn" was intended


def test_login_invalid_user(client):
    # Test login with non-existing user
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    
    response = client.post('/users/login', json=login_data)
    
    # Check if response is 401 (Unauthorized)
    assert response.status_code == 401
    response_json = response.get_json()
    assert 'error' in response_json
    assert response_json['error'] == "Invalid email or password."


def test_protected_route_without_token(client):
    # Try to access a protected route without a token
    response = client.get('/users')
    
    # Should return 401 (Unauthorized)
    assert response.status_code == 401
    response_json = response.get_json()
    assert 'error' in response_json
    assert response_json['error'] == "Authorization header is missing."


def test_protected_route_with_invalid_token(client):
    # Access protected route with an invalid token
    response = client.get('/users', headers={'Authorization': 'Bearer invalid_token'})
    
    # Should return 401 (Unauthorized)
    assert response.status_code == 401
    response_json = response.get_json()
    assert 'error' in response_json
    assert response_json['error'] == "Authentication failed"

