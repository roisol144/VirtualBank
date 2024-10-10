from flask import Flask, jsonify, request, g
import psycopg2
import logging
import os
from psycopg2 import OperationalError
from users import users_bp
from bank_accounts import bank_accounts_bp
from db import get_db_connection 
from auth_utils import verify_token


app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

# Register the Blueprint with the Flask app
app.register_blueprint(users_bp)
app.register_blueprint(bank_accounts_bp)


open_routes = {
    ('/login', 'POST'): 'login',
    ('/register', 'POST'): 'register',
    ('/create_bank_account', 'POST'): 'create_bank_account'
    }

closed_routes = {
    ('/get_user', 'GET'): 'get_user',
    ('/bank_accounts', 'GET') : 'get_bank_account'
}

# Middleware for token auth
@app.before_request
def auth_token():
    # Normalize the request path (strip any trailing slashes) and lowercase it for comparison
    request_path = request.path.rstrip('/').lower()
    request_key = (request_path, request.method)
    logging.debug(f"Request key: {request_key}")
    
    # check if there's a match between path and method
    if request_key in open_routes:
        return

    elif request_key in closed_routes:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logging.debug('Token is missing or invalid')
            return jsonify({'error': 'Internal Error'}), 401
        try: 
            token = auth_header.split(" ")[1]
        except IndexError:
            logging.debug("Invalid token format")
            return jsonify({'error': 'Invalid format'}), 401
        
        try: 
            current_user_id = verify_token(token)
            
            if not current_user_id:
                return jsonify({'error': 'Internal Error'}), 401
            
            g.current_user_id = current_user_id
            
        except Exception as e:
            logging.debug("Token verification failed")
            return jsonify({'error': 'Internal error.'}), 401
        
    
    else: # route not in open/close routes
        logging.debug("Route doesn't exist.")
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
