from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import requests
import os

#region App Setup
app = Flask(__name__)
app.config['DEBUG'] = True
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(20)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./backend/Arkham.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

FASTAPI_URL = "http://127.0.0.1:8000"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print("Form submitted with:", username, password)

        
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
    username = session.get('username','Guest')
    user_id=session.get("user_id",1)

    try:
        user_response = requests.get(f"{FASTAPI_URL}/users/username/{username}")
        user_data = user_response.json() if user_response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        return f"Error getting user info: {str(e)}"

    # Safely set the profilePic
    profile_pic = user_data['profilePic'] if user_data and 'profilePic' in user_data else "default.png"

    response_received = requests.get(f"{FASTAPI_URL}/messages/received/{user_id}")
    received_messages = response_received.json() if response_received.status_code == 200 else []

    response_recent = requests.get(f"{FASTAPI_URL}/messages/recent/{user_id}")
    recent_messages = response_recent.json() if response_recent.status_code == 200 else []

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



if __name__ == "__main__":
    app.run(debug=True)