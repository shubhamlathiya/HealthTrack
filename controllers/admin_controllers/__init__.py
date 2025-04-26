from flask import Blueprint

from ..constant.adminPathConstant import ADMIN

# Initialize the 'client' blueprint
admin = Blueprint(ADMIN, __name__)

from controllers.admin_controllers.department.department_routes import *
from .dashboard_routes import *
from .resources_routes import *
from .leave_management_routes import *
from .search_routes import *
from .patient_routes import *
from controllers.admin_controllers.operations.operation_routes import *

# Staff
from controllers.admin_controllers.staff.staff_routes import *

# Room
from controllers.admin_controllers.room.rooom_routes import *
from controllers.admin_controllers.room.bad_routes import *

from .ambulance_routes import *
from controllers.admin_controllers.human_resources.human_resources_routes import *
from controllers.admin_controllers.accounts.accounts_routes import *

# inventory
from controllers.admin_controllers.inventory.inventory_routes import *
from controllers.admin_controllers.inventory.issued_item_routes import *

# Blood Bank
from controllers.admin_controllers.blood_bank.blood_bank_issued_routes import *
from controllers.admin_controllers.blood_bank.blood_bank_stock_routes import *
from controllers.admin_controllers.blood_bank.blood_bank_donor_routes import *

# insurance
from controllers.admin_controllers.insurance.coverage_types_routes import *
from controllers.admin_controllers.insurance.insurance_providers_routes import *
from controllers.admin_controllers.insurance.insurance_patient_routes import *
from controllers.admin_controllers.insurance.insurance_claims_routes import *

# pharmacy
from controllers.admin_controllers.pharmacy.pharmacy_routes import *
from controllers.admin_controllers.pharmacy.medicine_categories_routes import *

# Records
from controllers.admin_controllers.records.death_records_routes import *
from controllers.admin_controllers.records.birth_records_routes import *

# Doctor
from controllers.admin_controllers.doctor.assign_department import *
from controllers.admin_controllers.doctor.shift_management import *
from controllers.admin_controllers.doctor.doctor_routes import *
