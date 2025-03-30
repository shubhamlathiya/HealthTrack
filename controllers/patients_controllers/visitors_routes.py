from bson import ObjectId
from flask import jsonify, request, render_template, redirect

from controllers.patients_controllers import patients
from utils.config import mongo
from middleware.auth_middleware import token_required


@patients.route('/add-visitor', methods=['POST'], endpoint='add-visitor')
@token_required
def add_visitor(current_user):
    visitor_name = request.form.get('name')
    relationship = request.form.get('relationship')
    contact = request.form.get('contact')

    if not all([visitor_name, relationship, contact]):
        return jsonify({"error": "All fields are required"}), 400

    # Check the number of visitors for the current patient in the visitors collection
    visitor_count = mongo.db.visitor.count_documents({"user_id": ObjectId(current_user)})
    if visitor_count >= 2:
        return jsonify({"error": "Visitor limit reached"}), 400

    # Add visitor
    # Create the visitor entry
    new_visitor = {
        "user_id": ObjectId(current_user),
        "name": visitor_name,
        "relationship": relationship,
        "contact": contact
    }

    # Insert the new visitor into the visitor collection
    mongo.db.visitor.insert_one(new_visitor)

    return redirect("/patient/get-visitors")
    # return render_template("patient/patient_visitor_templates.html" , ), 200
#

@patients.route('/get-visitors', methods=['GET'], endpoint='get-visitors')
@token_required
def get_visitors(current_user):
    visitor = list(mongo.db.visitor.find({"user_id": ObjectId(current_user)}))
    # print(visitor)
    if not visitor:
        return render_template("patient/patient_visitor_templates.html", error="visitor not found"), 200

        # return jsonify({"error": "visitor not found"}), 404

    return render_template("patient/patient_visitor_templates.html", visitors=visitor), 200


@patients.route('/remove-visitor/<visitor_id>', methods=['GET'])
def remove_visitor(visitor_id):
    # Find the visitor record by its ID
    visitor = mongo.db.visitor.find_one({"_id": ObjectId(visitor_id)})
    if not visitor:
        return jsonify({"error": "Visitor not found"}), 404

    # Delete the visitor record from the database
    mongo.db.visitor.delete_one({"_id": ObjectId(visitor_id)})

    return redirect("/patient/get-visitors")
    # return jsonify({"message": "Visitor removed successfully"}), 200
