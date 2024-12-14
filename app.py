from flask import Flask, request, jsonify
import sqlite3
import smtplib
import random

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE,
                        phone TEXT UNIQUE,
                        password TEXT NOT NULL,
                        referral_code TEXT,
                        balance REAL DEFAULT 0.0,
                        is_admin INTEGER DEFAULT 0
                    )''')
    conn.commit()
    conn.close()

init_db()

# Helper function to get user data
def get_user_by_email_or_phone(identifier):
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? OR phone = ?', (identifier, identifier))
    user = cursor.fetchone()
    conn.close()
    return user

# Generate a random OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Send OTP via email
def send_email_otp(email, otp):
    try:
        sender_email = "your_email@example.com"
        sender_password = "your_email_password"

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            message = f"Subject: Your OTP\n\nYour OTP is: {otp}"
            server.sendmail(sender_email, email, message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    referral_code = data.get('referral_code')

    if not (email or phone) or not password or not confirm_password:
        return jsonify({"error": "Email/Phone, Password, and Confirm Password are required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if email and get_user_by_email_or_phone(email):
        return jsonify({"error": "User with this email already exists"}), 400

    if phone and get_user_by_email_or_phone(phone):
        return jsonify({"error": "User with this phone number already exists"}), 400

    otp = generate_otp()
    if email and not send_email_otp(email, otp):
        return jsonify({"error": "Failed to send OTP to email"}), 500

    # Store the user in the database
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (email, phone, password, referral_code) VALUES (?, ?, ?, ?)',
                   (email, phone, password, referral_code))
    conn.commit()
    conn.close()

    return jsonify({"message": "User registered successfully. Verify OTP sent to email."}), 201

# Login existing user
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('email_or_phone')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"error": "Email/Phone and Password are required"}), 400

    user = get_user_by_email_or_phone(identifier)

    if not user or user[3] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "username": user[1], "is_admin": user[7]}), 200

# Admin route to view all users
@app.route('/admin/users', methods=['GET'])
def view_users():
    auth_email = request.headers.get('Admin-Email')
    auth_password = request.headers.get('Admin-Password')

    # Authenticate admin
    admin = get_user_by_email_or_phone(auth_email)
    if not admin or admin[3] != auth_password or admin[7] != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    # Fetch all users
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, phone, balance FROM users WHERE is_admin = 0')
    users = cursor.fetchall()
    conn.close()

    return jsonify({"users": users}), 200

# Admin route to manage user balance
@app.route('/admin/manage_user', methods=['POST'])
def manage_user():
    auth_email = request.headers.get('Admin-Email')
    auth_password = request.headers.get('Admin-Password')

    # Authenticate admin
    admin = get_user_by_email_or_phone(auth_email)
    if not admin or admin[3] != auth_password or admin[7] != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    action = data.get('action')
    amount = data.get('amount', 0)

    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()

    if action == "delete":
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    elif action == "update_balance":
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    else:
        return jsonify({"error": "Invalid action"}), 400

    conn.commit()
    conn.close()

    return jsonify({"message": "Action completed successfully"}), 200

# Create an admin account manually (uncomment and run once to create)
conn = sqlite3.connect('wallet.db')
cursor = conn.cursor()
cursor.execute('INSERT INTO users (username, email,  password, is_admin) VALUES (?, ?, ?, ?)',
               ('admin', 'ak2183874@gmail.com', 'Avengers12345@@##$$', 1))
conn.commit()
conn.close()

if __name__ == '__main__':
    app.run(debug=True)
