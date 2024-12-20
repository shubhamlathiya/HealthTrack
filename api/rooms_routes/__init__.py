from flask import Blueprint

# Initialize the 'client' blueprint
rooms = Blueprint('rooms', __name__)

# Import views from other modules (dashboard, orders)
from .rooms_routes import *