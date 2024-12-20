from flask import Blueprint

# Initialize the 'client' blueprint
staffs = Blueprint('staffs', __name__)

# Import views from other modules (dashboard, orders)
from .staff_routes import *