
class UserNotFoundError(Exception):
    def __init__(self, email):
        super().__init__(f"User with email '{email}' not found.")
        self.email = email

class DatabaseConnectionError(Exception):
    def __init__(self):
        super().__init__("Failed to connect to the database.")
        
class TokenVerificationError(Exception):
    def __init__(self):
        super().__init__("Token verification failed.")

