from datetime import datetime

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
