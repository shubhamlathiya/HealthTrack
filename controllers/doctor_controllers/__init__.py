from flask import Blueprint

# Initialize the 'client' blueprint
doctors = Blueprint('doctor', __name__)

# Import views from other modules (dashboard, orders)
from .appointments_routes import *
from .dashboard_routes import *
from .generate_operation_request import *
from .team_routes import *