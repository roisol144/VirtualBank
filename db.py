import os
import psycopg2
from urllib.parse import urlparse
from psycopg2.extras import RealDictCursor

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return cursor, conn
    except Exception as e:
        print(f"Failed to connect to DB.")
        return None, None
    
def get_user_by_email(email):
    try:
        cursor, conn = get_db_connection()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone() # return dict - with properties as keys
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error fetching user by email: {email}")
        return None

    
