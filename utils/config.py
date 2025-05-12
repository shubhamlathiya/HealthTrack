from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()


def init_app(app):
    """Initialize the Flask app with MySQL and SQLAlchemy. healthtrack_demo"""
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost/healthtrack'  # Replace with your MySQL credentials and DB name
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking modifications to avoid overhead
    app.config['SQLALCHEMY_ECHO'] = True  # Set to True for debugging SQL queries

    # Initialize the SQLAlchemy extension with the app
    db.init_app(app)


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)