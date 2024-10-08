from flask import Blueprint, request, jsonify
import psycopg2
from flask_bcrypt import Bcrypt
from auth_utils import generate_token
from uuid import uuid4
import datetime
from db import get_db_connection, get_user_by_email
from auth_utils import token_required # Toekn validation function
import re
import secrets

# Create a Blueprint for users
users_bp = Blueprint('users', __name__)
bcrypt = Bcrypt()

    
@users_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Input validation 
    require_fields = ['first_name', 'last_name', 'email', 'password']
    
    for field in require_fields:
        if field not in data or not data[field].strip():
            return jsonify({'Error occured': f"'{field}' is missing"}), 400
    
    email = data['email'].strip().lower() # email - not case sensitive, without spaces
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        return jsonify({'error:', 'Invalid email format'}), 400

    password = data['password'].strip()
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'})
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_id = str(uuid4())      # UUID generation
    created_at = datetime.datetime.now() # Get current time
    updated_at = datetime.datetime.now() # Get current time


    # Connect to the database and insert new user (handle database exceptions)
    try:
        # psycopg2 sql injection
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            return jsonify({'error' : 'Failed to connect to server' }), 500
        
        # Checking if a user with this email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'error' : 'User with this email already exist!'}), 409

        cursor.execute("""
            INSERT INTO users (id, first_name, last_name, email, password_hash, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (user_id, data['first_name'], data['last_name'], email, hashed_password, str(created_at), str(updated_at)))
        conn.commit() 
        cursor.close()
        conn.close()
        # more error hanlding regarding - like "user already exist"
    except Exception as e:
        return jsonify({'error': 'Error creating a new user'}), 500

    # Return the created user data
    return jsonify({'id': user_id, 'first_name': data['first_name'], 'last_name': data['last_name'], 'email': data['email']}), 201

# Get All Users
@users_bp.route('/users', methods=['GET'])
def get_users():
    # Retrieve users from the database (handle database exceptions)
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            return jsonify({'Error' : 'Failed to connect to server' }), 500
    
        cursor.execute("SELECT id, first_name, last_name, email FROM users;")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        # Return a list of users
        return jsonify([
            {'id': user['id'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'email': user['email']}
            for user in users
        ]), 200
    except Exception as e:
        return jsonify({'error': 'General error'}), 500
    

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = get_user_by_email(email) # Get USER

    if user and bcrypt.check_password_hash(user['password_hash'], password):
        token = generate_token(user['id'])
        
        return jsonify({
            'message': 'Logged In Successfully',
            'auth_token': token
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password.'}), 401

# testing auth process
@users_bp.route('/auth', methods=['GET'])
@token_required    
def checkAuth(current_user_id): 
    return jsonify({'message': 'Access granted to protected route', 'user id': current_user_id}), 200
    
        
