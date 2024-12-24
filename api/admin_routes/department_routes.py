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


@admin.route('/get-departments', methods=['GET'])
def get_departments():
    name = request.args.get('name')  # Retrieve query parameter 'name' if provided

    if name:
        # Fetch the department by name
        department = mongo.db.departments.find_one({"name": name})
        if not department:
            return jsonify({'error': 'Department not found'}), 404

        # Convert ObjectId and format response
        department['_id'] = str(department['_id'])
        return jsonify({'department': department}), 200

    # Fetch all departments
    departments = mongo.db.departments.find()
    departments_list = []
    for department in departments:
        department['_id'] = str(department['_id'])  # Convert ObjectId to string
        departments_list.append(department)

    return jsonify({'departments': departments_list}), 200
