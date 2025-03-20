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

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Twilio configuration
TWILIO_ACCOUNT_SID = 'Your Twilio SID' 
TWILIO_AUTH_TOKEN = 'Your Twilio Token'   
TWILIO_PHONE_NUMBER = 'Your Twilio Phone Number'

#mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'moyijulius17@gmail.com'
app.config['MAIL_PASSWORD'] = 'fwyh bkbi qdtp twbb'     
app.config['MAIL_DEFAULT_SENDER'] = 'moyijulius17@gmail.com'


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
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route("/")
def welcome():
    return render_template("welcome.html")


#route for logging in
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email 
            flash(f"Welcome, {user.username}!", "success")
            return redirect(url_for('dashboard'))  # Changed from 'home' to 'dashboard'
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

def dashboard():
    if 'user_id' not in session: 
        flash("Please login to access the system.", "error")
        return redirect(url_for('login')) 
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
    
    
#route send results via email
def send_results():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Please login to access this feature."})
    
    try:
        # Get data from the request
        email = request.form.get("email")
        disease = request.form.get("disease")
        description = request.form.get("description")
        medication = request.form.get("medication")
        precaution = request.form.get("precaution")
        diet = request.form.get("diet")
        workout = request.form.get("workout")
        
        # Creating  the email content
        subject = f"Your Health Report for {disease}"
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: auto; padding: 20px; }}
                h1 {{ color: #2a5885; }}
                h2 {{ color: #507299; margin-top: 20px; }}
                p {{ line-height: 1.5; }}
                .footer {{ margin-top: 30px; font-size: 0.8em; color: #777; }}
                #dis{{color:red;}}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Your Health Report</h1>
                <h2>Predicted Disease: <span id="dis">{disease}<span></h2>
                
                <h2>Description</h2>
                <p>{description}</p>
                
                <h2>Recommended Medication</h2>
                <p>{medication}</p>
                
                <h2>Precautions</h2>
                <p>{precaution}</p>
                
                <h2>Recommended Diet</h2>
                <p>{diet}</p>
                
                <h2>Recommended Workout</h2>
                <p>{workout}</p>
                
                <div class="footer">
                    <p>This health report is generated based on your symptoms by our AI system.</p>
                    <p>Disclaimer: This is not medical advice. Please consult a healthcare professional for proper diagnosis and treatment.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send the email
        msg = Message(subject=subject, recipients=[email], html=body)
        mail.send(msg)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"success": False, "message": f"Error: {e}"})
           
# get email
@app.route("/get-user-email", methods=["GET"])
def get_user_email():
    if 'email' in session:
        return jsonify({"email": session['email']})
    return jsonify({"email": ""})

#flash message for email sending
@app.route("/set-flash-message", methods=["GET"])
def set_flash_message():
    message_type = request.args.get("type", "info") 
    message = request.args.get("message", "")
    
    if message:
        flash(message, message_type)
    
    return jsonify({"success": True})

    
  # Route to send results via SMS 
@app.route('/api/send-sms', methods=['POST'])
def send_sms():
    try:
        start_time = time.time()
        data = request.get_json()
        
        if not data:
            app.logger.error("No JSON data provided")
            return jsonify({'success': False, 'message': 'No JSON data provided'}), 400
        
        phone_number = data.get('phoneNumber')
        report_data = data.get('data', {})
        
        if not phone_number:
            app.logger.error("Phone number is required")
            return jsonify({'success': False, 'message': 'Phone number is required'}), 400
        
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number.lstrip('0')
        
        disease = report_data.get('disease', 'Not specified')
        precaution = summarize_text(report_data.get('precaution', ''), 100)
        medication = summarize_text(report_data.get('medication', ''), 100)
        
        sms_message = (f"Your Health Report Summary:\n\n"
                     f"Condition: {disease}\n"
                     f"Key Precautions: {precaution}\n"
                     f"Medication: {medication}\n\n"
                     f"Please check your patient portal for the full report.")
        
        app.logger.info(f"Sending SMS to {phone_number}: {sms_message}")
        
        # Log the time taken before sending the SMS
        pre_sms_time = time.time()
        app.logger.info(f"Time taken before sending SMS: {pre_sms_time - start_time} seconds")
        
        try:
            # Send SMS via Twilio
            message = twilio_client.messages.create(
                body=sms_message,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            # Log the time taken after sending the SMS
            post_sms_time = time.time()
            app.logger.info(f"Time taken to send SMS: {post_sms_time - pre_sms_time} seconds")
            
            app.logger.info(f'SMS sent successfully with SID: {message.sid}')
            return jsonify({'success': True, 'message': 'Health report summary sent to your phone'})
        
        except Exception as twilio_error:
            app.logger.error(f'Twilio error: {str(twilio_error)}')
            # Check if it's the specific geographic permissions error
            if "21612" in str(twilio_error):
                return jsonify({
                    'success': False, 
                    'message': 'Your phone number cannot receive messages from our system. This may be due to geographic restrictions or carrier limitations.'
                }), 400
            else:
                return jsonify({'success': False, 'message': f'Failed to send SMS: {str(twilio_error)}'}), 400
    
    except Exception as e:
        app.logger.error(f'Error sending SMS: {str(e)}')
        return jsonify({'success': False, 'message': f'Failed to send SMS: {str(e)}'}), 500


# Get user phone number from the database
@app.route("/get-user-phone", methods=["GET"])
def get_user_phone():
    print("Session:", session)  # Debugging: Print the session
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({"phone_number": user.phone_number})
    return jsonify({"phone_number": ""})

    
#helper
def summarize_text(text, max_length):
    if not text:
        return "None provided"
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
#update profile
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401
    
    user_id = session['user_id']  # Get the user_id from session
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





if __name__ == "__main__":
    app.run(debug=True)