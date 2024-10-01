from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'sidopkey'

# MongoDB Setup
client = MongoClient('mongodb://localhost:27017/')
db = client['user_db']
users_collection = db['users']
codes_collection = db['verification_codes']

# Generate random verification code
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username})
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

# Route for password reset page
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        code = request.form['code']
        new_password = request.form['new_password']
        
        stored_code = codes_collection.find_one({'username': username})
        
        if stored_code:
            # Check if the code is expired (valid for 2 minutes)
            if datetime.now() > stored_code['expiry_time']:
                flash('The verification code has expired. Please request a new one.', 'danger')
            elif stored_code['code'] == code:
                users_collection.update_one({'username': username}, {'$set': {'password': new_password}})
                flash('Password successfully reset!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Invalid verification code. Please try again.', 'danger')
        else:
            flash('Invalid username or code. Please try again.', 'danger')
        
    return render_template('reset_password.html')

# Simulate dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return f"Welcome {session['username']} to your dashboard!"
    return redirect(url_for('login'))

# Forget password (send code)
@app.route('/send_code', methods=['POST'])
def send_code():
    username = request.form['username']
    user = users_collection.find_one({'username': username})
    
    if user:
        code = generate_code()
        expiry_time = datetime.now() + timedelta(minutes=2)
        
        # Store verification code with expiry time
        codes_collection.update_one(
            {'username': username},
            {'$set': {'code': code, 'expiry_time': expiry_time}},
            upsert=True
        )
        
        # Send code to user (you can integrate this with a Telegram bot or email service)
        flash(f'Your verification code has been sent to {username}.', 'info')
    else:
        flash('Username not found.', 'danger')
    
    return redirect(url_for('reset_password'))

if __name__ == "__main__":
    app.run(debug=True)
