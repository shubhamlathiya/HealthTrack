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
# @admin.route('/add-staff', methods=['GET', 'POST'], endpoint='add_staff')
# def add_staff():
#     if request.method == 'POST':
#         try:
#             # Get form data
#             name = request.form['name']
#             email = request.form['email']
#             password = request.form['password']  # Ensure to hash the password before saving
#             age = int(request.form['age'])
#             address = request.form['address']
#             mobile_number = request.form['mobile_number']
#             gender = request.form['gender']
#             dob = datetime.strptime(request.form['dob'], "%Y-%m-%d")
#             department_id = request.form['department_id']
#             specialization = request.form['specialization']
#             start_time = request.form['start_time']
#             end_time = request.form['end_time']
#
#             current_date = datetime.utcnow()
#             year = current_date.year
#             month = f"{current_date.month:02d}"
#             day = f"{current_date.day:02d}"
#
#             # Generate random 2-digit number
#             random_digits = random.randint(10, 99)
#
#             unique_patient_id = f"{year}{month}{day}{random_digits}"
#
#             hashed_password = generate_password_hash(password)
#
#             # Insert doctor data
#             doctor_data = {
#                 "user_id": unique_patient_id,  # Generate a user_id
#                 "name": name,
#                 "email": email,
#                 "password": hashed_password,  # Hash password before saving
#                 "age": age,
#                 "address": address,
#                 "mobile_number": mobile_number,
#                 "gender": gender,
#                 "dob": dob,
#                 "role": "staff",
#                 "status": True,
#                 "created_at": datetime.utcnow(),
#                 "updated_at": datetime.utcnow()
#             }
#             doctor_result = mongo.db.users.insert_one(doctor_data)
#             doctor_id = doctor_result.inserted_id
#
#             # Insert department data
#             department_data = {
#                 "user_id": doctor_id,  # Link the department to the doctor
#                 "department_id": ObjectId(department_id),
#                 "specialization": specialization,
#                 "shift_schedule": [
#                     {"start_time": start_time, "end_time": end_time}
#                 ]
#             }
#             department_result = mongo.db.DoctorsAndStaff.insert_one(department_data)
#
#             # patient_id = mongo.db.users.insert_one(patient).inserted_id
#
#             verification_link = f"http://localhost:5000/auth/verify-email/{str(doctor_id)}"
#             send_email('Verify Your Email', email, verification_link)
#
#             # Redirect to success page or show success message
#             return redirect("/admin/dashboard")
#
#         except Exception as e:
#             return jsonify({
#                 "message": "Error adding doctor and department",
#                 "error": str(e)
#             }), 500
#     elif request.method == 'GET':
#
#         departments = list(mongo.db.departments.find())
#
#         return render_template('admin_templates/staff/add_staff_templates.html', departments=departments)
#
#
# @admin.route('/get-all-staff', methods=['GET'],endpoint='get_staff')
# def get_all_staff():
#     try:
#         # Define the aggregation pipeline to get doctors and their details
#         pipeline = [
#             {
#                 "$match": {
#                     "role": "staff"  # Ensure that only doctors are fetched from the users collection
#                 }
#             },
#             {
#                 "$lookup": {
#                     "from": "DoctorsAndStaff",  # The collection to join with
#                     "localField": "_id",  # Field in the users collection to match with
#                     "foreignField": "user_id",  # Field in the DoctorsAndStaff collection to match with
#                     "as": "doctor_details"  # The alias for the joined data
#                 }
#             },
#             {
#                 "$unwind": "$doctor_details"  # Flatten the joined data
#             },
#             {
#                 "$project": {
#                     "user_id": 1,
#                     "name": 1,
#                     "specialization": "$doctor_details.specialization",
#                     "email": 1,
#                     "mobile_number": 1,
#                     "gender": 1,
#                     "created_at": 1,
#                     "status": 1,
#
#                 }
#             }
#         ]
#
#         # Execute the aggregation query
#         staffs = list(mongo.db.users.aggregate(pipeline))
#
#         # Convert _id to string for JSON serialization
#         for staff in staffs:
#             if '_id' in staff:
#                 staff['_id'] = str(staff['_id'])  # Convert ObjectId to string
#
#         # print(doctors)
#         # Return the result as JSON (corrected to return the list directly)
#         return jsonify(staffs), 200
#
#     except Exception as e:
#         print(f"Error fetching doctors: {e}")
#         return jsonify({"error": "Unable to fetch doctors"}), 500
#
#
# @admin.route('/view-staff', methods=['GET'], endpoint="view_staff")
# def view_all_staffs():
#     try:
#         # Define the aggregation pipeline to get doctors and their details
#         pipeline = [
#             {
#                 "$match": {
#                     "role": "staff"  # Ensure that only doctors are fetched from the users collection
#                 }
#             },
#             {
#                 "$lookup": {
#                     "from": "DoctorsAndStaff",  # The collection to join with
#                     "localField": "_id",  # Field in the users collection to match with
#                     "foreignField": "user_id",  # Field in the DoctorsAndStaff collection to match with
#                     "as": "doctor_details"  # The alias for the joined data
#                 }
#             },
#             {
#                 "$unwind": "$doctor_details"  # Flatten the joined data
#             },
#             {
#                 "$project": {
#                     "user_id": 1,
#                     "name": 1,
#                     "specialization": "$doctor_details.specialization",
#                     "email": 1,
#                     "mobile_number": 1,
#                     "gender": 1,
#                     "created_at": 1,
#                     "status": 1,
#
#                 }
#             }
#         ]
#
#         # Execute the aggregation query
#         staffs = list(mongo.db.users.aggregate(pipeline))
#
#         # print(staffs)
#
#         return render_template("admin_templates/staff/view_staff_templates.html", staffs=staffs)
#
#     except Exception as e:
#         print(f"Error fetching doctors: {e}")
#         return jsonify({"error": "Unable to fetch doctors"}), 500
