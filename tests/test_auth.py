import json
import pytest

# Assuming your app is created in app.py or server.py
from server import app  # or from server import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_register(client):
    response = client.post('/register', json={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'securepassword'
    })
    
    assert response.status_code == 201  # Adjust based on your actual response
    assert 'user_id' in json.loads(response.data)  # Ensure the response contains user_id

def test_login(client):
    # First, register a user
    client.post('/register', json={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'securepassword'
    })
    
    # Now, try to login
    response = client.post('/login', json={
        'email': 'john.doe@example.com',
        'password': 'securepassword'
    })
    
    assert response.status_code == 200
    assert 'token' in json.loads(response.data)  # Ensure the response contains a token

def test_get_user(client):
    # Register and login to get a token
    client.post('/register', json={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'password': 'securepassword'
    })
    
    login_response = client.post('/login', json={
        'email': 'john.doe@example.com',
        'password': 'securepassword'
    })
    
    token = json.loads(login_response.data)['token']
    
    # Get user data with the token
    response = client.get('/get_user', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    user_data = json.loads(response.data)
    assert user_data['email'] == 'john.doe@example.com'  # Ensure the email matches
