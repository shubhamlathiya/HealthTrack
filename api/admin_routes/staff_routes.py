from datetime import datetime

from bson import ObjectId
from werkzeug.security import generate_password_hash

from api.admin_routes import admin
from flask import jsonify,request

from config import mongo


@admin.route('/add-staff', methods=['POST'])
def add_staff():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    department = data.get("department")
    contact_number = data.get("contact_number")

    # Validate required fields
    if not all([name, email, password, role, department, contact_number]):
        return jsonify({"error": "All fields are required"}), 400

    # Check if the staff member already exists
    existing_staff = mongo.db.staff.find_one({"email": email})
    if existing_staff:
        return jsonify({"error": "Staff member with this email already exists"}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Create the staff document
    staff = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "role": role,
        "department": department,
        "contact_number": contact_number,
        "date_joined": datetime.utcnow()
    }

    # Insert into the database
    staff_id = mongo.db.staff.insert_one(staff).inserted_id

    return jsonify({"message": "Staff member added successfully", "staff_id": str(staff_id)}), 201


@admin.route('/get-staff/<staff_id>', methods=['GET'])
def get_staff(staff_id):
    # Retrieve the staff member by their staff_id
    staff = mongo.db.staff.find_one({"_id": ObjectId(staff_id)})

    # Check if staff exists
    if not staff:
        return jsonify({"error": "Staff member not found"}), 404

    # Remove sensitive information such as password before sending response
    staff_data = {
        "name": staff["name"],
        "email": staff["email"],
        "role": staff["role"],
        "department": staff["department"],
        "contact_number": staff["contact_number"],
        "date_joined": staff["date_joined"]
    }

    return jsonify({"staff": staff_data}), 200


@admin.route('/get-all-staff', methods=['GET'])
def get_all_staff():
    try:
        # Fetch all staff members from the database
        staff_list = mongo.db.staff.find()

        # If no staff members are found
        if not staff_list:
            return jsonify({"error": "No staff members found"}), 404

        # Prepare a list of staff details to return (without sensitive information like password)
        staff_data = []
        for staff in staff_list:
            staff_data.append({
                "staff_id": str(staff["_id"]),
                "name": staff["name"],
                "email": staff["email"],
                "role": staff["role"],
                "department": staff["department"],
                "contact_number": staff["contact_number"],
                "date_joined": staff["date_joined"]
            })

        return jsonify({"staff": staff_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
