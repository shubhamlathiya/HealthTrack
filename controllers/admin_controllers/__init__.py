from flask import Blueprint

from ..constant.PathConstant import ADMIN

# Initialize the 'client' blueprint
admin = Blueprint(ADMIN, __name__)

from .department_routes import *
from .doctor_routes import *
from .dashboard_routes import *
from .resources_routes import *
from .leave_management_routes import *
from .search_routes import *
from .patient_routes import *
from .operation_routes import *
from .staff_routes import *
from .rooom_routes import *
from .ambulance_routes import *
from .human_resources_routes import *
from .accounts_routes import *
from .blood_bank_routes import *
from .insurance_routes import *
from .pharmacy_routes import *
from .records_routes import *

@admin.route('/user-status', methods=['POST'],endpoint='userStatus')
@token_required
def user_status(current_user):
    data = request.get_json()

    user_id = data.get('user_id')  # User ID passed from the client-side
    new_status = data.get('status')  # New status (true/false)

    if user_id and new_status:
        # Update the user's status in the database
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'status': new_status}}
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Status update failed'})
    return jsonify({'success': False, 'message': 'Invalid request'}), 400
