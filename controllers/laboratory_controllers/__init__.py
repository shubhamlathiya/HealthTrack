from flask import Blueprint

# Initialize the 'client' blueprint
laboratory = Blueprint('laboratory', __name__)

# Import views from other modules (dashboard, orders)
from .dashboard_routes import *
from .manage_lab_reports_routes import *
from .lab import *