import os
from datetime import datetime

import humanize
from dotenv import load_dotenv
from flask import Flask, render_template, session, redirect, send_from_directory, request
from flask_mail import Mail
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

from controllers.admin_controllers import admin
from controllers.auth_controllers import auth
from controllers.backups_controllers.backups import backups_bp
from controllers.chat_bot_controllers import chatbot
from controllers.department_controllers import department
from controllers.doctor_controllers import doctors
from controllers.every_one_controllers import idCard
from controllers.laboratory_controllers import laboratory
from controllers.patients_controllers import patients
from controllers.setup_controllers import setup
from models import User, UserRole
from models.medicineModel import MedicineUnit, MedicineGroup
from utils.config import init_app, db
from utils.create_new_patient import create_new_patient

app = Flask(__name__, static_folder="static")
load_dotenv()
init_app(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # Your email
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
app.config['MAIL_DEBUG'] = True  # Enable SMTP debug output
app.config['MAIL_SUPPRESS_SEND'] = False  # Actually send emails

# Initialize the mail object
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(department, url_prefix='/department')
from controllers.chat_controllers import chat

app.register_blueprint(chat, url_prefix='/chat')
app.register_blueprint(chatbot , url_prefix='/chatbot')
app.register_blueprint(backups_bp, url_prefix='/backups')
app.register_blueprint(patients, url_prefix='/patient')
app.register_blueprint(doctors, url_prefix='/doctor')
app.register_blueprint(laboratory, url_prefix='/laboratory')
app.register_blueprint(setup, url_prefix='/setup')

app.register_blueprint(idCard, url_prefix='/id-card')

with app.app_context():
    # db.drop_all()
    db.create_all()

    if not User.query.filter_by(role=UserRole.ADMIN).first():
        units = [
            {"name": "Tablet", "symbol": "tab"},
            {"name": "Capsule", "symbol": "cap"},
            {"name": "Syrup", "symbol": "ml"},
            {"name": "Injection", "symbol": "inj"},
            {"name": "Cream", "symbol": "g"},
        ]

        for unit in units:
            db.session.add(MedicineUnit(name=unit["name"], symbol=unit["symbol"]))

        db.session.commit()

        groups = [
            {"name": "Antibiotics", "description": "Used to treat bacterial infections"},
            {"name": "Analgesics", "description": "Pain relievers"},
            {"name": "Antipyretics", "description": "Used to reduce fever"},
            {"name": "Antiseptics", "description": "Prevent the growth of disease-causing microorganisms"},
            {"name": "Antacids", "description": "Neutralize stomach acidity"},
        ]

        for group in groups:
            db.session.add(MedicineGroup(name=group["name"], description=group["description"]))

        db.session.commit()
        for role in UserRole:
            if not User.query.filter_by(role=role).first():
                user = User(
                    email=f'{role.value}@hospital.com',
                    password=generate_password_hash('Shubham123'),
                    role=role,
                    status=True,
                    verified=True
                )
                db.session.add(user)

        db.session.commit()

        # List of 5 patient dictionaries
        sample_patients = [
            {
                "email": "rahul.sharma@example.com",
                "first_name": "Rahul",
                "last_name": "Sharma",
                "phone": "9876543210",
                "age": 28,
                "gender": "Male"
            },
            {
                "email": "priya.verma@example.com",
                "first_name": "Priya",
                "last_name": "Verma",
                "phone": "8765432109",
                "age": 34,
                "gender": "Female"
            },
            {
                "email": "amit.patel@example.com",
                "first_name": "Amit",
                "last_name": "Patel",
                "phone": "7654321098",
                "age": 45,
                "gender": "Male"
            },
            {
                "email": "sneha.kumar@example.com",
                "first_name": "Sneha",
                "last_name": "Kumar",
                "phone": "6543210987",
                "age": 23,
                "gender": "Female"
            },
            {
                "email": "deepak.joshi@example.com",
                "first_name": "Deepak",
                "last_name": "Joshi",
                "phone": "5432109876",
                "age": 37,
                "gender": "Male"
            }
        ]

        # Insert all sample patients
        for patient in sample_patients:
            create_new_patient(patient)

        # Commit all at once
        db.session.commit()

        # admin = User(
        #     email='admin@hospital.com',
        #     password=generate_password_hash('Shubham123'),
        #     role=UserRole.ADMIN,
        #     status=True,
        #     verified=True
        # )
        # db.session.add(admin)
        # db.session.commit()

@app.template_filter('humanize')
def humanize_timestamp(value):
    if isinstance(value, datetime):
        return humanize.naturaltime(datetime.now() - value)
    return value
@app.route('/')
def index():  # put application's code here
    return render_template('auth_templates/login_templates.html')


@app.errorhandler(404)
def handle_404_error(e):
    return render_template('error_handler/error_404.html'),404


@app.errorhandler(500)
def handle_500_error(e):
    return render_template('error_handler/error_500.html'),505

@app.errorhandler(403)
def forbidden_error(e):
    return render_template("error_handler/error_403.html"), 403


# Configure upload folder for profile pictures
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


@app.route('/logout', methods=['GET'])
def logout():
    # Clear the session
    session.clear()

    # Create a redirect response
    response = redirect('/')

    # Clear all cookies by iterating through request.cookies
    for cookie_name in request.cookies:
        response.delete_cookie(cookie_name)

    return response


@app.route('/demo')
def demo():  # put application's code here
    return render_template('setup_templates/operationtheatre.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
