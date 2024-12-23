from bson import ObjectId
from flask import jsonify,request

from api.pharmacy_routes import pharmacy
from config import mongo


@pharmacy.route('/add-inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    medication_name = data.get('medication_name')
    quantity = data.get('quantity')
    reorder_threshold = data.get('reorder_threshold')

    if not all([medication_name, quantity, reorder_threshold]):
        return jsonify({"error": "All fields are required"}), 400

    inventory_item = {
        "medication_name": medication_name,
        "quantity": quantity,
        "reorder_threshold": reorder_threshold
    }

    inventory_id = mongo.db.inventory.insert_one(inventory_item).inserted_id
    return jsonify({"message": "Medication added to inventory", "inventory_id": str(inventory_id)}), 201


@pharmacy.route('/inventory/<medication_id>', methods=['PUT'])
def update_inventory(medication_id):
    data = request.json
    quantity = data.get('quantity')

    if quantity is None:
        return jsonify({"error": "Quantity is required"}), 400

    mongo.db.inventory.update_one(
        {"_id": ObjectId(medication_id)},
        {"$set": {"quantity": quantity}}
    )

    return jsonify({"message": "Inventory updated successfully"}), 200


@pharmacy.route('/inventory', methods=['GET'])
def view_inventory():
    # Retrieve all inventory items
    inventory_items = mongo.db.inventory.find()
    inventory_list = [{"medication_name": item['medication_name'], "quantity": item['quantity']} for item in
                      inventory_items]

    return jsonify({"inventory": inventory_list}), 200
