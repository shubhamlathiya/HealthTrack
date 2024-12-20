from flask import Blueprint

# Initialize the 'client' blueprint
receptionist = Blueprint('receptionist', __name__)

# Import views from other modules (dashboard, orders)
from .receptionist_routes import *
