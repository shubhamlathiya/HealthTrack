from flask import Blueprint

# Initialize the 'client' blueprint
admin = Blueprint('admin', __name__)

# Import views from other modules (dashboard, orders)
from .doctor_routes import *
from .department_routes import *
from .resources_routes import *