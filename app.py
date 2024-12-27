from flask_socketio import SocketIO

from flask import Flask, render_template, send_from_directory, jsonify, make_response
from flask_mail import Mail

from api.admin_routes import admin
from api.auth_routes import auth
from api.chat_routes.chat_routes import chat_routes
from api.chat_routes.chat_sockets import init_socket_events
from api.doctor_routes import doctors
from api.every_one import idCard
from api.laboratory_routes import laboratory
from api.nurse_routes import nurses
from api.patients import patients
from api.rooms_routes import rooms
from config import mongo, init_app
from flask_cors import CORS

app = Flask(__name__)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shubhamlathiya2021@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tqerujnjzuvgdjho'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize the mail object
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*")
init_app(app)

app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(patients, url_prefix='/patients')
app.register_blueprint(doctors, url_prefix='/doctors')
app.register_blueprint(laboratory, url_prefix='/laboratory')
app.register_blueprint(rooms, url_prefix='/rooms')
app.register_blueprint(nurses, url_prefix='/nurses')
app.register_blueprint(idCard, url_prefix='/idCard')
# Register Routes
app.register_blueprint(chat_routes)

init_socket_events(socketio, mongo)

CORS(app)


@app.route('/uploads/reports/<filename>')
def download_file(filename):
    return send_from_directory('uploads/reports', filename)

@app.route('/uploads/patient_reports/<filename>')
def download_file_patient_reports(filename):
    return send_from_directory('uploads/patient_reports', filename)

@app.route('/logout', methods=['GET'])
def logout():
    try:
        # Clear cookies (e.g., for authentication token or session)
        response = make_response(jsonify({"message": "Logged out successfully"}), 200)

        # Example of clearing a cookie (e.g., 'auth_token')
        response.delete_cookie('token')  # Adjust this based on the name of your auth token cookie
        response.delete_cookie('session_id')  # If you have other cookies to delete

        # Optionally, clear other session data on the server-side if needed
        # For example, using Flask sessions (if used):
        # session.clear()

        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run()
