from flask import Flask, render_template, session, jsonify, redirect
from flask_mail import Mail

from controllers.admin_controllers import admin
from controllers.auth_controllers import auth
from controllers.patients_controllers import patients
from utils.config import init_app

app = Flask(__name__, static_folder="static")

init_app(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shubhamlathiya2021@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tqerujnjzuvgdjho'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize the mail object
mail = Mail(app)

app.config['SECRET_KEY'] = 'your_secure_random_key'
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(patients, url_prefix='/patients')

@app.route('/')
def index():  # put application's code here
    return render_template('auth_templates/login_templates.html')


@app.errorhandler(404)
def handle_404_error(e):
    return render_template('error_handler/error_404.html')


@app.errorhandler(500)
def handle_500_error(e):
    return render_template('error_handler/error_500.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    response = jsonify({'message': 'Logged out successfully!'})
    response.set_cookie('token', '', expires=0)
    response = redirect('/')  # Clear the cookie
    return response


if __name__ == '__main__':
    app.run()
