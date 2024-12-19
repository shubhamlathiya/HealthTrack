from flask_socketio import SocketIO


from flask import Flask
from flask_mail import Mail

from api.admin_routes import admin
from api.auth_routes import auth
from api.chat_routes.chat_routes import chat_routes
from api.chat_routes.chat_sockets import init_socket_events
from api.doctor_routes import doctors
from api.patients import patients
from config import mongo, init_app

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

# Register Routes
app.register_blueprint(chat_routes)

init_socket_events(socketio, mongo)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
