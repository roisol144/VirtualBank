import os
import psycopg2
import logging
from psycopg2 import DatabaseError, OperationalError
from urllib.parse import urlparse
from psycopg2.extras import RealDictCursor
from exceptions import UserNotFoundError, DatabaseConnectionError

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])


def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return cursor, conn
    except Exception as e:
        logging.error("Failed to connect to DB.", exc_info=True)
        return None, None
    
def get_user_by_email(email):
    try:
        cursor, conn = get_db_connection()
        if cursor is None or conn is None:
            raise DatabaseConnectionError("No connection to DB.")
            logging.debug("No connection to the database.")
            return None

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            raise UserNotFoundError(f"No user found with email:{email}")
        cursor.close()
        conn.close()
        return user
    
    except OperationalError as e:
        logging.error(f"An error occured when trying to fetch user.", exc_info=True)
        raise DatabaseConnectionError("Failed to connect to the db")

    except DatabaseError as e:
            logging.error("Database error:", exc_info=True)
            raise DatabaseConnectionError("An error occurred while fetching user.")
        
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
    