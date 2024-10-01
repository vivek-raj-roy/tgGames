from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import random
import string
from datetime import datetime, timedelta
from telegram import Bot

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Setup
client = MongoClient('mongodb+srv://vivekrajroy705:o6X6gvdM84G0nG3x@cluster0.djx5h.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['site_userdb']
users_collection = db['Siteusers']
codes_collection = db['verification_codes']

# Telegram Bot Setup (python-telegram-bot)
BOT_TOKEN = '6658351224:AAHdlDUfEOmK4DHzoB_Pj2oUgZVEDUO9zLI'  # Replace with your bot token
bot = Bot(token=BOT_TOKEN)

# Generate random verification code
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Send verification code using Telegram bot
def send_verification_code(username, telegram_id, code):
    message = f"Hello {username},\nYour verification code is: {code}. This code will expire in 2 minutes."
    bot.send_message(chat_id=telegram_id, text=message)

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
        telegram_id = user['telegram_id']  # The Telegram ID must be stored when registering the user
        code = generate_code()
        expiry_time = datetime.now() + timedelta(minutes=2)
        
        # Store verification code with expiry time
        codes_collection.update_one(
            {'username': username},
            {'$set': {'code': code, 'expiry_time': expiry_time}},
            upsert=True
        )
        
        # Send verification code via Telegram bot
        send_verification_code(username, telegram_id, code)
        
        flash(f'A verification code has been sent to your Telegram account.', 'info')
    else:
        flash('Username not found.', 'danger')
    
    return redirect(url_for('reset_password'))

if __name__ == "__main__":
    app.run(debug=True)
