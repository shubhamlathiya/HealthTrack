from flask import Blueprint

# Initialize the 'client' blueprint
patients = Blueprint('patients', __name__)

# Import views from other modules (dashboard, orders)
from .visitors_routes import *
from .appointments_routes import *
from .medical_records_routes import *
from .prescription_routes import *
from .dashboard_routes import *
from .profile_routes import *

from .web_routes import *