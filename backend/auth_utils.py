import jwt
import datetime
from flask import request, jsonify
from functools import wraps
import logging
import os
import hashlib
from dotenv import load_dotenv
from cryptography.fernet import Fernet
load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY')
# Keys
fernet_key = os.environ.get('FERNET_KEY')

# Check if fernet_key is None and raise an error if it is
if fernet_key is None:
    raise ValueError("FERNET_KEY not found in environment variables.")

fernet = Fernet(fernet_key.encode())
TOKEN_EXPIRATION_HOURS = int(os.environ.get('TOKEN_EXPIRATION_HOURS'))

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.now() + datetime.timedelta(hours = TOKEN_EXPIRATION_HOURS),  # Token expiration time
        'iat': datetime.datetime.now(),  # Issued at time
        'sub': user_id  # Subject of the token (user ID)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        logging.debug(f"Authentication token valid for user {payload['sub']}")
        return payload['sub']
    except jwt.ExpiredSignatureError:
        logging.debug("Token Expired.")
        return None
    except jwt.InvalidTokenError:
        logging.debug("Invalid token was supplied.")
        return None
    
    
def encrypt_account_number(account_number):
    encrypted_account_number = fernet.encrypt(account_number.encode())
    return encrypted_account_number

def hash_account_number(account_number):
    salt = os.getenv('SALT')
    if salt is None:
        raise ValueError("SALT not found in environment variables.")
    
    if not isinstance(account_number, str):
        raise ValueError("Account number must be a string.")
    
    hashed_account_number = hashlib.sha256((account_number + salt).encode()).hexdigest()
    return hashed_account_number
      
    
    