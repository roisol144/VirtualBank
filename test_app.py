import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from bank_accounts import bank_accounts_bp
from exceptions import UserNotFoundError
from users import users_bp
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(bank_accounts_bp)
        self.app.register_blueprint(users_bp)
        self.client = self.app.test_client()

    # Bank Account Tests

    @patch('bank_accounts.get_db_connection')
    def test_get_bank_accounts(self, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_cursor.fetchall.return_value = [
            {
                'id': '123',
                'user_id': '456',
                'account_number': '789',
                'balance': 1000,
                'type': 'CHECKINGS',
                'currency': 'USD',
                'created_at': '2023-01-01',
                'status': 'ACTIVE'
            }
        ]

        response = self.client.get('/bank_accounts?user_id=456')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], '123')
        self.assertEqual(data[0]['user_id'], '456')

    @patch('bank_accounts.get_db_connection')
    @patch('bank_accounts.check_is_valid_user_id')
    @patch('bank_accounts.uuid4')
    @patch('bank_accounts.encrypt_account_number')
    def test_create_bank_account(self, mock_encrypt, mock_uuid4, mock_check_user, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_check_user.return_value = '456'
        mock_uuid4.return_value.int = 123456
        mock_uuid4.return_value = '123'
        mock_encrypt.return_value = b'encrypted_account_number'

        response = self.client.post('/bank_accounts', 
                                    data=json.dumps({'user_id': '456'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['account_id'], '123')
        self.assertEqual(data['account_number'], 'encrypted_account_number')

    # User Tests

    @patch('users.get_db_connection')
    @patch('users.bcrypt.generate_password_hash')
    @patch('users.uuid4')
    def test_register_user(self, mock_uuid4, mock_hash, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_uuid4.return_value = '123'
        mock_hash.return_value = b'hashed_password'

        response = self.client.post('/users/register', 
                                    data=json.dumps({
                                        'first_name': 'John',
                                        'last_name': 'Doe',
                                        'email': 'john@example.com',
                                        'password': 'password123'
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['id'], '123')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['email'], 'john@example.com')

    @patch('users.get_user_by_email')
    def test_get_user(self, mock_get_user):
        mock_get_user.return_value = {
            'id': '123',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        }

        response = self.client.get('/users?email=john@example.com')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], '123')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['email'], 'john@example.com')

    @patch('users.get_user_by_email')
    @patch('users.bcrypt.check_password_hash')
    @patch('users.generate_token')
    def test_login_user(self, mock_generate_token, mock_check_password, mock_get_user):
        mock_get_user.return_value = {
            'id': '123',
            'email': 'john@example.com',
            'password_hash': 'hashed_password'
        }
        mock_check_password.return_value = True
        mock_generate_token.return_value = 'fake_token'

        response = self.client.post('/users/login',
                                    data=json.dumps({
                                        'email': 'john@example.com',
                                        'password': 'password123'
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Logged In Successfully')
        self.assertEqual(data['toekn'], 'fake_token')  # Note: There's a typo in your original code ('toekn' instead of 'token')

    def test_register_user_missing_field(self):
        response = self.client.post('/users/register', 
                                    data=json.dumps({
                                        'first_name': 'John',
                                        'last_name': 'Doe',
                                        'email': 'john@example.com'
                                        # Missing password field
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("'password' is missing", data['Error occured'])

    @patch('users.get_user_by_email')
    def test_login_user_invalid_credentials(self, mock_get_user):
        mock_get_user.return_value = None

        response = self.client.post('/users/login',
                                    data=json.dumps({
                                        'email': 'nonexistent@example.com',
                                        'password': 'wrongpassword'
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid email or password.')

    @patch('users.get_user_by_email')
    def test_get_user_not_found(self, mock_get_user):
        # Provide the required argument for UserNotFoundError
        mock_get_user.side_effect = UserNotFoundError(email='nonexistent@example.com')

        response = self.client.get('/users?email=nonexistent@example.com')

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'User Not Found')

if __name__ == '__main__':
    unittest.main()
