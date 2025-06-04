import os

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()


def init_app(app):
    """Initialize the Flask app with MySQL and SQLAlchemy. healthtrack_demo"""
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications to avoid overhead
    app.config['SQLALCHEMY_ECHO'] = True  # Set to True for debugging SQL queries
    app.config['use_enum_values '] = True
    # Initialize the SQLAlchemy extension with the app
    db.init_app(app)
