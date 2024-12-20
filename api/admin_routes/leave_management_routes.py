from datetime import datetime

from bson import ObjectId
from flask import jsonify

from api.admin_routes import admin
from config import mongo


# {
#   "_id": { "$oid": "leave_application_id" },
#   "staff_id": { "$oid": "staff_unique_id" },
#   "leave_type": "Annual",
#   "start_date": { "$date": "2024-12-22" },
#   "end_date": { "$date": "2024-12-25" },
#   "reason": "Family vacation",
#   "status": "Pending", // "Approved", "Rejected"
#   "admin_notes": "Please ensure backup coverage."
# }

@admin.route('/staff/leave/apply', methods=['POST'])
def apply_leave():
    data = request.get_json()
    staff_id = data.get("staff_id")
    leave_type = data.get("leave_type")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    reason = data.get("reason")

    if not all([staff_id, leave_type, start_date, end_date, reason]):
        return jsonify({"error": "All fields are required"}), 400

    leave_application = {
        "staff_id": ObjectId(staff_id),
        "leave_type": leave_type,
        "start_date": datetime.strptime(start_date, "%Y-%m-%d"),
        "end_date": datetime.strptime(end_date, "%Y-%m-%d"),
        "reason": reason,
        "status": "Pending",
        "admin_notes": ""
    }

    mongo.db.leave_applications.insert_one(leave_application)
    return jsonify({"message": "Leave application submitted successfully"}), 201


@admin.route('/admin/leave/review', methods=['PATCH'])
def review_leave():
    data = request.get_json()
    leave_id = data.get("leave_id")
    status = data.get("status")
    admin_notes = data.get("admin_notes", "")

    if not leave_id or status not in ["Approved", "Rejected"]:
        return jsonify({"error": "Invalid data"}), 400

    leave = mongo.db.leave_applications.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        return jsonify({"error": "Leave application not found"}), 404

    mongo.db.leave_applications.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {"status": status, "admin_notes": admin_notes}}
    )
    return jsonify({"message": "Leave application reviewed successfully"}), 200


@admin.route('/admin/leave/applications', methods=['GET'])
def get_leave_applications():
    applications = list(mongo.db.leave_applications.find())
    for app in applications:
        app["_id"] = str(app["_id"])
        app["staff_id"] = str(app["staff_id"])
    return jsonify(applications), 200
