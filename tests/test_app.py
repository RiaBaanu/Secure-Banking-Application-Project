import unittest
from app import create_app, db
from app.models import User

class SecureBankTestCase(unittest.TestCase):
    def setUp(self):
        # Setup a test version of the Flask app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # In-memory DB for testing
        self.client = self.app.test_client()

        # Initialize the database
        with self.app.app_context():
            db.drop_all()     # Reset DB before each test
            db.create_all()

    def test_register_user(self):
        # Test user registration endpoint
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Secure123'
        }, follow_redirects=True)
        # Expect redirection to 2FA setup page
        self.assertIn(b'Set Up Two-Factor Authentication', response.data)

    def test_login_valid(self):
        # Pre-create a user in the test DB
        with self.app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Secure123')
            db.session.add(user)
            db.session.commit()

        # Test valid login
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'Secure123'
        }, follow_redirects=True)
        self.assertIn(b'Set Up Two-Factor Authentication', response.data)

    def test_login_invalid(self):
        # Test login with invalid credentials
        response = self.client.post('/login', data={
            'email': 'fake@example.com',
            'password': 'wrongpass'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)


# Run tests when executed directly
if __name__ == '__main__':
    unittest.main()
