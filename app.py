from flask import Flask
from flask_mail import Mail

from utils.config import init_app

app = Flask(__name__)

init_app(app)


app.config['SECRET_KEY'] = 'your_secure_random_key'

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shubhamlathiya2021@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tqerujnjzuvgdjho'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize the mail object
mail = Mail(app)

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
