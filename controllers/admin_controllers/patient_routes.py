# from datetime import datetime
# import random
#
# from bson import ObjectId
# from flask import redirect, jsonify, render_template, request
# from werkzeug.security import generate_password_hash
#
# from controllers.admin_controllers import admin
# from utils.config import mongo
# from utils.email_utils import send_email
# from middleware.auth_middleware import token_required
#
#
# @admin.route('/view-patients', methods=['GET'])
# def view_all_patients():
#     try:
#         # Define the aggregation pipeline to get doctors and their details
#         pipeline = [
#             {
#                 "$match": {
#                     "role": "patient"  # Ensure that only doctors are fetched from the users collection
#                 }
#             },
#             {
#                 "$project": {
#                     "user_id": 1,
#                     "name": 1,
#                     "email": 1,
#                     "mobile_number": 1,
#                     "gender": 1,
#                     "created_at": 1,
#                     "status": 1,
#                 }
#             }
#         ]
#
#         # Execute the aggregation query
#         patient = list(mongo.db.users.aggregate(pipeline))
#
#         # print(doctors)
#
#         return render_template("admin_templates/patients/view_patient_templates.html", patients=patient)
#
#     except Exception as e:
#         print(f"Error fetching doctors: {e}")
#         return jsonify({"error": "Unable to fetch doctors"}), 500
#
# # Success page
# # @admin.route('/success')
# # def success():
# #     return "<h1>Doctor and Department added successfully!</h1>"
