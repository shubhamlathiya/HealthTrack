from datetime import datetime
from bson import ObjectId
from flask import jsonify, request, render_template

from api.admin import admin
from config import mongo
from middleware.auth_middleware import token_required


# Leave Application Schema:
# {
#   "_id": ObjectId("648b7b1a2d2a6a2a3f1e0c20"),
#   "user_id": ObjectId("648b7b1a2d2a6a2a3f1e0c13"),
#   "leave_type": "Vacation",
#   "start_date": ISODate("2024-12-25T00:00:00Z"),
#   "end_date": ISODate("2024-12-29T00:00:00Z"),
#   "reason": "Family vacation",
#   "status": "Approved",
#   "notes": "Approved by HR"
# }

@admin.route('/staff/leave/apply', methods=['GET', 'POST'], endpoint='apply_leave')
@token_required
def apply_leave(current_user):
    if request.method == 'GET':
        return render_template("admin/apply_for_leave.html")
    elif request.method == 'POST':

        data = request.get_json()

        # Extract data from the request
        leave_type = data.get("leave_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        reason = data.get("reason")
        notes = data.get("notes", "")  # Optional field for additional notes

        # Validate required fields
        if not all([leave_type, start_date, end_date, reason]):
            return jsonify({"error": "All fields are required"}), 400

        # Convert the start and end dates to datetime objects
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # Construct the leave application document
        leave_application = {
            "user_id": ObjectId(current_user),  # We use user_id instead of staff_id based on your schema
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "status": "Pending",  # Default status is "Pending"
            "notes": notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Insert the leave application into the database
        mongo.db.leave_applications.insert_one(leave_application)

        return jsonify({"message": "Leave application submitted successfully"}), 201


@admin.route('/staff/leave/review', methods=['PATCH'])
def review_leave():
    data = request.get_json()

    # Extract leave ID and review data
    leave_id = data.get("leave_id")
    status = data.get("status")
    admin_notes = data.get("admin_notes", "")

    # Validate input data
    if not leave_id or status not in ["Approved", "Rejected"]:
        return jsonify({"error": "Invalid data"}), 400

    # Find the leave application by its ID
    leave = mongo.db.leave_applications.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        return jsonify({"error": "Leave application not found"}), 404

    # Update the leave application with the review status and admin notes
    mongo.db.leave_applications.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"status": status, "notes": admin_notes}}  # Updated "notes" as per schema
    )

    return jsonify({"message": "Leave application reviewed successfully"}), 200


@admin.route('/leave/applications', methods=['GET'])
def get_leave_applications():
    # Define the aggregation pipeline
    pipeline = [
        {
            '$lookup': {
                'from': 'users',  # The collection to join (users)
                'localField': 'user_id',  # The field in the leave_applications collection
                'foreignField': '_id',  # The field in the users collection
                'as': 'user_info'  # The field to store user info in the result
            }
        },
        {
            '$unwind': '$user_info'  # Flatten the user_info array
        },
        {
            '$addFields': {
                'user_name': '$user_info.name',  # Assuming 'name' is the field in the users collection
                'user_email': '$user_info.email'  # Assuming 'email' is the field in the users collection
            }
        },
        {
            '$project': {
                'user_info': 0  # Exclude the full user_info field
            }
        }
    ]

    # Execute the aggregation pipeline
    applications = mongo.db.leave_applications.aggregate(pipeline)

    # Convert the applications cursor to a list for JSON response
    applications_list = list(applications)

    print(applications_list)
    # Format the applications to convert ObjectId to string for JSON compatibility
    for app in applications_list:
        app["_id"] = str(app["_id"])
        app["user_id"] = str(app["user_id"])

    # return jsonify(applications_list), 200
    return render_template("admin/view_leave_templates.html", applications=applications_list)
