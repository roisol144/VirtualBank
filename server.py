from flask import Flask, jsonify
import psycopg2
from psycopg2 import OperationalError
from users import users_bp  # Import the Blueprint from users.py(for the APIs handlers)


app = Flask(__name__)

# Register the Blueprint with the Flask app
app.register_blueprint(users_bp)

# Database params
DB_USER = 'postgres'
DB_PASSWORD = 'solo6755'
DB_HOST = 'postgres'  
DB_PORT = '5432'      
DB_NAME = 'postgres'

def check_database_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.close()
        return True
    except OperationalError:
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
