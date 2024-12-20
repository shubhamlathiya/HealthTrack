# 1. Automated Staff Scheduling - POST /staff/schedule
from datetime import datetime

from bson import ObjectId
from flask import jsonify,request

from api.staff_routes import staffs
from config import mongo


@staffs.route('/staff/schedule', methods=['POST'])
def create_schedule():
    data = request.get_json()
    staff_id = data.get('staff_id')
    department = data.get('department')
    shift_start_time = data.get('shift_start_time')
    shift_end_time = data.get('shift_end_time')
    assigned_role = data.get('assigned_role')
    status = data.get('status', "Scheduled")

    if not all([staff_id, department, shift_start_time, shift_end_time, assigned_role]):
        return jsonify({"error": "All fields are required"}), 400

    # Create schedule document
    schedule = {
        "staff_id": ObjectId(staff_id),
        "department": department,
        "shift_start_time": datetime.strptime(shift_start_time, "%Y-%m-%dT%H:%M:%S"),
        "shift_end_time": datetime.strptime(shift_end_time, "%Y-%m-%dT%H:%M:%S"),
        "assigned_role": assigned_role,
        "status": status
    }

    # Insert schedule into the database
    schedule_id = mongo.db.staff_schedules.insert_one(schedule).inserted_id
    return jsonify({"message": "Staff scheduled successfully", "schedule_id": str(schedule_id)}), 201

# 2. View Staff Schedule - GET /staff/schedule/{staff_id}
@staffs.route('/staff/schedule/<staff_id>', methods=['GET'])
def get_schedule(staff_id):
    schedules = mongo.db.staff_schedules.find({"staff_id": ObjectId(staff_id)})
    return jsonify([{
        "schedule_id": str(schedule["_id"]),
        "staff_id": serialize_objectid(schedule["staff_id"]),
        "department": schedule["department"],
        "shift_start_time": schedule["shift_start_time"].strftime("%Y-%m-%dT%H:%M:%S"),
        "shift_end_time": schedule["shift_end_time"].strftime("%Y-%m-%dT%H:%M:%S"),
        "assigned_role": schedule["assigned_role"],
        "status": schedule["status"]
    } for schedule in schedules])

# 3. Add Employee Record - POST /staff/record
@staffs.route('/staff/record', methods=['POST'])
def add_employee_record():
    data = request.get_json()
    staff_id = data.get('staff_id')
    name = data.get('name')
    role = data.get('role')
    department = data.get('department')
    qualifications = data.get('qualifications')
    certifications = data.get('certifications')
    performance = data.get('performance')

    if not all([staff_id, name, role, department, qualifications, certifications, performance]):
        return jsonify({"error": "All fields are required"}), 400

    # Create employee record
    employee_record = {
        "staff_id": ObjectId(staff_id),
        "name": name,
        "role": role,
        "department": department,
        "qualifications": qualifications,
        "certifications": certifications,
        "performance": performance
    }

    # Insert employee record into the database
    mongo.db.staff_records.insert_one(employee_record)
    return jsonify({"message": "Employee record added successfully"}), 201

# 4. View Employee Record - GET /staff/record/{staff_id}
@staffs.route('/staff/record/<staff_id>', methods=['GET'])
def get_employee_record(staff_id):
    employee = mongo.db.staff_records.find_one({"staff_id": ObjectId(staff_id)})

    if employee:
        return jsonify({
            "staff_id": serialize_objectid(employee["_id"]),
            "name": employee["name"],
            "role": employee["role"],
            "department": employee["department"],
            "qualifications": employee["qualifications"],
            "certifications": employee["certifications"],
            "performance": employee["performance"]
        })
    else:
        return jsonify({"error": "Employee record not found"}), 404

# 5. Add Training Record - POST /staff/training
@staffs.route('/staff/training', methods=['POST'])
def add_training_record():
    data = request.get_json()
    staff_id = data.get('staff_id')
    training_name = data.get('training_name')
    completion_date = data.get('completion_date')
    status = data.get('status')
    certification_validity = data.get('certification_validity')

    if not all([staff_id, training_name, completion_date, status, certification_validity]):
        return jsonify({"error": "All fields are required"}), 400

    # Create training record
    training_record = {
        "staff_id": ObjectId(staff_id),
        "training_name": training_name,
        "completion_date": datetime.strptime(completion_date, "%Y-%m-%d"),
        "status": status,
        "certification_validity": datetime.strptime(certification_validity, "%Y-%m-%d")
    }

    # Insert training record into the database
    mongo.db.staff_trainings.insert_one(training_record)
    return jsonify({"message": "Training record added successfully"}), 201

# 6. Get Training Record - GET /staff/training/{staff_id}
@staffs.route('/staff/training/<staff_id>', methods=['GET'])
def get_training_record(staff_id):
    trainings = mongo.db.staff_trainings.find({"staff_id": ObjectId(staff_id)})
    return jsonify([{
        "training_name": training["training_name"],
        "completion_date": training["completion_date"].strftime("%Y-%m-%d"),
        "status": training["status"],
        "certification_validity": training["certification_validity"].strftime("%Y-%m-%d")
    } for training in trainings])

# 7. Check Compliance - GET /staff/compliance/{staff_id}
@staffs.route('/staff/compliance/<staff_id>', methods=['GET'])
def check_compliance(staff_id):
    employee = mongo.db.staff_records.find_one({"staff_id": ObjectId(staff_id)})
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    compliant = True
    missing_certifications = []
    required_certifications = ["ACLS", "BLS"]  # Example certifications

    for cert in required_certifications:
        if cert not in employee["certifications"]:
            missing_certifications.append(cert)

    compliance_details = {
        "required_certifications": required_certifications,
        "missing_certifications": missing_certifications,
        "training_status": "Up-to-date" if not missing_certifications else "Outdated"
    }

    return jsonify({
        "staff_id": serialize_objectid(employee["_id"]),
        "compliant": compliant,
        "compliance_details": compliance_details
    })

# Helper function to serialize ObjectId to string
def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj