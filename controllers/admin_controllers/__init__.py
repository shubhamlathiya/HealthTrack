from flask import Blueprint

from ..constant.adminPathConstant import ADMIN

# Initialize the 'client' blueprint
admin = Blueprint(ADMIN, __name__)


# departments
from controllers.admin_controllers.department.department_routes import *
from controllers.admin_controllers.department.department_manage_heads_routes import *


from .dashboard_routes import *
from controllers.admin_controllers.operations.operation_routes import *

# appointment
from controllers.admin_controllers.appointment.appointment import *
from controllers.admin_controllers.appointment.treatment import *

# Staff
from controllers.admin_controllers.staff.staff_routes import *

# Room
from controllers.admin_controllers.room.rooom_routes import *
from controllers.admin_controllers.room.bad_routes import *

# ambulance
from controllers.admin_controllers.ambulance.ambulance_routes import *
from controllers.admin_controllers.ambulance.driver_routes import *
from controllers.admin_controllers.ambulance.ambulance_call_routes import *
from controllers.admin_controllers.ambulance.ambulance_category_routes import *
from controllers.admin_controllers.ambulance.ambulance_charge_item_routes import *

from controllers.admin_controllers.human_resources.human_resources_routes import *
from controllers.admin_controllers.accounts.accounts_routes import *

# noticeboard
from controllers.admin_controllers.noticeboard.noticeboard_routes import *

# inventory
from controllers.admin_controllers.inventory.inventory_routes import *
from controllers.admin_controllers.inventory.issued_item_routes import *

# Blood Bank
# from controllers.admin_controllers.blood_bank.blood_bank_issued_routes import *
from controllers.admin_controllers.blood_bank.blood_bank_inventory_routes import *
from controllers.admin_controllers.blood_bank.blood_bank_donor_routes import *
from controllers.admin_controllers.blood_bank.blood_requests import *
from controllers.admin_controllers.blood_bank.blood_bank_transfusions_routes import *

# insurance
from controllers.admin_controllers.insurance.coverage_types_routes import *
from controllers.admin_controllers.insurance.insurance_providers_routes import *
from controllers.admin_controllers.insurance.insurance_patient_routes import *
from controllers.admin_controllers.insurance.insurance_claims_routes import *

# pharmacy
from controllers.admin_controllers.pharmacy.medicine_categories_routes import *
from controllers.admin_controllers.pharmacy.medicine_companies_routes import *
from controllers.admin_controllers.pharmacy.pharmacy_routes import *
from controllers.admin_controllers.pharmacy.suppliers_routes import *
from controllers.admin_controllers.pharmacy.purchase_routes import *
from controllers.admin_controllers.pharmacy.sales_routes import *
# Records
from controllers.admin_controllers.records.death_records_routes import *
from controllers.admin_controllers.records.birth_records_routes import *

# Doctor
from controllers.admin_controllers.doctor.assign_department import *
from controllers.admin_controllers.doctor.shift_management import *
from controllers.admin_controllers.doctor.doctor_routes import *


@admin.route(GET_PATIENT + '/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    try:
        patient = Patient.query.filter_by(patient_id=patient_id, is_deleted=False).first()  # <-- fixed here

        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        users = User.query.filter_by(id=patient.user_id).first()
        return jsonify({
            'id': patient.id,
            'name': patient.first_name,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'email': users.email,
            'phone': patient.phone,
            'gender': patient.gender,
            'age': patient.age
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin.route('/api/patients/search', methods=['GET'])
def search_patients():
    """
    Searches for patients by name, custom patient ID, or phone number using 'q' query parameter.
    Example: /api/patients/search?q=John%20Doe
    Example: /api/patients/search?q=PID-001
    Example: /api/patients/search?q=9876543210
    """
    search_term = request.args.get('q', '').strip()

    if not search_term:
        # Return empty list if no search term provided, consistent with medicine search
        return jsonify([])

    try:
        # Search for patients matching the search term in various fields
        patients = Patient.query.filter(
            or_(
                Patient.first_name.ilike(f'%{search_term}%'),
                Patient.last_name.ilike(f'%{search_term}%'),
                (Patient.first_name + ' ' + Patient.last_name).ilike(f'%{search_term}%'),
                Patient.patient_id.ilike(f'%{search_term}%'), # Your custom patient_id
                Patient.phone.ilike(f'%{search_term}%') # Assuming phone can be searched
            ),
            Patient.is_deleted == False
        ).limit(10).all() # Limit results for performance

        results = []
        for patient in patients:
            # Eagerly load the user to avoid N+1 queries if you fetch many patients
            users = User.query.filter_by(id=patient.user_id).first()
            user_email = users.email if users else None

            results.append({
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}".strip(),
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'email': user_email,
                'phone': patient.phone,
                'gender': patient.gender,
                'age': patient.age
            })

        return jsonify(results), 200

    except Exception as e:
        # Log the full exception for debugging in a real app
        # current_app.logger.error(f"Error searching patients: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
