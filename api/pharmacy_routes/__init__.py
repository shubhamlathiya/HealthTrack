from flask import Blueprint

# Initialize the 'client' blueprint
pharmacy = Blueprint('pharmacy', __name__)

# Import views from other modules (dashboard, orders)
from .pharmacy_routes import *