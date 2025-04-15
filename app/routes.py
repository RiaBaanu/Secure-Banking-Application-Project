from flask import render_template, request, redirect, url_for, flash, Blueprint, jsonify, session
import pyotp
from app.models import User, Account, Transaction
from app import db, limiter
from datetime import datetime, date
import re
import qrcode
import io
import base64
DAILY_WITHDRAWAL_LIMIT = 1500.00  # You can adjust this

main = Blueprint('main', __name__)

@main.route('/')
def home():
    session.clear()
    return render_template('home.html')

@main.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if 'user_id' not in session:
        flash("You must be logged in to set up 2FA.", "danger")
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        otp = request.form.get('otp')

        if not otp:
            flash("OTP is required.", "danger")
            return redirect(url_for('main.setup_2fa'))

        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp):
            user.is_2fa_enabled = True
            db.session.commit()
            flash("Two-Factor Authentication is now active.", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('main.setup_2fa'))

    # GET method: render QR code
    uri = pyotp.TOTP(user.otp_secret).provisioning_uri(name=user.email, issuer_name="Secure Banking App")
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_data = base64.b64encode(buffer.getvalue()).decode()
    qr_code_data = f"data:image/png;base64,{qr_data}"

    return render_template('setup_2fa.html', qr_code_data=qr_code_data, otp_uri=uri)


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.register'))

        # ✅ Password Strength Check
        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password):
            flash("Password must include at least 8 characters, one number, and one uppercase letter.", "danger")
            return redirect(url_for('main.register'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "warning")
            return redirect(url_for('main.register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for('main.register'))

        # ✅ Create user & account
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        account = Account(user_id=new_user.id, balance=0.0)
        db.session.add(account)
        db.session.commit()

        session['user_id'] = new_user.id
        flash("Please set up 2FA by scanning the QR code.", "info")
        return redirect(url_for('main.setup_2fa'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Both fields are required.', 'danger')
            return redirect(url_for('main.login'))

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.is_2fa_enabled:
                # 2FA already set up
                session['pending_user_id'] = user.id
                flash("Enter the OTP from your authenticator app.", "info")
                return redirect(url_for('main.verify_otp'))
            else:
                # 2FA not yet set up
                session.permanent =  True
                session['user_id'] = user.id
                flash("Please set up 2FA before accessing your account.", "warning")
                return redirect(url_for('main.setup_2fa'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('main.login'))

    return render_template('login.html')


@main.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])
    now = datetime.now()

    this_month_withdrawals = sum(
        t.amount for t in user.transactions
        if t.type == 'withdraw' and t.timestamp.month == now.month and t.timestamp.year == now.year
    )

    this_month_deposits = sum(
        t.amount for t in user.transactions
        if t.type == 'deposit' and t.timestamp.month == now.month and t.timestamp.year == now.year
    )

    return render_template('dashboard.html', user=user,
                           monthly_withdrawals=this_month_withdrawals,
                           monthly_deposits=this_month_deposits)


@main.route('/balance', methods=['POST'])
def balance():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    if user and user.account:
        return jsonify({'balance': user.account.balance}), 200
    return jsonify({'error': 'User not found'}), 404


@main.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
            if amount > 0:
                user.account.balance += amount
                db.session.commit()

                # Log transaction
                transaction = Transaction(type='deposit', amount=amount, user_id=user.id)
                db.session.add(transaction)
                db.session.commit()

                flash(f"Deposited €{amount}", "success")
                return redirect(url_for('main.dashboard'))
        except:
            flash("Invalid amount.", "danger")

    return render_template('deposit.html')


@main.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))

            if amount <= 0:
                flash("Amount must be greater than zero.", "warning")
                return redirect(url_for('main.withdraw'))

            # ✅ Calculate today's total withdrawals
            today = date.today()
            total_withdrawn_today = sum(
                t.amount for t in user.transactions
                if t.type == 'withdraw' and t.timestamp.date() == today
            )

            if total_withdrawn_today + amount > DAILY_WITHDRAWAL_LIMIT:
                remaining = DAILY_WITHDRAWAL_LIMIT - total_withdrawn_today
                flash(f"Withdrawal denied. Daily limit €{DAILY_WITHDRAWAL_LIMIT} exceeded. You can still withdraw €{remaining:.2f} today.", "danger")
                return redirect(url_for('main.withdraw'))

            if user.account.balance >= amount:
                user.account.balance -= amount
                db.session.commit()

                transaction = Transaction(type='withdraw', amount=amount, user_id=user.id)
                db.session.add(transaction)
                db.session.commit()

                flash(f"Withdrew €{amount}. Remaining daily limit: €{DAILY_WITHDRAWAL_LIMIT - (total_withdrawn_today + amount):.2f}", "success")
                return redirect(url_for('main.dashboard'))
            else:
                flash("Insufficient funds.", "warning")
        except:
            flash("Invalid input. Please enter a valid number.", "danger")

    return render_template('withdraw.html')

@main.route('/verify-otp', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('main.login'))

    user = User.query.get(user_id)

    if request.method == 'POST':
        otp_input = request.form.get('otp')
        totp = user.get_otp()
        if totp.verify(otp_input):
            # ✅ OTP verified — now finalize login
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session.pop('pending_user_id', None)
            flash("Login successful!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid OTP. Try again.", "danger")

    return render_template('verify_otp.html')

@main.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.app_errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@main.app_errorhandler(429)
def rate_limit_exceeded(e):
    return render_template("429.html"), 429

