# from datetime import datetime
#
# from flask import jsonify, request, render_template
#
# from controllers.admin_controllers import admin
# from utils.config import mongo
#
#
# @admin.route('/add-operation', methods=['GET','POST'])
# def add_operation():
#     if request.method == 'GET':
#         return render_template("admin_templates/operation/add_operation_templates.html")
#     elif request.method == 'POST':
#         data = request.get_json()
#
#         # Get data from the form submission
#         operation_type = data['operation_type']
#         price = data['price']
#         benefits = data['benefits']
#
#         # Create the operation record
#         operation_record = {
#             "operation_type": operation_type,
#             "price": price,
#             "benefits": benefits,
#             "status": True,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow(),
#         }
#
#         # Save the operation to MongoDB
#         mongo.db.operations.insert_one(operation_record)
#
#         return jsonify({"message": "Operation added successfully!"}), 201
#
#
# @admin.route('/get-all-operations', methods=['GET'])
# def get_all_operations():
#     operations = mongo.db.operations.find()  # Fetch all operations from the MongoDB
#     operation_list = []
#
#     for operation in operations:
#         operation_list.append({
#             "id": str(operation["_id"]),
#             "operation_type": operation["operation_type"]
#         })
#
#     return jsonify(operation_list)
#
# @admin.route('/get-operations', methods=['GET'])
# def get_operations():
#     operations = mongo.db.operations.find()  # Fetch all operations from the MongoDB
#
#     # print(list(operations))
#     return render_template("admin_templates/operation/view_operations_templates.html", operations=operations)