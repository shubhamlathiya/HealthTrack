# 5. Patient Check-in/Check-out - POST /patients/checkin
from datetime import datetime

from bson import ObjectId
from flask import jsonify

from api.receptionist_routes import receptionist
from config import mongo


# 4. Insurance Verification - POST /patients/insurance/verify
@receptionist.route('/patients/insurance/verify', methods=['POST'])
def verify_insurance():
    data = request.get_json()
    patient_id = data.get('patient_id')
    insurance_provider = data.get('insurance_provider')
    insurance_policy_number = data.get('insurance_policy_number')

    if not all([patient_id, insurance_provider, insurance_policy_number]):
        return jsonify({"error": "All fields are required"}), 400

    # Update the patient's insurance details in the database
    mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$set": {
        "insurance_details": {
            "provider": insurance_provider,
            "policy_number": insurance_policy_number
        }
    }})

    return jsonify({"message": "Insurance details verified and updated successfully"}), 200



@receptionist.route('/patients/checkin', methods=['POST'])
def checkin_patient():
    data = request.get_json()
    patient_id = data.get('patient_id')

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    checkin_time = datetime.now()

    mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$set": {"checkin_time": checkin_time}})

    return jsonify({"message": f"Patient {patient_id} checked in successfully",
                    "checkin_time": checkin_time.strftime("%Y-%m-%dT%H:%M:%S")}), 200


# 6. Patient Check-out - POST /patients/checkout
@receptionist.route('/patients/checkout', methods=['POST'])
def checkout_patient():
    data = request.get_json()
    patient_id = data.get('patient_id')

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    checkout_time = datetime.now()

    mongo.db.patients.update_one({"_id": ObjectId(patient_id)}, {"$set": {"checkout_time": checkout_time}})

    return jsonify({"message": f"Patient {patient_id} checked out successfully",
                    "checkout_time": checkout_time.strftime("%Y-%m-%dT%H:%M:%S")}), 200


# 7. Generate Bill - POST /billing/generate
@receptionist.route('/billing/generate', methods=['POST'])
def generate_bill():
    data = request.get_json()
    patient_id = data.get('patient_id')
    consultation_fee = data.get('consultation_fee', 0)
    test_fees = data.get('test_fees', 0)
    medication_fees = data.get('medication_fees', 0)
    insurance_discount = data.get('insurance_discount', 0)

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    total_amount = consultation_fee + test_fees + medication_fees - insurance_discount

    bill = {
        "patient_id": ObjectId(patient_id),
        "consultation_fee": consultation_fee,
        "test_fees": test_fees,
        "medication_fees": medication_fees,
        "insurance_discount": insurance_discount,
        "total_amount": total_amount,
        "status": "Pending"
    }

    bill_id = mongo.db.billing.insert_one(bill).inserted_id
    return jsonify(
        {"message": "Bill generated successfully", "bill_id": str(bill_id), "total_amount": total_amount}), 201


# 8. Manage Cash Offline - POST /billing/offline-payment
@receptionist.route('/billing/offline-payment', methods=['POST'])
def offline_payment():
    data = request.get_json()
    bill_id = data.get('bill_id')
    amount_paid = data.get('amount_paid')

    if not all([bill_id, amount_paid]):
        return jsonify({"error": "Bill ID and Amount Paid are required"}), 400

    bill = mongo.db.billing.find_one({"_id": ObjectId(bill_id)})

    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    remaining_balance = bill["total_amount"] - amount_paid

    # Update the bill status to "Paid" if balance is zero or less
    if remaining_balance <= 0:
        mongo.db.billing.update_one({"_id": ObjectId(bill_id)}, {"$set": {"status": "Paid"}})

    return jsonify({
        "message": "Offline payment processed",
        "remaining_balance": remaining_balance,
        "status": "Paid" if remaining_balance <= 0 else "Pending"
    }), 200


# 9. Notifications (Appointment Reminders) - POST /notifications/send
@receptionist.route('/notifications/send', methods=['POST'])
def send_notification():
    data = request.get_json()
    patient_id = data.get('patient_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')

    if not all([patient_id, appointment_date, appointment_time]):
        return jsonify({"error": "All fields are required"}), 400

    # Send a reminder (For simplicity, just returning a message)
    reminder_message = f"Reminder: You have an appointment on {appointment_date} at {appointment_time}."

    return jsonify({"message": "Reminder sent successfully", "reminder": reminder_message}), 200
