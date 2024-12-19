from flask import Blueprint

# Initialize the 'client' blueprint
doctors = Blueprint('doctor', __name__)

# Import views from other modules (dashboard, orders)
from .medical_record_routes import *
from .appointments_routes import *
from .prescription_routes import *