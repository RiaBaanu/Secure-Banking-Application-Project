import unittest
from app import create_app, db
from app.models import User

class SecureBankTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()     # ✅ Add this line to wipe the DB before each test
            db.create_all()


    def test_register_user(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Secure123'
        }, follow_redirects=True)
        self.assertIn(b'Set Up Two-Factor Authentication', response.data)

    def test_login_valid(self):
        with self.app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('Secure123')
            db.session.add(user)
            db.session.commit()

        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'Secure123'
        }, follow_redirects=True)
        self.assertIn(b'Set Up Two-Factor Authentication', response.data)

    def test_login_invalid(self):
        response = self.client.post('/login', data={
            'email': 'fake@example.com',
            'password': 'wrongpass'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

if __name__ == '__main__':
    unittest.main()
