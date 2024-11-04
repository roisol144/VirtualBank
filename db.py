import os
import psycopg2
import logging
from psycopg2 import DatabaseError, OperationalError
from urllib.parse import urlparse
from psycopg2.extras import RealDictCursor
from exceptions import UserNotFoundError, DatabaseConnectionError, AccountNotFoundError
from auth_utils import encrypt_account_number
import hashlib

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])


def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
        
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        conn.set_isolation_level('SERIALIZABLE')
        return cursor, conn
    except Exception as e:
        logging.error("Failed to connect to DB.", exc_info=True)
        raise DatabaseConnectionError("Could not connect to DB.") 
       
def get_user_by_email(email):
    try:
        cursor, conn = get_db_connection()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            raise UserNotFoundError(f"No user found with email:{email}")
        cursor.close()
        conn.close()
        return user
    
    
    except DatabaseConnectionError as e:
        raise DatabaseConnectionError("Failed to connect to the db")

    except Exception as e:
        logging.debug(f"Error fetching user by email: {email}", exc_info=True)
        return None


def check_is_valid_user_id(user_id):
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("Failed to connect")
        
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise UserNotFoundError(f"No user found.")
        
        return user['id']
    
    except OperationalError as e:
        logging.error(f"An error occured when trying to fetch user.", exc_info=True)
        raise DatabaseConnectionError("Failed to connect to the db")

    except DatabaseError as e:
            logging.error("Database error:", exc_info=True)
            raise DatabaseConnectionError("An error occurred while fetching user.")
        
    except Exception as e:
        logging.debug(f"Error fetching user by user id: {user_id}", exc_info=True)
        return None
    
    finally:
        # Ensure that the cursor and connection are closed to avoid leaks
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def check_is_valid_account_number(account_number):
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("Failed to connect")
        hashed_account_number = hashlib.sha256(account_number.encode()).hexdigest()
        logging.debug(f"Hashed account number: {hashed_account_number}")
        cursor.execute("SELECT * FROM bank_accounts WHERE hashed_account_number = %s", (hashed_account_number,))
        account = cursor.fetchone()
        if not account:
            raise AccountNotFoundError(f"No account found with number {account_number}")
        
        account_id = account['id']
        return account_id
    
    except DatabaseConnectionError as e:
        logging.error("Database connection error:", exc_info=True)
        raise
    
    except AccountNotFoundError as e:
        logging.error(f"Account not found: {str(e)}", exc_info=True)
        raise AccountNotFoundError(f"No account found with number {account_number}")
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_accounts_id_by_user_id(user_id):
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("Failed to connect to db.")
        
        cursor.execute("SELECT id FROM bank_accounts WHERE user_id = %s", (user_id,))
        results = cursor.fetchall()  # Fetch all results
        
        return [result['id'] for result in results] if results else None
    
    except DatabaseConnectionError:
        logging.error(f"Database connection error: {user_id}", exc_info=True)
        return None
    except AccountNotFoundError:
        logging.error(f"Account not found for user: {user_id}", exc_info=True)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
            
def get_accounts_numbers_by_user_id(user_id):
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("Failed to connect to db.")
        
        cursor.execute("SELECT hashed_account_number FROM bank_accounts WHERE user_id = %s", (user_id,))
        results = cursor.fetchall()  # Fetch all results
        
        return [result['hashed_account_number'] for result in results] if results else None
    
    except DatabaseConnectionError:
        logging.error(f"Database connection error: {user_id}", exc_info=True)
        return None
    except AccountNotFoundError:
        logging.error(f"Account not found for user: {user_id}", exc_info=True)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

