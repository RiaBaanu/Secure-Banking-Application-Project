from app import db, bcrypt
from datetime import datetime
import pyotp

# User model: handles authentication, password, OTP
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-one relationship: each user has one account
    account = db.relationship('Account', backref='owner', uselist=False)

    # One-to-many: user can have multiple transactions
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    # Secret for OTP generation
    otp_secret = db.Column(db.String(16), default=pyotp.random_base32)

    # Hash password using bcrypt
    def set_password(self, raw_password):
        self.password = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    # Check hashed password against input
    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password, raw_password)
    
    # Return OTP object to validate or get URI
    def get_otp(self):
        return pyotp.TOTP(self.otp_secret)

# Account model: stores user balance
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Transaction model: logs deposit/withdrawal with timestamp
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20))  # "deposit" or "withdraw"
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
