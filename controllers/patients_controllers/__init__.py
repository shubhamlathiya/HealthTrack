from flask import Blueprint

# Initialize the 'client' blueprint
patients = Blueprint('patient', __name__)


from .dashboard_routes import *
from .appointment.appointments_routes import *
from .invoice.invoice import *