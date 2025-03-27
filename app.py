from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import numpy as np
import pandas as pd
from difflib import get_close_matches
from flask_sqlalchemy import SQLAlchemy
from model import db, User  
from forms import RegistrationForm, LoginForm
import time
from flask_migrate import Migrate
from twilio.rest import Client
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from functools import wraps
from datetime import datetime
from model import db, User, Testimonial
from model import UserReport
from flask import request, jsonify
from model import db, UserReport
import traceback 
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os

#defining app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login view

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize SQLAlchemy and Mail
db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)


#endpoint for welcoming page for the system
@app.route("/")
def welcome():
    return render_template("welcome.html")


#route for logging in the system
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id  
            session['email'] = user.email  
            flash(f"Welcome, {user.username}!", "success")
            
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)

#register route to redirect to login
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        phone_number = form.phone.data 

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            flash("Email already registered continue login", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            new_user = User(username=username, phone_number=phone_number, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
            return redirect(url_for('register'))

    return render_template('register.html', form=form)

#Route to allow register user navigate to main home page
@app.route("/dashboard")
@login_required 
def dashboard():
    return render_template("index.html", symptoms=symptoms)

#route to logout users
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!.", "success")
    return redirect(url_for('login'))

# Load the trained model and required files
try:
    model = pickle.load(open("model/svc.pkl", "rb"))
    symptoms = pickle.load(open("model/symptom_list.pkl", "rb"))
    disease_mapping = pickle.load(open("model/disease_mapping.pkl", "rb"))
except FileNotFoundError as e:
    print(f"Error: {e}")
    model, symptoms, disease_mapping = None, [], {}

# Load medication and description data
try:
    medication_data = pd.read_csv("data/medications.csv")
    description_data = pd.read_csv("data/description.csv")
    precautions_df_data=pd.read_csv("data/precautions_df.csv")
    diets_data=pd.read_csv("data/diets.csv")
    workout_df_data=pd.read_csv("data/workout_df.csv")
except FileNotFoundError as e:
    print(f"Error loading CSV files: {e}")
    medication_data, description_data, precautions_df_data, diets_data, workout_df_data = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def match_symptoms(user_symptoms, valid_symptoms, threshold=0.6):
    matched = []
    unmatched = []
    for user_symptom in user_symptoms:
        closest = get_close_matches(user_symptom, valid_symptoms, n=1, cutoff=threshold)
        if closest:
            matched.append(closest[0])
        else:
            unmatched.append(user_symptom)
    return matched, unmatched

#route to predict disease
@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model files not found. Ensure svc.pkl, symptom_list.pkl, and disease_mapping.pkl exist."})

    try:
        user_input = request.form.get("symptoms", "")
        user_symptoms = [symptom.strip().lower().replace(" ", "_") for symptom in user_input.split(",")]

        matched_symptoms, unmatched_symptoms = match_symptoms(user_symptoms, symptoms)

        if unmatched_symptoms:
            return jsonify({
                "error": f"Some symptoms could not be recognized: {', '.join(unmatched_symptoms)}. "
                         f"Matched symptoms: {', '.join(matched_symptoms)}."
            })

        # Create a zero vector with correct feature names
        input_vector = np.zeros(len(symptoms))
        for symptom in matched_symptoms:
            if symptom in symptoms:
                input_vector[symptoms.index(symptom)] = 1
        input_df = pd.DataFrame([input_vector], columns=symptoms)

        # Make prediction
        prediction = model.predict(input_df)[0]
        disease_name = disease_mapping.get(prediction, "Unknown Disease")

        return jsonify({"disease": disease_name})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/details/<disease>", methods=["GET"])
def get_disease_details(disease):
    try:
        # Fetch medication,description,precaution,workouts and diets for the given or predicted disease
        medication = medication_data[
            medication_data["Disease"].str.strip().str.lower() == disease.strip().lower()
        ]
        description = description_data[
           description_data["Disease"].str.strip().str.lower() == disease.strip().lower()
        ]
        precautions_df = precautions_df_data[
            precautions_df_data["Disease"].str.strip().str.lower() == disease.strip().lower()
        ]
        diets = diets_data[
            diets_data["Disease"].str.strip().str.lower() == disease.strip().lower()
        ]
        workout_df = workout_df_data[
           workout_df_data["Disease"].str.strip().str.lower() == disease.strip().lower()
        ]

        # Get the first match or return default messages
        medication_info = medication["Medication"].iloc[0] if not medication.empty else "No medication information available."
        description_info = description["Description"].iloc[0] if not description.empty else "No description available."
        precautions_df_info = precautions_df["Precaution_1"].iloc[0] if not precautions_df.empty else "No description available."
        diets_info = diets["Diet"].iloc[0] if not diets.empty else "No Diets available."
        workout_df_info = workout_df["workout"].iloc[0] if not workout_df.empty else "No Workout available."

        return jsonify({
            "medication": medication_info,
            "description": description_info,
            "precautions_df": precautions_df_info,
            "diets": diets_info,
            "workout_df": workout_df_info,
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    
#Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():  # Note: should be is_admin() if it's a method
        flash("You don't have permission to access this page", "error")
        return redirect(url_for('login'))  # Redirect to regular dashboard
    
    users = User.query.filter(User.id != current_user.id).all()
    current_year = datetime.now().year  
    return render_template('base_admin.html', users=users)


#admin various routes
#user management routes
@app.route('/admin/user-management')
@login_required
def user_management():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        # Fetch all users except the current admin, ordered by id
        users = User.query.filter(User.id != current_user.id).order_by(User.id).all()
        return render_template('user_management.html', users=users)
    except Exception as e:
        app.logger.error(f"Error in user management: {str(e)}")
        flash('An error occurred while loading user management.', 'danger')
        return redirect(url_for('admin_dashboard'))

# Additional route for user deletion
@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting the current admin user
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('user_management'))

        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting user: {str(e)}")
        flash('An error occurred while deleting the user.', 'danger')
    
    return redirect(url_for('user_management'))

#Admin Reports routes
@app.route('/admin/reports')
@login_required
def admin_reports():
    # Check admin privileges
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # Fetch more comprehensive reports
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_reports = UserReport.query.count()
        recent_reports = UserReport.query.order_by(UserReport.created_at.desc()).limit(10).all()
        
        # Get disease distribution
        disease_distribution = db.session.query(
            UserReport.disease, 
            db.func.count(UserReport.id).label('count')
        ).group_by(UserReport.disease).order_by(db.desc('count')).all()
        
        return render_template('reports.html', 
                               total_users=total_users,
                               active_users=active_users,
                               total_reports=total_reports,
                               recent_reports=recent_reports,
                               disease_distribution=disease_distribution)
    except Exception as e:
        # Import traceback to get more detailed error information
        import traceback
        print(traceback.format_exc())
        app.logger.error(f"Error in reports: {str(e)}")
        flash('An error occurred while generating reports.', 'danger')
        return redirect(url_for('admin_dashboard'))

#admin main dashboard
@app.route('/admindashboard', methods=['GET'])
def mainadmin():
    return render_template('admindashboard.html')

# Testimonial routes to allow users send reviews
@app.route('/testimonials', methods=['GET'])
def testimonials():
    return render_template('testimonials.html')

#routes to send testimonials
@app.route('/submit-testimonial', methods=['POST'])
@login_required
def submit_testimonial():
    name = request.form.get('name')
    content = request.form.get('content')
    
    if not name or not content:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('testimonials'))
    
    testimonial = Testimonial(
        user_id=current_user.id,
        name=name,
        content=content,
        status='pending'
    )
    
    db.session.add(testimonial)
    db.session.commit()
    
    flash('Thank you for your testimonial! It will be reviewed by our team.', 'success')
    return redirect(url_for('testimonials'))

# Admin testimonial management
@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    status = request.args.get('status', 'pending')
    testimonials = Testimonial.query.filter_by(status=status).all()
    return render_template('admin_testimonials.html', 
                         testimonials=testimonials,
                         status=status)
#routes to allow admin aprove
@app.route('/admin/testimonial/<int:testimonial_id>/approve', methods=['POST'])
@login_required
def approve_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.status = 'approved'
    testimonial.admin_notes = request.form.get('notes', '')
    db.session.commit()
    flash('Testimonial approved successfully', 'success')
    return redirect(url_for('admin_testimonials'))

# route to allow admin reject testimonials
@app.route('/admin/testimonial/<int:testimonial_id>/reject', methods=['POST'])
@login_required
def reject_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.status = 'rejected'
    testimonial.admin_notes = request.form.get('notes', '')
    db.session.commit()
    flash('Testimonial rejected', 'info')
    return redirect(url_for('admin_testimonials'))

#routes to load profile of user
@app.route('/profile')
@login_required
def profile():
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        app.logger.error(f"Error in profile: {str(e)}")
        flash('An error occurred while loading profile.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
#routes for setting
@app.route('/settings')
@login_required
def settings():
    try:
        return render_template('settings.html')
    except Exception as e:
        app.logger.error(f"Error in settings: {str(e)}")
        flash('An error occurred while loading settings.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
#save user report in database
@app.route('/save-report', methods=['POST'])
@login_required
def save_report():
    try:
        report_data = request.get_json()
        
        new_report = UserReport(
            user_id=current_user.id,
            disease=report_data.get('disease', ''),
            symptoms=report_data.get('symptoms', ''), 
            description=report_data.get('description', ''),
            medication=report_data.get('medication', ''),
            precaution=report_data.get('precaution', ''),
            diet=report_data.get('diet', ''),
            workout=report_data.get('workout', '')
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Report saved successfully'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving report: {str(e)}")
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
#update profile
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401
    
    user_id = session['user_id']  
    user = User.query.get(user_id)
    
    if user:
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.phone_number = request.form.get('phone_number')
        user.age = request.form.get('age')
        user.gender = request.form.get('gender')
        
        db.session.commit()
        
        # Update the session with new username and email
        session['username'] = user.username
        session['email'] = user.email
        
        return jsonify({'message': 'Profile updated successfully!'}), 200
    else:
        return jsonify({'message': 'User not found!'}), 404
    
#Reports
@app.route("/report-history")
@login_required
def report_history():
    reports = UserReport.query.filter_by(user_id=current_user.id).order_by(UserReport.created_at.desc()).all()
    return render_template("report_history.html", reports=reports)

#populate the profile with data
@app.route('/get_profile_data')
def get_profile_data():
    if 'user_id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401
    
    user = User.query.get(session['user_id'])
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'phone_number': user.phone_number,
            'age': user.age,
            'gender': user.gender
        })
    return jsonify({'message': 'User not found!'}), 404

# about view function and path
@app.route('/about')
def about():
    return render_template("about.html")


# contact view function and path
@app.route('/contact')
def contact():
    return render_template("contact.html")

# developer view function and path
@app.route('/developer')
def developer():
    return render_template("developer.html")
#dashboard refereshing
@app.route('/admin_dashboard1')
def admin_dashboard1():
    # Calculate user role counts
    admin_count = User.query.filter_by(role='admin').count()
    regular_count = User.query.filter_by(role='regular').count()
    restricted_count = User.query.filter_by(role='restricted').count()

    return render_template('admin_dashboard.html', 
        admin_count=admin_count,
        regular_count=regular_count,
        restricted_count=restricted_count
    )
#refreshing
@app.route('/refresh_dashboard')
def refresh_dashboard():
    # Example refresh logic
    return jsonify({
        'user_roles': {
            'admin': User.query.filter_by(role='admin').count(),
            'regular': User.query.filter_by(role='regular').count(),
            'restricted': User.query.filter_by(role='restricted').count()
        }
    })
#user details by admin
@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user details
        user.username = request.form['username']
        user.email = request.form['email']
        user.full_name = request.form.get('full_name')
        user.phone_number = request.form.get('phone_number')
        user.role = request.form.get('role')
        user.is_active = 'is_active' in request.form

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.profile_picture = file_path

        try:
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('view_user', user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')

    return render_template('edit_user.html', user=user)

@app.route('/users/view/<int:user_id>')
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('view_user.html', user=user)





if __name__ == "__main__":
    app.run(debug=True)