from flask import jsonify,request

from api.admin_routes import admin
from config import mongo


@admin.route('/add-department', methods=['POST'])
def add_department():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    head_of_department = data.get('head_of_department')

    if not all([name, description, head_of_department]):
        return jsonify({'error': 'All fields are required'}), 400

    # Check if the department already exists
    existing_department = mongo.db.departments.find_one({"name": name})
    if existing_department:
        return jsonify({'error': 'Department already exists'}), 400

    department_data = {
        "name": name,
        "description": description,
        "head_of_department": head_of_department
    }

    # Insert the department into the database
    result = mongo.db.departments.insert_one(department_data)

    # Convert ObjectId to string
    department_id = str(result.inserted_id)

    return jsonify({'message': 'Department created successfully', 'department_id': department_id}), 201
