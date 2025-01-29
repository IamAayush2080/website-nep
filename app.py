from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import os
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
UPLOAD_FOLDER = 'static/uploads'

# Automatically create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


app = Flask(__name__)
app.secret_key = 'your_secret_key'




app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db = SQLAlchemy(app)

# Configure Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'
mail = Mail(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    wallet_number = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(50), nullable=False)
    slip = db.Column(db.String(200), nullable=True)  # Filepath for proof
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected



import sqlite3

def save_to_database(deposit_data):
    # Connect to the database (or create one if it doesn't exist)
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            wallet_number TEXT,
            sender_name TEXT,
            transaction_id TEXT,
            proof_path TEXT,
            user_id INTEGER,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Insert the deposit data into the table
    cursor.execute('''
        INSERT INTO deposit_requests (amount, wallet_number, sender_name, transaction_id, proof_path, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        deposit_data['amount'],
        deposit_data['wallet_number'],
        deposit_data['sender_name'],
        deposit_data['transaction_id'],
        deposit_data['proof_path'],
        deposit_data['user_id']
    ))

    # Commit the transaction and close the connection
    connection.commit()
    connection.close()



# Database setup
def init_db():
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        balance REAL DEFAULT 0.0
                    )''')
    conn.commit()
    conn.close()

init_db()

# Hash password before storing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Register user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        hashed_password = hash_password(password)

        # Check if user already exists
        conn = sqlite3.connect('wallet.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if user:
            flash("User with this email already exists", "warning")
            return redirect(url_for('register'))

        # Insert user into database
        is_admin = True  # Set this to True for the admin user, False for regular users
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                       (username, email, hashed_password))
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hash_password(password)

        conn = sqlite3.connect('wallet.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, hashed_password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[4]  # Store the is_admin flag in session

            flash("Login successful!", "success")
            # Redirect to admin page if the user is an admin
            if user[4]:  # Check if the user is an admin
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('wallet.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()

    return render_template('dashboard.html', username=session['username'], balance=balance)

#transaction
@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash("Please log in to view transactions.", "warning")
        return redirect(url_for('login'))

    # Add logic to fetch and display transactions here
    return render_template('transactions.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        user_id = session.get('user_id')  # Assuming the user is logged in
        amount = request.form['amount']
        wallet_number = request.form['wallet_number']
        transaction_id = request.form['transaction_id']
        slip = request.files['slip']
        
        # Save slip file
        slip_path = f'static/uploads/{slip.filename}'
        slip.save(slip_path)
        
        # Create deposit entry
        deposit = Deposit(user_id=user_id, amount=amount, wallet_number=wallet_number,
                          transaction_id=transaction_id, slip=slip_path)
        db.session.add(deposit)
        db.session.commit()
        
        # Send email to admin
        msg = Message('New Deposit Request', sender=app.config['Aayush Kumar Kurmi'], recipients=['ak2183874@gmail.com'])
        msg.body = f"""
        Deposit Request:
        User ID: {user_id}
        Amount: {amount}
        Wallet Number: {wallet_number}
        Transaction ID: {transaction_id}
        """
        mail.send(msg)
        
        flash("Deposit request submitted successfully!", "success")
        return redirect(url_for('dashboard'))
    return render_template('deposit.html')
 
@app.route('/process-deposit', methods=['POST'])
def process_deposit():
    # Extract form data
    amount = request.form['amount']
    wallet_number = request.form['wallet_number']
    sender_name = request.form['sender_name']
    transaction_id = request.form['transaction_id']
    payment_proof = request.files['payment_proof']

    # Save proof screenshot to a folder
    proof_path = f"static/uploads/{payment_proof.filename}"
    payment_proof.save(proof_path)

    # Save deposit details to the database
    new_request = {
        "amount": amount,
        "wallet_number": wallet_number,
        "sender_name": sender_name,
        "transaction_id": transaction_id,
        "proof_path": proof_path,
        "user_id": session.get('user_id')  # Example: Store the logged-in user's ID
    }
    save_to_database(new_request)

    # Redirect user to their dashboard
    return redirect('/dashboard')


# Withdraw
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        flash("Please log in to withdraw funds.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        user_id = session['user_id']

        conn = sqlite3.connect('wallet.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
        balance = cursor.fetchone()[0]

        if amount <= balance:
            cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
            conn.commit()
            flash('Withdrawal successful!', 'success')
        else:
            flash('Insufficient balance.', 'danger')

        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('withdraw.html')


# Logout user
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


#admin 
# admin route updated to manage deposits and virtual coins
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Check if the user is logged in and is an admin
    if 'user_id' not in session or not session.get('is_admin'):
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('login'))

    deposits = Deposit.query.all()  # Fetch all deposits
    users = User.query.all()  # Fetch all users for the admin to view

    if request.method == 'POST':
        # Handling deposit approval/rejection
        deposit_id = request.form.get('deposit_id')
        action = request.form.get('action')  # Approve or Reject
        deposit = Deposit.query.get(deposit_id)

        if deposit and action:
            if action == 'Approve':
                deposit.status = 'Approved'
            elif action == 'Reject':
                deposit.status = 'Rejected'
            db.session.commit()
            flash("Deposit status updated.", "success")

        # Handling virtual coin addition (admin can send coins to a user)
        elif 'add_coin' in request.form:
            user_id = request.form['user_id']
            coin_amount = request.form.get('coin_amount')

            if coin_amount and float(coin_amount) > 0:
                coin_amount = float(coin_amount)
                user = User.query.get(user_id)

                if user:
                    user.balance += coin_amount  # Add virtual coins to user's balance
                    db.session.commit()
                    flash(f"{coin_amount} virtual coins added to {user.username}'s account.", "success")
                else:
                    flash("User not found.", "danger")
            else:
                flash("Please provide a valid coin amount.", "danger")

        return redirect(url_for('admin'))

    return render_template('admin.html', deposits=deposits, users=users)




if __name__ == '__main__':
    app.run(debug=True)
