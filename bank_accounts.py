from flask import Blueprint, request, jsonify
import logging
from flask_bcrypt import Bcrypt
from db import get_db_connection, get_user_by_email, check_is_valid_user_id
from exceptions import UserNotFoundError, DatabaseConnectionError
from uuid import uuid4
import datetime
import os
from auth_utils import encrypt_account_number

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])


# Create a Blueprint for users
bank_accounts_bp = Blueprint('bank_accounts', __name__)
bcrypt = Bcrypt()

@bank_accounts_bp.route('/bank_accounts', methods=['GET'])
def get_bank_accounts():
    user_id = request.args.get('user_id')
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            logging.debug("Couldn't connect to db.")
            return jsonify({'error' : 'Internal Error' }), 500
        
        cursor.execute('SELECT * FROM bank_accounts WHERE user_id = %s', (user_id,))
        bank_accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        accounts_list = [
            {
                'id': account['id'],
                'user_id': account['user_id'],
                'account_number': account['account_number'],
                'balance': account['balance'],
                'type': account['type'],
                'currency': account['currency'],
                'created_at': account['created_at'],
                'status': account['status']
            }
            for account in bank_accounts
        ]
        
        return jsonify(accounts_list), 200
        
    except Exception as e:
        logging.debug("General Error occured.")
        return jsonify({'error': 'Internal Error'}), 500
    
@bank_accounts_bp.route('/create_bank_account', methods=['POST'])
def create_bank_account():
    data = request.get_json()
    user_id = data['user_id']
    
    try:
        user_id = check_is_valid_user_id(str(data['user_id']))
        if not user_id:
            raise UserNotFoundError("Invalid user id.")

        # Required params
        account_id = str(uuid4())
        account_number = str(uuid4().int)[:6]
        encrypted_account_number = encrypt_account_number(account_number).decode('utf-8')
        currency = 'USD'
        balance = 0
        account_type = 'CHECKINGS'
        created_at = datetime.datetime.now()
        status = 'ACTIVE'
        
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError
        cursor.execute("""
            INSERT INTO bank_accounts (id, user_id, account_number, balance, type, currency, created_at, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (account_id, user_id, encrypted_account_number, balance, account_type, currency, str(created_at), status))
        
        conn.commit()
        cursor.close()
        conn.close()
            
    except DatabaseConnectionError as e:
        return jsonify({'error': 'Internal Error'}), 500
    except UserNotFoundError as e:
        return jsonify({'error' : 'User not found'}), 404
    except Exception as e:
        return jsonify({'error', 'Internal Erorr'}), 500
    
    return jsonify({'account_id': account_id, 'account_number': encrypted_account_number, 'created_at':created_at}), 201

    
    

