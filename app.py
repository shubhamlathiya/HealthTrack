from datetime import datetime

import humanize
from flask import Flask, render_template, session, redirect, send_from_directory, request
from flask_mail import Mail
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

from controllers.admin_controllers import admin
from controllers.auth_controllers import auth
from controllers.department_controllers import department
from controllers.doctor_controllers import doctors
from controllers.every_one_controllers import idCard
from controllers.laboratory_controllers import laboratory
from controllers.patients_controllers import patients
from models.userModel import User, UserRole
from utils.config import init_app, db

app = Flask(__name__, static_folder="static")

init_app(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shubhamlathiya2021@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tqerujnjzuvgdjho'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'shubhamlathiya2021@gmail.com'
app.config['MAIL_DEBUG'] = True  # Enable SMTP debug output
app.config['MAIL_SUPPRESS_SEND'] = False  # Actually send emails

# Initialize the mail object
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SECRET_KEY'] = 'your_secure_random_key'
app.register_blueprint(auth, url_prefix='/auth')
# app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(department, url_prefix='/department')
from controllers.chat_controllers import chat

# app.register_blueprint(chat, url_prefix='/chat')
# app.register_blueprint(patients, url_prefix='/patient')
# app.register_blueprint(doctors, url_prefix='/doctor')
# app.register_blueprint(laboratory , url_prefix='/laboratory')

# app.register_blueprint(idCard, url_prefix='/id-card')

with app.app_context():
    db.create_all()

    # Create admin user if not exists
    if not User.query.filter_by(role=UserRole.ADMIN).first():
        admin = User(
            email='admin@hospital.com',
            password=generate_password_hash('Shubham123'),
            role=UserRole.ADMIN,
            status=True,
            verified=True
        )
        db.session.add(admin)
        db.session.commit()

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


if __name__ == '__main__':
    socketio.run(app, debug=True)
