from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from db import get_db_connection, get_user_by_email
import datetime


# Create a Blueprint for users
bank_accounts_bp = Blueprint('bank_accounts', __name__)
bcrypt = Bcrypt()

@bank_accounts_bp.route('/bank_accounts', methods=['GET'])
def get_bank_accounts():
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            return jsonify({'Error' : 'Failed to connect to server' }), 500
        
        cursor.execute('SELECT * FROM bank_accounts')
        bank_accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            {'id': account['id'], 'user_id': account['user_id'], 'account_number': account['account_number'], 'balance': account['balance'],
             'type': account['type'], 'currency': account['currency'], 'created_at': account['created_at'], 'status': account['status']}
            for account in bank_accounts
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed retrieving all bank accounts'}), 500