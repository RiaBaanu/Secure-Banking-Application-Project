# Secure Banking Application Project

CA3 – Secure Code Project  
Atlantic Technological University  
Module: Secure Programming  
Author: Suriabaanu Rokanatnam

---

# Overview

The Secure Banking Application is a Flask-based web application that simulates a basic online banking system. It prioritizes **security, user authentication**, and **code quality**, implementing best practices for secure programming and static code analysis.

Users can:
- Register and log in securely
- Set up Two-Factor Authentication (2FA) using Google Authenticator
- View account balances
- Deposit or withdraw funds
- View transaction history with simple expense tracking

---

# Technologies Used

- **Backend**: Python, Flask, Flask-SQLAlchemy
- **Authentication**: Flask-Bcrypt, pyotp (TOTP for 2FA)
- **Security**: Flask-Limiter (rate limiting), session timeout, input validation
- **Frontend**: HTML, Bootstrap 5 (dark theme, responsive layout)
- **Testing**: Python `unittest`
- **Static Analysis**: Bandit
- **Database**: SQLite

---

# Key Security Features

- Passwords hashed with **bcrypt** and salted
- **2FA** via QR code (Google Authenticator compatible)
- Rate-limiting on login and OTP endpoints
- Session timeout after inactivity
- Password strength validation on registration
- Custom error pages for 403, 404, 429

---

# How to Run Tests

```bash
python -m unittest discover tests
```

Includes 3 unit tests:
- Register new user
- Login with valid credentials
- Login with invalid credentials

---

# Bandit Static Code Analysis

To run Bandit and check for vulnerabilities:

```bash
bandit -r app/ -f txt -o bandit_report.txt
```

The application passed with **0 high-severity issues** after code refinements.

---

# How to Run the App

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Secure-Banking-Application-Project.git
cd Secure-Banking-Application-Project
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python run.py
```

Then go to: `http://127.0.0.1:5000`

---

# Project Outcomes

- ✅ Secure user authentication (with 2FA)
- ✅ Proper exception handling and input validation
- ✅ Static analysis to detect vulnerabilities
- ✅ Clear session and access control logic
- ✅ Unit tests for validation
- ✅ Clean and modern user interface


