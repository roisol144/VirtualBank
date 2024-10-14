from flask import Blueprint, request, jsonify, g
import logging
from flask_bcrypt import Bcrypt
from db import get_db_connection, get_user_by_email, check_is_valid_user_id, check_is_valid_account_number, get_account_id_by_user_id
from exceptions import UserNotFoundError, DatabaseConnectionError, InsufficientFundsError
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
    
@bank_accounts_bp.route('/bank_accounts', methods=['POST'])
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
        balance = 2000
        account_type = 'CHECKINGS'
        created_at = datetime.datetime.now()
        status = 'ACTIVE'
         # ABOVE ADD ENUMS like a expection
        
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError
        
        # Enabling Auto Commit feature
        conn.autocommit = True
        
        cursor.execute("""
            INSERT INTO bank_accounts (id, user_id, account_number, balance, type, currency, created_at, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (account_id, user_id, encrypted_account_number, balance, account_type, currency, created_at, status))
        cursor.close()
        conn.close()
            
    except DatabaseConnectionError as e:
        return jsonify({'error': 'Internal Error'}), 500
    except UserNotFoundError as e:
        return jsonify({'error' : 'User not found'}), 404
    except Exception as e:
        return jsonify({'error', 'Internal Erorr'}), 500
    
    return jsonify({'account_id': account_id, 'account_number': encrypted_account_number, 'created_at':created_at}), 201

    
@bank_accounts_bp.route('/bank_accounts/transfer', methods=['POST'])
def transfer():
    logging.debug("Transfer function called")
    logging.debug(f"Request method: {request.method}")
    logging.debug(f"Request path: {request.path}")
    logging.debug(f"Request JSON: {request.get_json()}")
    
    data = request.get_json()
    to_account_number = data['to_account_number']
    amount = data['amount']
    transaction_type = data['transcation_type']  # Note: Typo in 'transaction'
    from_account_id = get_account_id_by_user_id(g.current_user_id)
    logging.debug(f"From account ID: {from_account_id}")

    
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400
    
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("Failed to connect to db.")
        
        conn.autocommit = True
        
        # Check if the sender's account exists
        cursor.execute("SELECT balance FROM bank_accounts WHERE id = %s", (from_account_id,))
        sender_account = cursor.fetchone()
        if not sender_account:
            raise ValueError("Sender's account not found")
        
        sender_balance = sender_account['balance']
        
        if sender_balance < amount:
            raise InsufficientFundsError("Insufficient funds.")
        
        if transaction_type == 'WITHDRAW':
            to_account_id = None
            cursor.execute("UPDATE bank_accounts SET balance = balance - %s WHERE id = %s", (amount, from_account_id))
        
        elif transaction_type == 'DEPOSIT': 
            if not to_account_number:
                raise ValueError("Account number is required for deposit.")
            
            receiver_account_id = check_is_valid_account_number(to_account_number)
            if not receiver_account_id:
                raise ValueError("Invalid receiver account number")
            
            cursor.execute("UPDATE bank_accounts SET balance = balance - %s WHERE id = %s", (amount, from_account_id))
            cursor.execute("UPDATE bank_accounts SET balance = balance + %s WHERE id = %s", (amount, receiver_account_id))
            to_account_id = receiver_account_id
        else:
            raise ValueError("Invalid transaction type")
        
        cursor.execute("""
                       INSERT INTO transactions (from_account_id, to_account_id, amount, transaction_type, transaction_date) 
                       VALUES (%s, %s, %s, %s, %s)""",
                       (from_account_id, to_account_id, amount, transaction_type, datetime.datetime.now()))
        
        return jsonify({'message': 'Transfer successful'}), 200

    except (DatabaseConnectionError, InsufficientFundsError, ValueError) as e:
        logging.error(f"Error in transfer: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error("Unexpected error in transfer", exc_info=True)
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal Error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            




