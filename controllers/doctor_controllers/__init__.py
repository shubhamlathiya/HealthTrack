from flask import Blueprint

# Initialize the 'client' blueprint
doctors = Blueprint('doctor', __name__)

from .dashboard_routes import *
from .appointment.doctor_appointments_routes import *
from .appointment.prescriptions_routes import *