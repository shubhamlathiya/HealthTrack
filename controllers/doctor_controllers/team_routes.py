
from bson import ObjectId
from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from datetime import datetime
import json

from api.doctor import doctors
from config import mongo
from middleware.auth_middleware import token_required


# Route to create a team for an operation
@doctors.route('/create-team', methods=['GET', 'POST'], endpoint='create_team')
@token_required
def create_team(current_user):
    if request.method == "GET":
        return render_template("doctor/creation_team_management.html")

    elif request.method == "POST":

        data = request.get_json()
        print(data)
        doctor_id = current_user
        operation_type = data['operation_type']
        members = data[
            'members']  # List of member info with roles (e.g., [ {"user_id": "123", "role": "surgeon"}, ... ])

        # Create a new team entry
        team = {
            "doctor_id": ObjectId(doctor_id),
            "operation_type": ObjectId(operation_type),
            "team_name": data['team_name'],
            "members": members,
            "status": True,
            "created_at": datetime.utcnow(),
        }

        # Insert into the database
        team_id = mongo.db.teams.insert_one(team).inserted_id
        # print(team)

        return jsonify({"message": "Team created successfully", "team_id": str(team_id)}), 201


@doctors.route('/get-all-teams' , methods=['GET'], endpoint='get_all_teams')
@token_required
def get_all_teams(current_user):
    teams = list(mongo.db.teams.find({"doctor_id" : ObjectId(current_user)}))
    print(teams)

    for doctor in teams:
        if 'doctor_id' in doctor:
            doctor['doctor_id'] = str(doctor['doctor_id'])
        if '_id' in doctor:
            doctor['_id'] = str(doctor['_id'])
        if 'operation_type' in doctor:
            doctor['operation_type'] = str(doctor['operation_type'])

    return jsonify(teams)


@doctors.route('/get-teams', methods=['GET'], endpoint='get_teams')
@token_required
def get_teams(current_user):
    # Aggregating the data
    teams = list(mongo.db.teams.aggregate([
        {
            '$match': {
                'doctor_id': ObjectId(current_user)
            }
        },
        {
            '$lookup': {
                'from': 'operations',
                'localField': 'operation_type',
                'foreignField': '_id',
                'as': 'operation_details'
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'members.user_id',
                'foreignField': 'user_id',
                'as': 'members_details'
            }
        }
    ]))

    # Merging members with their details
    for team in teams:
        merged_members = []

        # Ensure that 'members_details' is a list
        if isinstance(team['members_details'], str):  # If it's a string, convert it to list
            team['members_details'] = json.loads(team['members_details'])

        # Proceed to merge members if 'members_details' is a list
        if isinstance(team['members_details'], list):
            for member in team['members']:
                # Match the member's user_id with member details
                member_details = next(
                    (detail for detail in team['members_details'] if detail['user_id'] == member['user_id']),
                    None
                )
                if member_details:
                    # Merge member data with member details
                    merged_member = {**member, **member_details}
                    merged_members.append(merged_member)

            # Replace original members with the merged members
            team['members'] = merged_members

        # Clean up the 'members_details' field if no longer needed
        del team['members_details']

    # print(teams)
    # Return the result to the template
    return render_template("doctor/view_team_templates.html", teams=teams)


# Route to get real-time updates on the team
@doctors.route('/team-status/<team_id>', methods=['GET'])
def get_team_status(team_id):
    team = mongo.db.teams.find_one({"_id": mongo.db.ObjectId(team_id)})
    if not team:
        return jsonify({"message": "Team not found"}), 404

    return jsonify({
        "operation_type": team['operation_type'],
        "operation_time": team['operation_time'],
        "status": team['status'],
        "members": team['members'],
        "patient_id": team['patient_id']
    }), 200


# Route to update the team status (e.g., in progress, completed)
@doctors.route('/update-team-status/<team_id>', methods=['PATCH'])
def update_team_status(team_id):
    data = request.get_json()
    status = data['status']

    # Update team status
    result = mongo.db.teams.update_one(
        {"_id": mongo.db.ObjectId(team_id)},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        return jsonify({"message": "Team not found "}), 404

    return jsonify({"message": f"Team status updated to {status}"}), 200
