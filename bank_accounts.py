from flask import Blueprint, request, jsonify, g
import logging
from flask_bcrypt import Bcrypt
from db import get_db_connection, get_user_by_email, check_is_valid_user_id, check_is_valid_account_number, get_account_id_by_user_id
from exceptions import UserNotFoundError, DatabaseConnectionError, InsufficientFundsError, AccountNotFoundError
from uuid import uuid4
import datetime
import os
from auth_utils import encrypt_account_number
import hashlib
from enum import Enum


# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

class AccountType(Enum):
    CHECKINGS = 'CHECKINGS'
    SAVINGS = 'SAVINGS'
    BUSINESS = 'BUSINESS'
    
class Currency(Enum):
    USD = 'USD'
    EUR = 'EUR'
    GBP = 'GBP'
class Status(Enum):
    ACTIVE = 'ACTIVE'
    SUSPENDED = 'SUSPENDED'
    CLOSED = 'CLOSED'
    


# Create a Blueprint for users
bank_accounts_bp = Blueprint('bank_accounts', __name__)
bcrypt = Bcrypt()

@bank_accounts_bp.route('/bank_accounts', methods=['GET'])
def get_bank_accounts():
    user_id = request.args.get('user_id')
    try:
        cursor, conn = get_db_connection()
        
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
    
    except DatabaseConnectionError as e:
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
        account_number = str(int(uuid4()))[:6]
        logging.debug(f"Account number: {account_number}")
        salt = os.urandom(16).hex()
        hashed_account_number = hashlib.sha256((account_number + salt).encode()).hexdigest()
        encrypted_account_number = encrypt_account_number(account_number).decode('utf-8')
        currency = Currency.USD.value 
        balance = 0  # change it to other default value that will be config
        account_type = AccountType.CHECKINGS.value
        created_at = datetime.datetime.now()
        status = Status.ACTIVE.value
        
        cursor, conn = get_db_connection()
        
        cursor.execute("""
            INSERT INTO bank_accounts (id, user_id, account_number, balance, type, currency, created_at, status, hashed_account_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (account_id, user_id, encrypted_account_number, balance, account_type, currency, created_at, status, hashed_account_number))
        cursor.close()
        conn.close()
            
    except DatabaseConnectionError as e:
        return jsonify({'error': 'Internal Error'}), 500
    except UserNotFoundError as e:
        return jsonify({'error' : 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Internal Error'}), 500
    
    return jsonify({'account_id': account_id, 'account_number': encrypted_account_number, 'created_at': created_at}), 201

    
@bank_accounts_bp.route('/bank_accounts/transfer', methods=['POST'])
def transfer():    
    data = request.get_json()
    transfer_id = str(uuid4())
    to_account_number = data.get('to_account_number')
    amount = data.get('amount')
    transaction_type = data.get('transaction_type')
    logging.debug(f"Parsed data: transfer_id={transfer_id}, to_account_number={to_account_number}, amount={amount}, transaction_type={transaction_type}")

    
    # Validate input data
    if not amount or not isinstance(amount, (int, float)):
        return jsonify({'error': 'Invalid amount'}), 400
    if not transaction_type or transaction_type not in ['WITHDRAW', 'DEPOSIT']:
        return jsonify({'error': 'Invalid transaction type'}), 400
    
    try:
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        from_account_id = get_account_id_by_user_id(g.current_user_id)
        logging.debug(f"From account ID: {from_account_id}")
        
        if not from_account_id:
            raise AccountNotFoundError("Account not found for the current user")
        
        cursor, conn = get_db_connection() 
                
        # Check if the sender's account exists
        cursor.execute("SELECT balance FROM bank_accounts WHERE id = %s", (from_account_id,))
        sender_account = cursor.fetchone()
        if not sender_account:
            raise AccountNotFoundError("Sender's account not found")

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
        
        cursor.execute("""
                       INSERT INTO transactions (id, from_account, to_account, amount, type, transaction_date) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                       (transfer_id, from_account_id, to_account_id, amount, transaction_type, datetime.datetime.now()))
        
        return jsonify({'message': 'Transfer successful'}), 200

    except (DatabaseConnectionError, InsufficientFundsError, ValueError, AccountNotFoundError) as e:
        logging.error(f"Error in transfer: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error in transfer: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
        return jsonify({'error': 'Internal Error'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()