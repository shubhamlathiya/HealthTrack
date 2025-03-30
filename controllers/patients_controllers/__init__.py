from flask import Blueprint

# Initialize the 'client' blueprint
patients = Blueprint('patients', __name__)


from .appointments_routes import *
from .visitors_routes import *
from .profile_routes import *
from .prescription_routes import *
from .dashboard_routes import *
from .operation_request import *