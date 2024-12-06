from flask import Flask, jsonify, request, g
import psycopg2
import logging
import time
import os
from psycopg2 import OperationalError
from users import users_bp
from bank_accounts import bank_accounts_bp
from db import get_db_connection 
from auth_utils import verify_token
from exceptions import TokenVerificationError
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

# Register the Blueprint with the Flask app
app.register_blueprint(users_bp)
app.register_blueprint(bank_accounts_bp)

# Middleware for access log
@app.before_request
def log_request_info():
    g.start_time = time.time()
    logging.info(f"New Request: TYPE: {request.method}, PATH: {request.path}, TIME:{g.start_time}")
    logging.info(f"Headers: {request.headers}")
    if hasattr(g, 'current_user_id'):
        logging.debug(f"Current user ID: {g.current_user_id}")
    else:
        logging.debug("No current user ID set")

@app.after_request
def log_reponse_info(response):
    response_duration = time.time() - g.start_time
    logging.info(f"Request Completed. Time took {response_duration}")
    return response

# protected/non-protected routes
open_routes = {
    ('/users/login', 'POST'): 'login',
    ('/users/login', 'OPTIONS'): 'login',
    ('/users/register', 'POST'): 'register',
    ('/users/register', 'OPTIONS'): 'register'
    }

# Middleware for token auth
@app.before_request
def auth_token():
    request_path = request.path.rstrip('/').lower()
    request_method = request.method
    request_key = (request_path, request_method)
    logging.debug(f"Request key: {request_key}")
    logging.debug(f"Open routes: {open_routes}")

    if request_key in open_routes:
        logging.debug(f"Matched open route: {request_key}")
        return
    
    route_exists = any(rule.rule == request_path and rule.methods.intersection({request_method}) for rule in app.url_map.iter_rules())

    if route_exists:  # Check if the route is valid
        logging.debug(f"Route requires authorization: {request_key}")
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header is missing.'}), 401
        
        auth_parts = auth_header.split()
        
        if len(auth_parts) < 2:
            return jsonify({'error': 'Invalid authorization header format.'}), 401
        
        scheme = auth_parts[0].lower()
        
        if scheme == 'bearer':
            token = auth_parts[1]
            try:
                current_user_id = verify_token(token)
                if not current_user_id:
                    raise TokenVerificationError
                
                g.current_user_id = current_user_id  # setting the current user id to the global variable
                
            except TokenVerificationError as e:
                logging.debug(f"Failed to authenticate the token of user {current_user_id}", exc_info=True)
                return jsonify({'error': 'Authentication failed'}), 401
            
        else:
            logging.debug(f"Invalid authorization scheme {scheme}")
            return jsonify({'error': 'Unsupported authorization scheme.'})    
    else:  # Route not found
        logging.debug(f"Route not found: {request_key}")
        return jsonify({'error': 'Not Found'}), 404

def check_database_connection():
    cursor, conn = get_db_connection()
    if conn:
        conn.close()
        return True
    return False

@app.route('/status', methods=['GET'])
def status():
    db_status = check_database_connection()

    # Creating JSON response 
    response = {
        'status': 'success' if db_status else 'failure',
        'database_connected': db_status
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
