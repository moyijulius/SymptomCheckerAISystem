from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,current_user
from datetime import datetime

# Initialize the db instance here
db = SQLAlchemy()
class UserReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    disease = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.String(500), nullable=True) 
    description = db.Column(db.Text)
    medication = db.Column(db.Text)
    precaution = db.Column(db.Text)
    diet = db.Column(db.Text)
    workout = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    
    user = db.relationship('User', backref='reports')


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    admin_notes = db.Column(db.Text)
    
    user = db.relationship('User', backref='testimonials')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone_number = db.Column(db.String(10))
    age = db.Column(db.Integer)  
    gender = db.Column(db.String(50))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    full_name = db.Column(db.String(100), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'
    def is_admin(self):
        return self.role == 'admin'  # Helper method to check if user is admin
    
