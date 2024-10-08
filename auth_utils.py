import jwt
import datetime
from flask import request, jsonify
from functools import wraps
import os

SECRET_KEY = os.getenv('SECRET_KEY')


def generate_token(user_id):
    payload = {
        'exp': datetime.datetime.now() + datetime.timedelta(hours=1),  # Token expiration time
        'iat': datetime.datetime.now(),  # Issued at time
        'sub': user_id  # Subject of the token (user ID)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing.'}), 401
    
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token is expired.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401
        
        # Passing the user's id to the decorator function
        return f(current_user_id, *args, **kwargs)
    
    return decorated
    
    