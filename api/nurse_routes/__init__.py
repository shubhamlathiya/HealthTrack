from flask import Blueprint

# Initialize the 'client' blueprint
nurses = Blueprint('nurses', __name__)

# Import views from other modules (dashboard, orders)
from .nurses_routes import *
