from flask import Blueprint

# Initialize the 'client' blueprint
idCard = Blueprint('idCard', __name__)

# Import views from other modules (dashboard, orders)
from .Generate_ID_Cards import *
