from flask import Blueprint, request, jsonify, g
import logging
from flask_bcrypt import Bcrypt
from db import get_db_connection, get_accounts_numbers_by_user_id, check_is_valid_user_id, check_is_valid_account_number, get_accounts_id_by_user_id
from exceptions import UserNotFoundError, DatabaseConnectionError, InsufficientFundsError, AccountNotFoundError
from uuid import uuid4
import datetime
import os
from auth_utils import encrypt_account_number, hash_account_number
import hashlib
from enum import Enum
import random


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
    
    except DatabaseConnectionError as e:
        return jsonify({'error': 'Internal Error'}), 500
    except Exception as e:
        logging.debug("General Error occured.")
        return jsonify({'error': 'Internal Error'}), 500
    

    
@bank_accounts_bp.route('/bank_accounts', methods=['POST'])
def create_bank_account():
    data = request.get_json()
    user_id = data['user_id']
    currency = data['currency']
    account_type = data['account_type']
    
    try:
        user_id = check_is_valid_user_id(str(data['user_id']))
        if not user_id:
            raise UserNotFoundError("Invalid user id.")
        if not currency: # Might need to validate it in the case of an unexpected value
            currency = Currency.USD.value
        if not account_type:
            account_type = AccountType.CHECKINGS.value # Might need to validate it in the case of an unexpected value

        # Required params
        account_id = str(uuid4())
        account_number = str(random.randint(100000, 999999))
        logging.debug(f"Account number: {account_number}")
        salt = str(os.getenv('SALT'))
        hashed_account_number = hashlib.sha256((account_number + salt).encode()).hexdigest()
        encrypted_account_number = encrypt_account_number(account_number).decode('utf-8')
        balance = 0  # change it to other default value that will be config
        created_at = datetime.datetime.now()
        status = Status.ACTIVE.value
        
        cursor, conn = get_db_connection()
        cursor.execute("BEGIN;")
        
        cursor.execute("""
            INSERT INTO bank_accounts (id, user_id, account_number, balance, type, currency, created_at, status, hashed_account_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (account_id, user_id, encrypted_account_number, balance, account_type, currency, created_at, status, hashed_account_number))
        conn.commit()
        cursor.close()
        conn.close()
            
    except DatabaseConnectionError as e:
        return jsonify({'error': 'Internal Error'}), 500
    except UserNotFoundError as e:
        return jsonify({'error' : 'User not found'}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Internal Error'}), 500
    
    return jsonify({'account_id': account_id, 'account_number': encrypted_account_number, 'created_at': created_at}), 201

    

@bank_accounts_bp.route('/bank_accounts/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    amount = data['amount']
    transfer_id = str(uuid4())
    account_number_for_deposit = data['account_number']
    current_user_id = g.current_user_id
    transaction_type = "DEPOSIT"
    user_hashed_accounts_numbers_list = get_accounts_numbers_by_user_id(current_user_id)
    hashed_account_number = hash_account_number(account_number_for_deposit)    
    
    if not amount or not isinstance(amount, (int, float)):
        raise ValueError("Invalid/Missing amount.")
    if not user_hashed_accounts_numbers_list:
        raise AccountNotFoundError("User has no bank accounts.")
    
    if hashed_account_number not in user_hashed_accounts_numbers_list:
        raise AccountNotFoundError("No account found.")
    
    try:
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive.'}), 400
        
        cursor, conn = get_db_connection()
        cursor.execute("BEGIN;")
        
        cursor.execute("UPDATE bank_accounts SET balance = balance + %s WHERE hashed_account_number = %s", (amount, hashed_account_number))
        cursor.execute("""
                       INSERT INTO transactions (id, from_account, to_account, amount, type, transaction_date) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                       (transfer_id, hashed_account_number, hashed_account_number, amount, transaction_type, datetime.datetime.now()))
        conn.commit()
        return jsonify({'message': 'Deposit Successfully!'}), 200
        
    except ValueError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    
    except AccountNotFoundError as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Deposit failed.'}), 400    
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@bank_accounts_bp.route('/bank_accounts/withdraw', methods=['POST'])
def withdraw():
    data = request.get_json()
    amount_to_withdraw = data['amount']
    transaction_type = "WITHDRAW"
    account_number_for_withdrawal = data['account_number']
    transfer_id = str(uuid4())
    current_user_id = g.current_user_id
    user_hashed_accounts_numbers_list = get_accounts_numbers_by_user_id(current_user_id)
    hashed_account_number = hash_account_number(account_number_for_withdrawal)
    
    if not amount_to_withdraw or not isinstance(amount_to_withdraw, (int, float)):
        raise ValueError("Invalid/Missing amount.")
    if not user_hashed_accounts_numbers_list:   
        raise AccountNotFoundError("User has no bank accounts.")
    
    if hashed_account_number not in user_hashed_accounts_numbers_list:
        raise AccountNotFoundError("No account found.")
    
    try:
        if amount_to_withdraw <= 0:
            return jsonify({'error': 'Amount must be positive.'}),400
        cursor, conn = get_db_connection()
        
        if hashed_account_number not in user_hashed_accounts_numbers_list:
            raise AccountNotFoundError("No account found.")
        
        cursor.execute("SELECT balance FROM bank_accounts WHERE hashed_account_number = %s", (hashed_account_number,))
        account_to_withdraw_from = cursor.fetchone()
        if account_to_withdraw_from['balance'] < amount_to_withdraw:
            raise InsufficientFundsError("Insufficient Funds In Account.")
        
        cursor.execute("BEGIN;")
        cursor.execute("UPDATE bank_accounts SET balance = balance - %s WHERE hashed_account_number = %s", (amount_to_withdraw, hashed_account_number))
        cursor.execute("""
                       INSERT INTO transactions (id, from_account, to_account, amount, type, transaction_date) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                       (transfer_id, hashed_account_number, hashed_account_number, amount_to_withdraw, transaction_type, datetime.datetime.now()))
        conn.commit()  
        return jsonify({'message': 'Withdraw Succeded!'}), 200   
          
    except InsufficientFundsError as e:
        return jsonify({'error': str(e)}), 400
    
    except AccountNotFoundError as e:
        return jsonify({'error': str(e)}), 400
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        logging.debug(f"Error: {e}")
        return jsonify({'error' : 'General Erorr'}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    

@bank_accounts_bp.route('/bank_accounts/transfer', methods=['POST'])
def transfer():    
    data = request.get_json()
    transfer_id = str(uuid4())
    to_account_number = data.get('to_account_number')
    from_account_number = data.get('from_account_number')
    hashed_account_number_of_reciever = hash_account_number(to_account_number)
    hashed_account_nunber_of_sender = hash_account_number(from_account_number)
    tansaction_type = "TRANSFER"
    amount = data.get('amount')
    
    # Validate input data
    if not amount or not isinstance(amount, (int, float)):
        return jsonify({'error': 'Invalid amount'}), 400
    
    try:
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        
        if not to_account_number:
            raise ValueError("Account number is required for deposit.")
        
        # Establish db connection and transaction
        cursor, conn = get_db_connection() 
        cursor.execute("BEGIN;")
        
        # Check if the sender's account exists
        # Note to self - Check how to auth works here, how its possible to take money from account - will it auth first ? 
        cursor.execute("SELECT balance FROM bank_accounts WHERE hashed_account_number = %s", (hashed_account_nunber_of_sender,))
        sender_account = cursor.fetchone()
        if not sender_account:
            raise AccountNotFoundError("Sender's account not found")

        sender_balance = sender_account['balance']
        if sender_balance < amount:
            raise InsufficientFundsError("Insufficient funds.")
        
        # Validate Bank Account Number - 
        cursor.execute("SELECT balance FROM bank_accounts WHERE hashed_account_number = %s", (hashed_account_number_of_reciever,))
        account_to_transfer_money_to = cursor.fetchone()
        # Check if no account found
        if not account_to_transfer_money_to:
            raise AccountNotFoundError("No Account Found.")
            
        cursor.execute("UPDATE bank_accounts SET balance = balance - %s WHERE hashed_account_number = %s", (amount, hashed_account_nunber_of_sender))
        cursor.execute("UPDATE bank_accounts SET balance = balance + %s WHERE hashed_account_number = %s", (amount, hashed_account_number_of_reciever))        
        cursor.execute("""
                       INSERT INTO transactions (id, from_account, to_account, amount, type, transaction_date) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                       (transfer_id, hashed_account_number_of_reciever, hashed_account_nunber_of_sender, amount, tansaction_type, datetime.datetime.now()))
        conn.commit()
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