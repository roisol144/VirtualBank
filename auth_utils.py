import jwt
import datetime
from flask import request, jsonify
from functools import wraps
import logging
import os
from cryptography.fernet import Fernet

SECRET_KEY = os.environ.get('SECRET_KEY')
# Keys
ferney_key = os.environ.get("FERNET_KEY")
fernet = Fernet(ferney_key.encode())

# logging config
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])

def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.now() + datetime.timedelta(hours=1),  # Token expiration time
        'iat': datetime.datetime.now(),  # Issued at time
        'sub': user_id  # Subject of the token (user ID)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    logging.debug(f"Generated token for user{user_id}: {token}")
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        logging.debug(f"Token verified. Payload{payload}")
        logging.debug(f"for user{payload['sub']}")
        return payload['sub']
    except jwt.ExpiredSignatureError:
        logging.debug("Token Expired.")
        return None
    except jwt.InvalidTokenError:
        logging.debug("Invalid token.")
        return None
    
    
def encrypt_account_number(account_number):
    encrypted_account_number = fernet.encrypt(account_number.encode())
    return encrypted_account_number
      
    
    