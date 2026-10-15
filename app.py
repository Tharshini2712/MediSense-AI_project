from flask import Flask, render_template, request, session, send_file, redirect, jsonify, flash
from utils.predictor import predict_diseases
from utils.pdf_generator import generate_report
from utils.auth_db import init_db, register_user, check_login
from utils.session_db import save_consultation, get_consultations
from datetime import date
import os
import functools

app = Flask(__name__)
app.secret_key = "medisense_secret_key_2026"

# ----------------------------
# INIT DATABASE ON STARTUP
# Task 3 + Task 4: creates users and consultations tables
# ----------------------------

with app.app_context():
    init_db()


# ----------------------------
# LOGIN REQUIRED DECORATOR
# Task 3: protects all pages from unauthenticated access
# ----------------------------

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


# ----------------------------
# LOGIN
# Task 3: real login with password check
# ----------------------------

@app.route('/', methods=['GET'])
def login():
    if 'user_id' in session:
        return redirect('/home')
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def do_login():
    email    = request.form.get('email',    '').strip()
    password = request.form.get('password', '').strip()

    if not email or not password:
        flash('Please enter both email and password.', 'error')
        return redirect('/')

    user = check_login(email, password)

    if user:
        session['user_id']    = user['id']
        session['user_name']  = user['name']
        session['user_email'] = user['email']
        return redirect('/home')

    flash('Incorrect email or password. Please try again.', 'error')
    return redirect('/')


# ----------------------------
# REGISTER
# Task 3: create new account with hashed password
# ----------------------------

@app.route('/register', methods=['GET'])
def register():
    if 'user_id' in session:
        return redirect('/home')
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def do_register():
    name     = request.form.get('name',     '').strip()
    email    = request.form.get('email',    '').strip()
    password = request.form.get('password', '').strip()
    confirm  = request.form.get('confirm',  '').strip()

    if not name or not email or not password:
        flash('All fields are required.', 'error')
        return redirect('/register')

    if len(password) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect('/register')

    if password != confirm:
        flash('Passwords do not match.', 'error')
        return redirect('/register')

    result = register_user(name, email, password)

    if result['success']:
        flash('Account created! Please log in.', 'success')
        return redirect('/')

    flash(result['error'], 'error')
    return redirect('/register')


# ----------------------------
# LOGOUT
# Task 3: clear session and redirect to login
# ----------------------------

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/')


# ----------------------------
# HOME
# ----------------------------

@app.route('/home')
@login_required
def home():
    return render_template('home.html')


# ----------------------------
# TERMS
# ----------------------------

@app.route('/terms')
def terms():
    return render_template('terms.html')


# ----------------------------
# PATIENT
# ----------------------------

@app.route('/patient')
@login_required
def patient():
    return render_template('patient.html')


@app.route('/set_patient/<patient_type>')
@login_required
def set_patient(patient_type):
    session['patient_type'] = patient_type
    return redirect('/gender')


# ----------------------------
# GENDER
# ----------------------------

@app.route('/gender')
@login_required
def gender():
    return render_template('gender.html')


@app.route('/set_gender/<gender>')
@login_required
def set_gender(gender):
    session['gender'] = gender
    return redirect('/dob')


# ----------------------------
# DOB
# ----------------------------

@app.route('/dob')
@login_required
def dob():
    return render_template('dob.html')


@app.route('/save_dob', methods=['POST'])
@login_required
def save_dob():
    day   = int(request.form['day'])
    month = int(request.form['month'])
    year  = int(request.form['year'])

    today = date.today()

    age = (
        today.year
        - year
        - ((today.month, today.day) < (month, day))
    )

    session['age'] = f"{age} Years"

    return redirect('/history')


# ----------------------------
# HISTORY
# ----------------------------

@app.route('/history')
@login_required
def history():
    return render_template('history.html')


@app.route('/save_history', methods=['POST'])
@login_required
def save_history():
    selected = []

    for item in request.form:
        selected.append(item)

    session['history'] = selected

    return redirect('/symptoms')


# ----------------------------
# SYMPTOMS
# ----------------------------

@app.route('/symptoms')
@login_required
def symptoms():
    return render_template('symptoms.html')


@app.route('/save_symptoms', methods=['POST'])
@login_required
def save_symptoms():
    symptoms_text = request.form.get('symptoms', '')

    symptoms_list = [
        s.strip().lower()
        for s in symptoms_text.split(',')
        if s.strip()
    ]

    session['symptoms'] = symptoms_list

    return redirect('/carelevel')


# ----------------------------
# SYMPTOM AUTOCOMPLETE API
# Autocomplete: called by symptoms.html via fetch('/api/symptoms')
# Returns JSON list of matching symptom strings
# ----------------------------

@app.route('/api/symptoms')
@login_required
def api_symptoms():

    all_symptoms = sorted([
        "abdominal pain", "acidity", "altered sensorium", "anxiety",
        "back pain", "belly pain", "blackheads", "bladder discomfort",
        "blister", "blood in sputum", "blurred and distorted vision",
        "body aches", "breathlessness", "bruising", "burning micturition",
        "chest pain", "chest tightness", "chills", "cold hands and feets",
        "congestion", "constipation", "continuous feel of urine",
        "continuous sneezing", "cough", "cramps",
        "dark urine", "dehydration", "depression", "diarrhoea",
        "dischromic patches", "distention of abdomen", "dryness",
        "enlarged thyroid", "excessive hunger", "fatigue", "fever",
        "fluid overload", "foul smell of urine", "frequent urination",
        "headache", "high fever", "hip joint pain",
        "history of alcohol consumption", "inflammatory nails",
        "internal itching", "irritability", "irritation in anus", "itching",
        "jaw pain", "joint pain", "knee pain",
        "lack of concentration", "left arm pain", "lethargy",
        "loss of appetite", "loss of balance", "lower abdominal pain",
        "malaise", "mild fever", "mood swings", "movement stiffness",
        "mucoid sputum", "muscle pain", "muscle wasting", "muscle weakness",
        "nausea", "neck pain", "nodal skin eruptions",
        "obesity", "oily skin", "pain behind the eyes",
        "pain during bowel movements", "pain in anal region",
        "painful walking", "palpitations", "passage of gases",
        "patches in throat", "phlegm", "polyuria", "prolonged fever",
        "prominent veins on calf", "puffy face and eyes", "pus filled pimples",
        "red patches on skin", "red sore around nose", "red spots over body",
        "restlessness", "runny nose", "rusty sputum", "scarring", "shivering",
        "silver like dusting", "skin peeling", "skin rash", "slurred speech",
        "small dents in nails", "sore throat", "spinning movements",
        "stiff neck", "stomach cramps", "stomach pain",
        "sunken eyes", "swelled lymph nodes", "swelling joints",
        "swelling of stomach", "swollen blood vessels", "swollen legs",
        "sweating", "throat irritation", "toxic look",
        "ulcers on tongue", "unsteadiness", "visual disturbances", "vomiting",
        "watering from eyes", "weakness in limbs", "weakness of one body side",
        "weight gain", "weight loss", "wheezing",
        "yellowing of eyes", "yellowish skin", "yellow crust ooze",
    ])

    q = request.args.get('q', '').strip().lower()

    if q:
        result = [s for s in all_symptoms if q in s]
    else:
        result = all_symptoms

    return jsonify(result)


# ----------------------------
# CARE LEVEL
# ----------------------------

@app.route('/carelevel')
@login_required
def carelevel():
    return render_template('carelevel.html')


@app.route('/save_carelevel', methods=['POST'])
@login_required
def save_carelevel():
    session['care_level'] = request.form.get('care_level')
    return redirect('/intensity')


# ----------------------------
# INTENSITY
# ----------------------------

@app.route('/intensity')
@login_required
def intensity():
    return render_template('intensity.html')


@app.route('/save_intensity', methods=['POST'])
@login_required
def save_intensity():
    value = request.form.get('intensity')

    if value:
        session['intensity'] = f"{value}/10"
    else:
        session['intensity'] = "Not Selected"

    # Task 4: save the complete consultation to SQLite right here
    symptoms = session.get('symptoms', [])
    diseases = predict_diseases(symptoms)

    consultation_id = save_consultation(
        user_id      = session.get('user_id', 0),
        patient_type = session.get('patient_type', 'Not Selected'),
        gender       = session.get('gender',       'Not Selected'),
        age          = session.get('age',          'Not Selected'),
        care_level   = session.get('care_level',   'Not Selected'),
        intensity    = session.get('intensity',    'Not Selected'),
        symptoms     = symptoms,
        diseases     = diseases,
    )

    session['consultation_id'] = consultation_id

    return redirect('/result')


# ----------------------------
# RESULT
# Task 1: predict_diseases now uses real ML model
# ----------------------------

@app.route('/result')
@login_required
def result():
    symptoms = session.get('symptoms', [])
    diseases = predict_diseases(symptoms)

    return render_template(
        'result.html',
        symptoms=symptoms,
        diseases=diseases
    )


# ----------------------------
# SUMMARY
# ----------------------------

@app.route('/summary')
@login_required
def summary():
    symptoms = session.get('symptoms', [])
    diseases = predict_diseases(symptoms)

    return render_template(
        'summary.html',
        patient_type = session.get('patient_type', 'Not Selected'),
        gender       = session.get('gender',       'Not Selected'),
        age          = session.get('age',          'Not Selected'),
        care_level   = session.get('care_level',   'Not Selected'),
        intensity    = session.get('intensity',    'Not Selected'),
        symptoms     = symptoms,
        diseases     = diseases,
        user_name    = session.get('user_name',    ''),
    )


# ----------------------------
# CONSULTATION HISTORY PAGE
# Task 4: shows all past saved consultations for this user
# ----------------------------

@app.route('/history_page')
@login_required
def history_page():
    user_id       = session.get('user_id', 0)
    consultations = get_consultations(user_id)
    return render_template(
        'history_page.html',
        consultations = consultations,
        user_name     = session.get('user_name', ''),
    )


# ----------------------------
# PDF REPORT
# ----------------------------

@app.route('/download_report')
@login_required
def download_report():
    symptoms = session.get('symptoms', [])
    diseases = predict_diseases(symptoms)

    patient_type = session.get('patient_type', 'Not Selected')
    gender       = session.get('gender',       'Not Selected')
    age          = session.get('age',          'Not Selected')
    care_level   = session.get('care_level',   'Not Selected')
    intensity    = session.get('intensity',    'Not Selected')

    os.makedirs('reports', exist_ok=True)

    filepath = os.path.join('reports', 'MediSense_Report.pdf')

    generate_report(
        filepath,
        patient_type,
        gender,
        age,
        care_level,
        intensity,
        symptoms,
        diseases
    )

    return send_file(filepath, as_attachment=True)


# ----------------------------
# RUN APP
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True)