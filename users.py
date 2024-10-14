from flask import Blueprint, request, jsonify
import psycopg2
import logging
from psycopg2.errors import UniqueViolation
from flask_bcrypt import Bcrypt
from auth_utils import generate_token
from uuid import uuid4
import datetime
from db import get_db_connection, get_user_by_email
import re
from exceptions import DatabaseConnectionError, UserNotFoundError

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
# Create a Blueprint for users
users_bp = Blueprint('users', __name__)
bcrypt = Bcrypt()

    
@users_bp.route('/users/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Input validation 
    require_fields = ['first_name', 'last_name', 'email', 'password']
    
    for field in require_fields:
        if field not in data or not data[field].strip():
            return jsonify({'Error occured': f"'{field}' is missing"}), 400
    
    email = data['email'].strip().lower() # email - not case sensitive, without spaces
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        logging.debug("Email format is invalid.")
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
            return jsonify({'error' : 'Internal Error' }), 500
        
        cursor.execute("""
            INSERT INTO users (id, first_name, last_name, email, password_hash, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (user_id, data['first_name'], data['last_name'], email, hashed_password, str(created_at), str(updated_at)))
        
        conn.commit() 
        cursor.close()
        conn.close()

    except Exception as e:
        logging.debug("Error creating user: ", exc_info=True)
        return jsonify({'error': 'Internal Error'}), 500
    
    except UniqueViolation as UV:
        logging.debug(f"Unique constraint violation for email {email}: {UV}")
        return jsonify({'error': 'Try another email.'}), 409

    # Return the created user data
    return jsonify({'id': user_id, 'first_name': data['first_name'], 'last_name': data['last_name'], 'email': data['email']}), 201

# Get User
@users_bp.route('/users', methods=['GET']) 
def get_user():
    #data = request.get_json() 
    email = request.args.get('email') 

    if not email:
        logging.error("Email not provided", exc_info=True)
        return jsonify({'error': "'email' is required."}), 400

    try:
        user = get_user_by_email(email)  
        return jsonify({
            'id': user['id'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'email': user['email']
        }), 200
    
    except UserNotFoundError as e:
        return jsonify({'error': 'User Not Found'}), 404
    except DatabaseConnectionError as e:
        logging.error("Couldn't connect to server", exc_info=True)
        return jsonify({'error': 'Internal Error'}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@users_bp.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = get_user_by_email(email) # Get USER

    if user and bcrypt.check_password_hash(user['password_hash'], password):
        login_time = datetime.datetime.now()
        token = generate_token(user['id'])
        logging.debug(f"user with email {email} logged in at {login_time}...")
        return jsonify({
            'message': 'Logged In Successfully',
            'toekn': token
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password.'}), 401