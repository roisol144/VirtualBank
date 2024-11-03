import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from bank_accounts import bank_accounts_bp
from exceptions import UserNotFoundError
from users import users_bp
import json
from datetime import datetime
from dotenv import load_dotenv
from faker import Faker

load_dotenv()

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(bank_accounts_bp)
        self.app.register_blueprint(users_bp)
        self.client = self.app.test_client()
        self.fake = Faker()

    # Bank Account Tests

    @patch('bank_accounts.get_db_connection')
    def test_get_bank_accounts(self, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_cursor.fetchall.return_value = [
            {
                'id': self.fake.uuid4(),
                'user_id': self.fake.uuid4(),
                'account_number': self.fake.bban(),
                'balance': self.fake.random_int(min=100, max=10000),
                'type': self.fake.random_element(elements=('CHECKINGS', 'SAVINGS')),
                'currency': 'USD',
                'created_at': self.fake.date_this_decade().isoformat(),
                'status': 'ACTIVE'
            }
        ]

        response = self.client.get(f'/bank_accounts?user_id={mock_cursor.fetchall()[0]["user_id"]}')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], mock_cursor.fetchall()[0]['id'])
        self.assertEqual(data[0]['user_id'], mock_cursor.fetchall()[0]['user_id'])

    @patch('bank_accounts.get_db_connection')
    @patch('bank_accounts.check_is_valid_user_id')
    @patch('bank_accounts.uuid4')
    @patch('bank_accounts.encrypt_account_number')
    def test_create_bank_account(self, mock_encrypt, mock_uuid4, mock_check_user, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_check_user.return_value = self.fake.uuid4()
        mock_uuid4.return_value = self.fake.uuid4()
        mock_encrypt.return_value = b'encrypted_account_number'

        response = self.client.post('/bank_accounts', 
                                    data=json.dumps({
                                        'user_id': mock_check_user.return_value,
                                        'currency': 'USD',
                                        'account_type': self.fake.random_element(elements=('CHECKINGS', 'SAVINGS'))
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['account_id'], mock_uuid4.return_value)
        self.assertEqual(data['account_number'], 'encrypted_account_number')

    # User Tests

    @patch('users.get_db_connection')
    @patch('users.bcrypt.generate_password_hash')
    @patch('users.uuid4')
    def test_register_user(self, mock_uuid4, mock_hash, mock_get_db_connection):
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_get_db_connection.return_value = (mock_cursor, mock_conn)

        mock_uuid4.return_value = self.fake.uuid4()
        mock_hash.return_value = b'hashed_password'

        # Store generated values
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        email = self.fake.email()
        password = self.fake.password()

        response = self.client.post('/users/register', 
                                    data=json.dumps({
                                        'first_name': first_name,
                                        'last_name': last_name,
                                        'email': email,
                                        'password': password
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['id'], mock_uuid4.return_value)
        self.assertEqual(data['first_name'], first_name)  # Use stored first name
        self.assertEqual(data['last_name'], last_name)    # Use stored last name
        self.assertEqual(data['email'], email)            # Use stored email

    @patch('users.get_user_by_email')
    def test_get_user(self, mock_get_user):
        mock_get_user.return_value = {
            'id': self.fake.uuid4(),
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'email': self.fake.email()
        }

        response = self.client.get(f'/users?email={mock_get_user.return_value["email"]}')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], mock_get_user.return_value['id'])
        self.assertEqual(data['first_name'], mock_get_user.return_value['first_name'])
        self.assertEqual(data['last_name'], mock_get_user.return_value['last_name'])
        self.assertEqual(data['email'], mock_get_user.return_value['email'])

    @patch('users.get_user_by_email')
    @patch('users.bcrypt.check_password_hash')
    @patch('users.generate_token')
    def test_login_user(self, mock_generate_token, mock_check_password, mock_get_user):
        mock_get_user.return_value = {
            'id': self.fake.uuid4(),
            'email': self.fake.email(),
            'password_hash': 'hashed_password'
        }
        mock_check_password.return_value = True
        mock_generate_token.return_value = 'fake_token'

        response = self.client.post('/users/login',
                                    data=json.dumps({
                                        'email': mock_get_user.return_value['email'],
                                        'password': 'password123'
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Logged In Successfully')
        self.assertEqual(data['token'], 'fake_token')

    def test_register_user_missing_field(self):
        response = self.client.post('/users/register', 
                                    data=json.dumps({
                                        'first_name': self.fake.first_name(),
                                        'last_name': self.fake.last_name(),
                                        'email': self.fake.email()
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
                                        'email': self.fake.email(),
                                        'password': 'wrongpassword'
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid email or password.')

    @patch('users.get_user_by_email')
    def test_get_user_not_found(self, mock_get_user):
        # Provide the required argument for UserNotFoundError
        mock_get_user.side_effect = UserNotFoundError(email=self.fake.email())

        response = self.client.get(f'/users?email={mock_get_user.side_effect.email}')

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'User Not Found')

if __name__ == '__main__':
    unittest.main()
