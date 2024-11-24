from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from pymongo import MongoClient

# Initialize Blueprint for Authentication
auth = Blueprint('auth', __name__)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.user_db
users_collection = db.users

# User Class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.password = user_data["password"]

    @staticmethod
    def get(user_id):
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None

# User Registration Route
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        confirm_email = request.form['confirm_email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form['phone']
        alt_phone = request.form.get('alt_phone', None)

        if email != confirm_email:
            flash('Emails do not match. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        existing_user = users_collection.find_one({'username': username})
        if existing_user is None:
            hashed_password = generate_password_hash(password)
            users_collection.insert_one({
                'full_name': full_name,
                'email': email,
                'username': username,
                'password': hashed_password,
                'phone': phone,
                'alt_phone': alt_phone
            })

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        flash('Username already exists. Please try another one.', 'error')
        return redirect(url_for('auth.register'))

    return render_template('register.html')

# User Login Route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = users_collection.find_one({'username': username})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            flash('Login successful!', 'success')

            # Use the correct Blueprint name for the `set_router_ip` route
            if 'router_ip' not in session:
                return redirect(url_for('ip_setup.set_router_ip'))  # Update with correct Blueprint

            return redirect(url_for('dashboard.get_dashboard_data'))  # Ensure correct endpoint

        flash('Invalid username or password. Please try again.', 'error')

    return render_template('about_us.html')

# User Logout Route
@auth.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
