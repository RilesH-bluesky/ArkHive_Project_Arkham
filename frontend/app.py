import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from utils import load_key, decrypt_message
import requests


#region App Setup
app = Flask(__name__)
app.config['DEBUG'] = True
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(20)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./backend/Arkham.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

FASTAPI_URL = "http://127.0.0.1:8000"

@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        recaptcha_response = request.form.get('g-recaptcha-response')
        print("Form submitted with:", username, password)
        # Verify reCAPTCHA
        recaptcha_verify = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': '6Lek7CkrAAAAAEz8IVaVJE0cCcmjM623Q9HAySqG',
                'response': recaptcha_response
            }
        )
        recaptcha_result = recaptcha_verify.json()
        if not recaptcha_result.get('success'):
            return render_template("login.html", error="reCAPTCHA verification failed.")

        
        try:
            response = requests.post(f"{FASTAPI_URL}/login", json={
                "username": username,
                "password": password
            })
            result = response.json()
        except requests.exceptions.RequestException as e:
            return render_template("login.html", error="API connection error.")

        if result.get("success"):
            session['username'] = result.get("username")
            session['user_id'] = result.get("user_id")
            return redirect(url_for('home')) 
        else:
            return render_template("login.html", error=result.get("message", "Login failed."))
    
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username', 'Guest')
    user_id = session.get("user_id", 1)

    # Get user profile info
    try:
        user_response = requests.get(f"{FASTAPI_URL}/users/username/{username}")
        user_data = user_response.json() if user_response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return f"Error getting user info: {str(e)}"

    profile_pic = user_data['profilePic'] if user_data and 'profilePic' in user_data else "default.png"

    # Get and decrypt received messages
    response_received = requests.get(f"{FASTAPI_URL}/messages/received/{user_id}")
    received_messages = response_received.json() if response_received.status_code == 200 else []

    key = load_key()
    for msg in received_messages:
        msg['content'] = decrypt_message(msg['content'], key)

        # Fetch and attach sender's username
        sender_id = msg['userIdSender']
        try:
            sender_response = requests.get(f"{FASTAPI_URL}/users/{sender_id}")
            sender = sender_response.json()
            msg['sender_username'] = sender['username'] if sender else f"ID {sender_id}"
        except:
            msg['sender_username'] = f"ID {sender_id}"

    # Reverse inbox order
    received_messages.reverse()

    # Recent messages and user list
    response_recent = requests.get(f"{FASTAPI_URL}/messages/recent/{user_id}")
    recent_messages = response_recent.json() if response_recent.status_code == 200 else []

    for msg in recent_messages:
        msg['content'] = decrypt_message(msg['content'], key)

        # Figure out the other user
        other_id = msg['userIdReceiver'] if msg['userIdSender'] == user_id else msg['userIdSender']
        try:
            other_user_response = requests.get(f"{FASTAPI_URL}/users/{other_id}")
            other_user = other_user_response.json()
            msg['other_username'] = other_user['username'] if other_user else f"ID {other_id}"
            msg['other_userId'] = other_id
        except:
            msg['other_username'] = f"ID {other_id}"
            msg['other_userId'] = other_id

    response_users = requests.get(f"{FASTAPI_URL}/users/")
    users = response_users.json() if response_users.status_code == 200 else []

    return render_template(
        'home.html',
        username=username,
        user_profile_pic=profile_pic,
        received_messages=received_messages,
        recent_messages=recent_messages,
        users=users
    )



# @app.route('/register')
# def register():

#@app.route('/message')
#def messages():
#    return render_template('messages.html')

@app.route('/conversation/<int:other_user_id>')
def conversation(other_user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user_id = session.get('user_id', 1)  # fallback to 1 if not logged in

    try:
        user_response = requests.get(f"{FASTAPI_URL}/users/{other_user_id}")
        other_user = user_response.json() if user_response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return f"Error getting user: {str(e)}"

    if other_user is None:
        return "User not found.", 404

    return render_template(
        'conversation.html',
        other_user_id=other_user_id,
        other_user_name=other_user['username'],
        current_user_id=current_user_id
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)