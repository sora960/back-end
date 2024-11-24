# user.py

from flask_login import UserMixin
from bson import ObjectId
from flask import current_app

class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

    def get_id(self):
        return self.id

# Define the user_loader
def load_user(user_id):
    # Fetch the user from MongoDB using the user_id
    mongo = current_app.extensions['pymongo']
    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(str(user_data['_id']), user_data['username'], user_data['role'])
    return None
