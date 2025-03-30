# 1. Add a new resource - POST /resources/add
from datetime import datetime

from bson import ObjectId
from flask import jsonify, request, render_template, redirect

from api.admin import admin
from config import mongo


@admin.route('/add-resources', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'GET':
        departments = list(mongo.db.departments.find())
        return render_template("admin/add_resource_templates.html", departments=departments)
    elif request.method == 'POST':

        # Extract fields
        resource_name = request.form.get('name')
        department_id = request.form.get('department_id')  # ObjectId reference
        quantity = request.form.get('quantity', 0)
        status = request.form.get('status', 'active')
        maintenance = request.form.get('maintenance', '')
        notes = request.form.get('notes', '')

        print(request.form)
        # Validate inputs
        if not resource_name or not department_id or int(quantity) < 0:
            return jsonify({"error": "Resource name, department_id, and a valid quantity are required"}), 400

        try:
            department_id = ObjectId(department_id)  # Convert to ObjectId
        except Exception as e:
            return jsonify({"error": f"Invalid department_id: {e}"}), 400

        # Prepare resource data
        resource = {
            "name": resource_name,
            "department_id": department_id,
            "quantity": quantity,
            "status": status,
            "maintenance": maintenance,
            "notes": notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Insert resource
        resource_id = mongo.db.resources.insert_one(resource).inserted_id
        return redirect('/admin/dashboard')
        # return redirect("/admin/dashboard"), 201


@admin.route('/get-resources', methods=['GET'], endpoint='get_resources')
def get_resources():
    # Use aggregation to join 'resources' with 'departments' to fetch the department name
    pipeline = [
        {
            '$lookup': {
                'from': 'departments',  # The collection to join (departments)
                'localField': 'department_id',  # The field in the resources collection
                'foreignField': '_id',  # The field in the departments collection
                'as': 'department_info'  # The field to store department info in the result
            }
        },
        {
            '$unwind': '$department_info'  # Flatten the department_info array
        },
        {
            '$addFields': {
                'department_name': '$department_info.name'  # Add the department name to the resource
            }
        },
        {
            '$project': {
                'department_info': 0  # Exclude the full department_info field
            }
        }
    ]

    # Execute the aggregation pipeline
    resources = mongo.db.resources.aggregate(pipeline)

    # Return the rendered template with resources
    return render_template("admin/view_resources_templates.html", resources=resources)

# # 2. Update resource details - PUT /resources/<resource_id>
# @admin.route('/resources/<resource_id>', methods=['PUT'])
# def update_resource(resource_id):
#     data = request.get_json()
#     updates = {}
#
#     if "resource_name" in data:
#         updates["resource_name"] = data["resource_name"]
#     if "resource_type" in data:
#         updates["resource_type"] = data["resource_type"]
#     if "quantity" in data:
#         updates["quantity"] = data["quantity"]
#     if "department" in data:
#         updates["department"] = data["department"]
#     if "status" in data:
#         updates["status"] = data["status"]
#     if "maintenance_flag" in data:
#         updates["maintenance_flag"] = data["maintenance_flag"]
#
#     if not updates:
#         return jsonify({"error": "No valid fields provided for update"}), 400
#
#     result = mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": updates})
#
#     if result.matched_count == 0:
#         return jsonify({"error": "Resource not found"}), 404
#
#     return jsonify({"message": "Resource updated successfully"}), 200
#
#
# # 3. Assign a resource to a staff or department - POST /resources/assign
# @admin.route('/resources/assign', methods=['POST'])
# def assign_resource():
#     data = request.get_json()
#     resource_id = data.get('resource_id')
#     assigned_to = data.get('assigned_to')  # Staff name or department
#     department = data.get('department')
#
#     if not resource_id or not assigned_to:
#         return jsonify({"error": "Resource ID and assigned_to fields are required"}), 400
#
#     resource = mongo.db.resources.find_one({"_id": ObjectId(resource_id)})
#
#     if not resource:
#         return jsonify({"error": "Resource not found"}), 404
#
#     mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": {
#         "assigned_to": assigned_to,
#         "department": department,
#         "status": "Assigned"
#     }})
#
#     return jsonify({"message": "Resource assigned successfully"}), 200
#
#
# # 4. Flag a resource for maintenance - POST /resources/flag-maintenance
# @admin.route('/resources/flag-maintenance', methods=['POST'])
# def flag_maintenance():
#     data = request.get_json()
#     resource_id = data.get('resource_id')
#
#     if not resource_id:
#         return jsonify({"error": "Resource ID is required"}), 400
#
#     resource = mongo.db.resources.find_one({"_id": ObjectId(resource_id)})
#
#     if not resource:
#         return jsonify({"error": "Resource not found"}), 404
#
#     mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": {"maintenance_flag": True, "status": "Under Maintenance"}})
#
#     return jsonify({"message": "Resource flagged for maintenance"}), 200
#
#
# # 5. List all resources - GET /resources
# @admin.route('/resources', methods=['GET'])
# def list_resources():
#     resources = mongo.db.resources.find()
#     resources_list = []
#
#     for resource in resources:
#         resource["_id"] = str(resource["_id"])  # Convert ObjectId to string for JSON serialization
#         resources_list.append(resource)
#
#     return jsonify(resources_list), 200
#

# 6. Delete a resource - DELETE /resources/<resource_id>
# @admin.route('/resources/<resource_id>', methods=['DELETE'])
# def delete_resource(resource_id):
#     result = mongo.db.resources.delete_one({"_id": ObjectId(resource_id)})
#
#     if result.deleted_count == 0:
#         return jsonify({"error": "Resource not found"}), 404
#
#     return jsonify({"message": "Resource deleted successfully"}), 200
