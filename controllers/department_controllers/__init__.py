from flask import Blueprint

from controllers.constant.departmentPathConstant import DEPARTMENT

department = Blueprint(DEPARTMENT, __name__)

from .deshboard.dashboard_routes import *
from .department_inventory_routes import *