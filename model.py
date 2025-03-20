from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize the db instance here
db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone_number = db.Column(db.String(10))
    age = db.Column(db.Integer)  # Fixed this line
    gender = db.Column(db.String(50))  # New field for gender

    def __repr__(self):
        return f'<User {self.username}>'
