# from bson import ObjectId
# from flask import render_template, jsonify, request
#
# from controllers.admin_controllers import admin
# from utils.config import mongo
# from middleware.auth_middleware import token_required
#
#
# def objectid_to_str(obj):
#     if isinstance(obj, ObjectId):
#         return str(obj)
#     elif isinstance(obj, dict):
#         return {k: objectid_to_str(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [objectid_to_str(v) for v in obj]
#     else:
#         return obj
#
#
# @admin.route('/search', methods=['GET', 'POST'],endpoint='search')
# @token_required
# def search(current_user):
#     if request.method == 'POST':
#         user_id = request.form.get('user_id')  # Get user_id from form input
#
#         if not user_id:
#             return jsonify({"error": "user_id is required"}), 400
#
#         try:
#             # Fetch user details
#             user = mongo.db.users.find_one({"user_id": user_id})
#             if not user:
#                 return jsonify({"error": "User not found"}), 404
#
#             # Fetch appointments for the given user
#             appointments = list(mongo.db.appointments.find({"patient_id": ObjectId(user['_id'])}))
#
#             # Fetch uploaded test reports for the given user
#             uploaded_test_reports = list(mongo.db.uploaded_test_reports.find({"user_id": ObjectId(user['_id'])}))
#
#             # Fetch prescriptions related to the user's appointments
#             appointment_ids = [a["_id"] for a in appointments]
#             prescriptions = list(mongo.db.prescriptions.find({"appointment_id": {"$in": appointment_ids}}))
#
#             # Prepare the response data
#             patient_data = {
#                 "user": {
#                     "_id": str(user["_id"]),
#                     "name": user.get("name"),
#                     "email": user.get("email"),
#                     "age": user.get("age"),
#                     "address": user.get("address"),
#                 },
#                 "appointments": appointments,
#                 "uploadedTestReports": uploaded_test_reports,
#                 "prescriptions": prescriptions
#             }
#
#             # print(patient_data)
#             # Return the search result in the template
#             return render_template('admin_templates/search_page.html', patient_data=patient_data)
#         except Exception as e:
#             print(f"Error: {e}")
#             return jsonify({"error": "Internal server error"}), 500
#     return render_template('admin_templates/search_page.html')
#
#
# # @admin.route('/get-patient-details/<patient_id>', methods=['GET'])
# # @token_required
# # def get_patient_details(current_user):
# #     return  "hy"
#     # try:
#     #     # Fetch user details by patient_id (which corresponds to user_id in the database)
#     #     user = mongo.db.users.find_one({"user_id": patient_id})
#     #
#     #     if not user:
#     #         return jsonify({"error": "User not found"}), 404
#     #
#     #     # Fetch appointments for the given user
#     #     appointments = list(mongo.db.appointments.find({"patient_id": ObjectId(user['_id'])}))
#     #
#     #     # Fetch uploaded test reports for the given user
#     #     uploaded_test_reports = list(mongo.db.uploaded_test_reports.find({"user_id": ObjectId(user['_id'])}))
#     #
#     #     # Fetch prescriptions related to the user's appointments
#     #     appointment_ids = [a["_id"] for a in appointments]
#     #     prescriptions = list(mongo.db.prescriptions.find({"appointment_id": {"$in": appointment_ids}}))
#     #
#     #     # Prepare the response data
#     #     patient_data = {
#     #         "user": {
#     #             "_id": str(user["_id"]),
#     #             "name": user.get("name"),
#     #             "email": user.get("email"),
#     #             "age": user.get("age"),
#     #             "address": user.get("address"),
#     #         },
#     #         "appointments": objectid_to_str(appointments),
#     #         "uploadedTestReports": objectid_to_str(uploaded_test_reports),
#     #         "prescriptions": objectid_to_str(prescriptions),
#     #     }
#     #
#     #     # Return the data in JSON format
#     #     return jsonify(patient_data)
#     #
#     # except Exception as e:
#     #     print(f"Error: {e}")
#     #     return jsonify({"error": "Internal server error"}), 500