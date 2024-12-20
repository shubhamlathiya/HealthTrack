# 1. Add a new resource - POST /resources/add
from bson import ObjectId
from flask import jsonify

from api.admin_routes import admin
from config import mongo


@admin.route('/resources/add', methods=['POST'])
def add_resource():
    data = request.get_json()
    resource_name = data.get('resource_name')
    resource_type = data.get('resource_type')  # e.g., Machine, Computer, Oxygen Bottle, etc.
    quantity = data.get('quantity', 0)
    department = data.get('department', None)  # Optional: Department where the resource is allocated.

    if not resource_name or not resource_type or quantity < 0:
        return jsonify({"error": "Resource name, type, and valid quantity are required"}), 400

    resource = {
        "resource_name": resource_name,
        "resource_type": resource_type,
        "quantity": quantity,
        "department": department,
        "status": "Available",  # Default status
        "assigned_to": None,  # Assigned staff or department (initially None)
        "maintenance_flag": False  # Initially not flagged for maintenance
    }

    resource_id = mongo.db.resources.insert_one(resource).inserted_id
    return jsonify({"message": "Resource added successfully", "resource_id": str(resource_id)}), 201


# 2. Update resource details - PUT /resources/<resource_id>
@admin.route('/resources/<resource_id>', methods=['PUT'])
def update_resource(resource_id):
    data = request.get_json()
    updates = {}

    if "resource_name" in data:
        updates["resource_name"] = data["resource_name"]
    if "resource_type" in data:
        updates["resource_type"] = data["resource_type"]
    if "quantity" in data:
        updates["quantity"] = data["quantity"]
    if "department" in data:
        updates["department"] = data["department"]
    if "status" in data:
        updates["status"] = data["status"]
    if "maintenance_flag" in data:
        updates["maintenance_flag"] = data["maintenance_flag"]

    if not updates:
        return jsonify({"error": "No valid fields provided for update"}), 400

    result = mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": updates})

    if result.matched_count == 0:
        return jsonify({"error": "Resource not found"}), 404

    return jsonify({"message": "Resource updated successfully"}), 200


# 3. Assign a resource to a staff or department - POST /resources/assign
@admin.route('/resources/assign', methods=['POST'])
def assign_resource():
    data = request.get_json()
    resource_id = data.get('resource_id')
    assigned_to = data.get('assigned_to')  # Staff name or department
    department = data.get('department')

    if not resource_id or not assigned_to:
        return jsonify({"error": "Resource ID and assigned_to fields are required"}), 400

    resource = mongo.db.resources.find_one({"_id": ObjectId(resource_id)})

    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": {
        "assigned_to": assigned_to,
        "department": department,
        "status": "Assigned"
    }})

    return jsonify({"message": "Resource assigned successfully"}), 200


# 4. Flag a resource for maintenance - POST /resources/flag-maintenance
@admin.route('/resources/flag-maintenance', methods=['POST'])
def flag_maintenance():
    data = request.get_json()
    resource_id = data.get('resource_id')

    if not resource_id:
        return jsonify({"error": "Resource ID is required"}), 400

    resource = mongo.db.resources.find_one({"_id": ObjectId(resource_id)})

    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    mongo.db.resources.update_one({"_id": ObjectId(resource_id)}, {"$set": {"maintenance_flag": True, "status": "Under Maintenance"}})

    return jsonify({"message": "Resource flagged for maintenance"}), 200


# 5. List all resources - GET /resources
@admin.route('/resources', methods=['GET'])
def list_resources():
    resources = mongo.db.resources.find()
    resources_list = []

    for resource in resources:
        resource["_id"] = str(resource["_id"])  # Convert ObjectId to string for JSON serialization
        resources_list.append(resource)

    return jsonify(resources_list), 200


# 6. Delete a resource - DELETE /resources/<resource_id>
@admin.route('/resources/<resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    result = mongo.db.resources.delete_one({"_id": ObjectId(resource_id)})

    if result.deleted_count == 0:
        return jsonify({"error": "Resource not found"}), 404

    return jsonify({"message": "Resource deleted successfully"}), 200
