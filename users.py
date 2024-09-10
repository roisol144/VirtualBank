from flask import Blueprint, request, jsonify
import psycopg2
from flask_bcrypt import Bcrypt
from uuid import uuid4
from datetime import datetime

# Create a Blueprint for users
users_bp = Blueprint('users', __name__)
bcrypt = Bcrypt()

# PostgreSQL connection setup (update as needed)
DATABASE_URL = "postgres://postgres:solo6755@postgres:5432/postgres"

@users_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password_hash']).decode('utf-8')
    
    # UUID generation
    user_id = str(uuid4())
    created_at = datetime.now()  # Get current UTC time
    updated_at = datetime.now()

    # Connect to the database and insert new user (handle database exceptions)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (id, first_name, last_name, email, password_hash, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (user_id, data['first_name'], data['last_name'], data['email'], hashed_password, str(created_at), str(updated_at)))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Return the created user data
    return jsonify({'id': user_id, 'first_name': data['first_name'], 'last_name': data['last_name'], 'email': data['email']}), 201

@users_bp.route('/users', methods=['GET'])
def get_users():
    # Retrieve users from the database (handle database exceptions)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, email FROM users;")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        # Return a list of users
        return jsonify([
            {'id': user[0], 'first_name': user[1], 'last_name': user[2], 'email': user[3]}
            for user in users
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
