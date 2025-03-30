from datetime import datetime

from bson import ObjectId
from flask import jsonify, request, render_template

from api.doctor import doctors
from config import mongo
from middleware.auth_middleware import token_required


@doctors.route('/generate-operation-request', methods=['GET', 'POST'], endpoint='generate_operation_request')
@token_required
def generate_operation_request(current_user):
    if request.method == 'GET':
        return render_template("doctor/generate_operation_request.html")
    elif request.method == 'POST':
        data = request.get_json()

        patient_id = data['patient_id']
        operation_type = data['operation_type']
        operation_time = data['operation_time']
        team_id = data['team']

        # Create the operation request data
        operation_request = {
            "doctor_id": ObjectId(current_user),
            "patient_id": patient_id,
            "operation_type": ObjectId(operation_type),
            "operation_time": operation_time,
            "team_id": ObjectId(team_id),
            "status": "pending",  # Initial status is 'pending'
            "created_at": datetime.utcnow(),
        }

        # print(operation_request)
        # Save the operation request to MongoDB
        mongo.db.operation_requests.insert_one(operation_request)

        return jsonify({"message": "Operation request submitted successfully!"}), 201


@doctors.route('/get-all-operation-request', methods=['GET'], endpoint='get_all_operation_request')
@token_required
def get_all_operation_request(current_user):
    # Aggregating operation requests
    operation_requests = list(mongo.db.operation_requests.aggregate([
        # Match the doctor_id to fetch the operation requests for the current doctor
        {
            '$match': {
                'doctor_id': ObjectId(current_user)
            }
        },
        # Lookup to join the users collection based on patient_id to get patient details
        {
            '$lookup': {
                'from': 'users',
                'localField': 'patient_id',  # patient_id in operation request
                'foreignField': 'user_id',  # user_id in the users collection
                'as': 'patient_details'
            }
        },
        # Lookup to join the operations collection to fetch operation details
        {
            '$lookup': {
                'from': 'operations',
                'localField': 'operation_type',  # operation_type in operation request
                'foreignField': '_id',  # _id field in operations collection
                'as': 'operation_details'
            }
        },
        # Lookup to join the teams collection to fetch team details
        {
            '$lookup': {
                'from': 'teams',
                'localField': 'team_id',  # team_id in operation request
                'foreignField': '_id',  # _id field in teams collection
                'as': 'team_details'
            }
        },
        # Optionally, unwind the arrays to flatten the data
        {
            '$unwind': {
                'path': '$patient_details',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$unwind': {
                'path': '$operation_details',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$unwind': {
                'path': '$team_details',
                'preserveNullAndEmptyArrays': True
            }
        },
        # For each team member, perform another lookup to fetch the member's full user details
        {
            '$lookup': {
                'from': 'users',
                'localField': 'team_details.members.user_id',  # each member's user_id in the team_details
                'foreignField': 'user_id',  # matching user_id in the users collection
                'as': 'team_details.members_details'  # This will contain the full user details of each member
            }
        }
    ]))

    # Modify the data structure to merge patient details, operation details, and team details into one object
    for request in operation_requests:
        # Extract patient details
        patient_data = request.get('patient_details', {})

        # Extract operation details
        operation_data = {
            "operation_type": request.get('operation_details', {}).get('operation_type', ''),
            "price": request.get('operation_details', {}).get('price', ''),
            "benefits": request.get('operation_details', {}).get('benefits', '')
        }

        # Extract team details
        team_data = request.get('team_details', {})
        team_members = team_data.get('members', [])
        team_members_details = request.get('team_details', {}).get('members_details', [])

        # Merge team members with their full user details
        merged_members = []
        for member, member_details in zip(team_members, team_members_details):
            merged_member = {
                "user_id": member.get('user_id'),
                "role": member.get('role'),
                "name": member_details.get('name', 'Name not available'),
                "email": member_details.get('email', 'Email not available'),
                "mobile_number": member_details.get('mobile_number', 'Phone not available')
            }
            merged_members.append(merged_member)

        # Merge all details into a single object
        merged_request = {
            "_id": request['_id'],
            "doctor_id": request['doctor_id'],
            "patient_id": request['patient_id'],
            "operation_time": request['operation_time'],
            "status": request['status'],
            "created_at": request['created_at'],
            "patient_details": patient_data,
            "operation_details": operation_data,
            "team_details": {
                "team_name": team_data.get('team_name', ''),
                "members": merged_members
            }
        }

        # Replace the original request with the merged request
        request.update(merged_request)

    # Debugging the result to check the structure
    print(operation_requests)

    # Return the results in JSON format
    return render_template("doctor/view_operation_request_templates.html", operation_requests=operation_requests)

