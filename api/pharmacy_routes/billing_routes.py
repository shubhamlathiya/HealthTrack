from datetime import datetime

from bson import ObjectId
from flask import jsonify

from api.pharmacy_routes import pharmacy
from config import mongo


@pharmacy.route('/billing', methods=['POST'])
def generate_billing():
    data = request.json
    patient_id = data.get('patient_id')
    medication_id = data.get('medication_id')
    quantity_dispensed = data.get('quantity_dispensed')
    medication_price = data.get('medication_price')

    if not all([patient_id, medication_id, quantity_dispensed, medication_price]):
        return jsonify({"error": "All fields are required"}), 400

    total_amount = quantity_dispensed * medication_price

    bill = {
        "patient_id": patient_id,
        "medication_id": medication_id,
        "quantity_dispensed": quantity_dispensed,
        "total_amount": total_amount,
        "billing_date": datetime.utcnow()
    }

    # Save the billing record
    billing_id = mongo.db.billing.insert_one(bill).inserted_id

    # Update patient's account with the bill
    mongo.db.patients.update_one(
        {"_id": ObjectId(patient_id)},
        {"$push": {"bills": str(billing_id)}}
    )

    return jsonify({"message": "Billing generated successfully", "billing_id": str(billing_id)}), 201

@pharmacy.route('/billing/<patient_id>', methods=['GET'])
def get_billing(patient_id):
    # Retrieve all billing records for the given patient
    bills = mongo.db.billing.find({"patient_id": patient_id})
    billing_list = [{"medication_id": bill['medication_id'], "total_amount": bill['total_amount'], "billing_date": bill['billing_date']} for bill in bills]

    return jsonify({"billing_records": billing_list}), 200
