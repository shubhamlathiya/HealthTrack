from flask import Blueprint

from ..constant.adminPathConstant import AUTH

# Initialize the 'client' blueprint
auth = Blueprint(AUTH, __name__)

# Import views from other modules (dashboard, orders)
from .auth_login_routes import *
from .auth_register_routes import *
from .forgot_password_routes import *