from flask import Flask, jsonify
import psycopg2
import os
from psycopg2 import OperationalError
from users import users_bp  # Import the Blueprint from users.py(for the APIs handlers)
from db import get_db_connection 


app = Flask(__name__)
# Load secret key from environment variable
#sapp.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
# Register the Blueprint with the Flask app
app.register_blueprint(users_bp)

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
