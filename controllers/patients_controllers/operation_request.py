from bson import ObjectId
from flask import jsonify, render_template, redirect

from controllers.patients_controllers import patients
from utils.config import mongo
from middleware.auth_middleware import token_required


@patients.route('/operation-request', methods=['GET'], endpoint='operation_request')
@token_required
def operation_request(current_user):
    # Fetch user data based on current_user
    user = mongo.db.users.find_one({"_id": ObjectId(current_user)})

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Use the correct field for the patient's ID (assuming it's 'user_id' in the user collection)
    patient_id = user.get('user_id')

    # Aggregating operation requests to fetch details from related collections (users, operations, and teams)
    operation_requests = list(mongo.db.operation_requests.aggregate([
        # Match the patient_id in the operation requests
        {"$match": {"patient_id": patient_id}},

        # Lookup to join the doctor details from the users collection
        {
            "$lookup": {
                "from": "users",  # Look for user in the 'users' collection
                "localField": "doctor_id",  # Match doctor_id from the operation request
                "foreignField": "_id",  # Match it with _id from the users collection
                "as": "doctor_details"  # Alias the result as 'doctor_details'
            }
        },

        # Lookup to join operation details from the operations collection
        {
            "$lookup": {
                "from": "operations",  # Look for operation in the 'operations' collection
                "localField": "operation_type",  # Match operation_type from the operation request
                "foreignField": "_id",  # Match it with _id from the operations collection
                "as": "operation_details"  # Alias the result as 'operation_details'
            }
        },

        # Lookup to join team details from the teams collection
        {
            "$lookup": {
                "from": "teams",  # Look for team in the 'teams' collection
                "localField": "team_id",  # Match team_id from the operation request
                "foreignField": "_id",  # Match it with _id from the teams collection
                "as": "team_details"  # Alias the result as 'team_details'
            }
        },

        # Unwind the arrays to flatten the results (optional, depending on your needs)
        {
            "$unwind": {
                "path": "$doctor_details",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$unwind": {
                "path": "$operation_details",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$unwind": {
                "path": "$team_details",
                "preserveNullAndEmptyArrays": True
            }
        }
    ]))

    # print(operation_requests)
    # Return the aggregated result
    return render_template("patient/view_operation_requests.html", operation_requests=operation_requests)


@patients.route('/accept-operation/<operation_id>', methods=['GET'], endpoint='accept-operation')
@token_required
def accept_operation(current_user, operation_id):
    # Find the operation request in the database
    operation_request = mongo.db.operation_requests.find_one({"_id": ObjectId(operation_id)})

    if not operation_request:
        # flash("Operation request not found!", "error")
        return redirect('/patient/operation_request')

    # Update the operation request status to 'accepted'
    mongo.db.operation_requests.update_one(
        {"_id": ObjectId(operation_id)},
        {"$set": {"status": "accepted"}}
    )

    # Redirect back to the patient's operation requests page
    return redirect('/patient/operation_request')


@patients.route('/reject-operation/<operation_id>', methods=['GET'], endpoint='reject-operation')
@token_required
def accept_operation(current_user, operation_id):
    # Find the operation request in the database
    operation_request = mongo.db.operation_requests.find_one({"_id": ObjectId(operation_id)})

    if not operation_request:
        # flash("Operation request not found!", "error")
        return redirect('/patient/operation_request')

    # Update the operation request status to 'accepted'
    mongo.db.operation_requests.update_one(
        {"_id": ObjectId(operation_id)},
        {"$set": {"status": "rejected"}}
    )

    # Redirect back to the patient's operation requests page
    return redirect('/patient/operation_request')
