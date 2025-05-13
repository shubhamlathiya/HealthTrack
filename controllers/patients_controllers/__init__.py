from flask import Blueprint

# Initialize the 'client' blueprint
patients = Blueprint('patient', __name__)


from .dashboard_routes import *
from .appointment.appointments_routes import *
from .invoice.invoice import *
from .blood_donor.donors import *
# from .blood_donor.blood_requests import *