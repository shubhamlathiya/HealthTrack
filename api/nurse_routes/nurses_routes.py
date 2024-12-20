from datetime import datetime

from bson import ObjectId
from flask import jsonify,request

from api.nurse_routes import nurses
from config import mongo


@nurses.route('/add', methods=['POST'])
def add_nurse():
    data = request.get_json()
    nurse_id = data.get('nurse_id')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    shift_timings = data.get('shift_timings')

    if not all([nurse_id, name, email, phone, shift_timings]):
        return jsonify({"error": "All fields are required"}), 400

    nurse = {
        "nurse_id": nurse_id,
        "name": name,
        "email": email,
        "phone": phone,
        "shift_timings": shift_timings,
        "assigned_patients": []
    }

    mongo.db.nurses.insert_one(nurse)
    return jsonify({"message": "Nurse added successfully"}), 201


@nurses.route('/assign-patient', methods=['POST'])
def assign_patient():
    data = request.get_json()
    nurse_id = data.get('nurse_id')
    patient_id = data.get('patient_id')
    notes = data.get('notes', "")

    if not all([nurse_id, patient_id]):
        return jsonify({"error": "Nurse ID and Patient ID are required"}), 400

    # Update nurse record
    mongo.db.nurses.update_one(
        {"_id": ObjectId(nurse_id)},
        {"$addToSet": {"assigned_patients": ObjectId(patient_id)}}
    )

    # Add assignment log
    assignment = {
        "nurse_id": ObjectId(nurse_id),
        "patient_id": ObjectId(patient_id),
        "assigned_on": datetime.utcnow(),
        "unassigned_on": None,
        "notes": notes
    }
    mongo.db.assigned_patients.insert_one(assignment)

    return jsonify({"message": "Patient assigned to nurse successfully"}), 201


@nurses.route('/unassign-patient', methods=['POST'])
def unassign_patient():
    data = request.get_json()
    nurse_id = data.get('nurse_id')
    patient_id = data.get('patient_id')

    if not all([nurse_id, patient_id]):
        return jsonify({"error": "Nurse ID and Patient ID are required"}), 400

    # Update nurse record
    mongo.db.nurses.update_one(
        {"_id": ObjectId(nurse_id)},
        {"$pull": {"assigned_patients": ObjectId(patient_id)}}
    )

    # Update assignment log
    mongo.db.assigned_patients.update_one(
        {"nurse_id": ObjectId(nurse_id), "patient_id": ObjectId(patient_id), "unassigned_on": None},
        {"$set": {"unassigned_on": datetime.utcnow()}}
    )

    return jsonify({"message": "Patient unassigned from nurse successfully"}), 200


@nurses.route('/assigned-patients/<nurse_id>', methods=['GET'])
def view_assigned_patients(nurse_id):
    nurse = mongo.db.nurses.find_one({"_id": ObjectId(nurse_id)})
    if not nurse:
        return jsonify({"error": "Nurse not found"}), 404

    patient_ids = nurse.get("assigned_patients", [])
    patients = list(mongo.db.patients.find({"_id": {"$in": patient_ids}}, {"_id": 1, "name": 1, "age": 1, "condition": 1}))

    return jsonify({"nurse": nurse["name"], "assigned_patients": patients}), 200


@nurses.route('/patients/vitals', methods=['POST'])
def record_vitals():
    data = request.get_json()
    patient_id = data.get('patient_id')
    blood_pressure = data.get('blood_pressure')
    heart_rate = data.get('heart_rate')
    temperature = data.get('temperature')
    respiratory_rate = data.get('respiratory_rate')
    oxygen_saturation = data.get('oxygen_saturation')
    other_observations = data.get('other_observations', "")
    recorded_by = data.get('recorded_by')

    if not all([patient_id, blood_pressure, heart_rate, temperature, respiratory_rate, oxygen_saturation]):
        return jsonify({"error": "All vital signs are required"}), 400

    vital_record = {
        "patient_id": ObjectId(patient_id),
        "blood_pressure": blood_pressure,
        "heart_rate": heart_rate,
        "temperature": temperature,
        "respiratory_rate": respiratory_rate,
        "oxygen_saturation": oxygen_saturation,
        "other_observations": other_observations,
        "recorded_by": recorded_by,
        "recorded_at": datetime.utcnow()
    }

    mongo.db.vitals.insert_one(vital_record)
    return jsonify({"message": "Vitals recorded successfully"}), 201

@nurses.route('/patients/<patient_id>/vitals/latest', methods=['GET'])
def get_latest_vitals(patient_id):
    vitals = mongo.db.vitals.find_one({"patient_id": ObjectId(patient_id)}, sort=[("recorded_at", -1)])
    if not vitals:
        return jsonify({"error": "No vitals found for this patient"}), 404

    return jsonify({
        "patient_id": str(vitals["patient_id"]),
        "blood_pressure": vitals["blood_pressure"],
        "heart_rate": vitals["heart_rate"],
        "temperature": vitals["temperature"],
        "respiratory_rate": vitals["respiratory_rate"],
        "oxygen_saturation": vitals["oxygen_saturation"],
        "other_observations": vitals["other_observations"],
        "recorded_at": vitals["recorded_at"]
    }), 200


@nurses.route('/patients/<patient_id>/vitals/history', methods=['GET'])
def get_vitals_history(patient_id):
    vitals_history = list(mongo.db.vitals.find({"patient_id": ObjectId(patient_id)}).sort([("recorded_at", -1)]))

    if not vitals_history:
        return jsonify({"error": "No vitals history found for this patient"}), 404

    vitals_data = []
    for vital in vitals_history:
        vitals_data.append({
            "blood_pressure": vital["blood_pressure"],
            "heart_rate": vital["heart_rate"],
            "temperature": vital["temperature"],
            "respiratory_rate": vital["respiratory_rate"],
            "oxygen_saturation": vital["oxygen_saturation"],
            "other_observations": vital["other_observations"],
            "recorded_at": vital["recorded_at"]
        })

    return jsonify({"patient_id": patient_id, "vitals_history": vitals_data}), 200
