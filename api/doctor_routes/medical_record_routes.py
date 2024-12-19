# from bson import ObjectId
# from flask import jsonify
#
# from api.doctor_routes import doctors
# from flask import request
#
# from config import mongo


# @doctors.route('/add-medical-record', methods=['POST'])
# def add_medical_record():
#     data = request.get_json()
#     patient_id = data.get('patient_id')
#     treatment_date = data.get('treatment_date')
#     diagnosis = data.get('diagnosis')
#     test_results = data.get('test_results', [])
#     prescriptions = data.get('prescriptions', [])
#     doctor = data.get('doctor')
#
#     if not all([patient_id, treatment_date, diagnosis, doctor]):
#         return jsonify({"error": "All fields are required"}), 400
#
#     # Create a new record
#     new_record = {
#         "record_id": str(uuid.uuid4()),
#         "treatment_date": treatment_date,
#         "diagnosis": diagnosis,
#         "test_results": test_results,
#         "prescriptions": prescriptions,
#         "doctor": doctor
#     }
#
#     # Add the record to the patient's medical records
#     mongo.db.patients.update_one(
#         {"_id": ObjectId(patient_id)},
#         {"$push": {"medical_records": new_record}}
#     )
#
#     return jsonify({"message": "Medical record added successfully"}), 200
