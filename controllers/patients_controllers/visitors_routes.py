# @app.route('/api/patient/<int:patient_id>/visitors')
# def api_patient_visitors(patient_id):
#     visitors = Patient.query.get_or_404(patient_id).get_visitor_history()
#     return jsonify([v.serialize() for v in visitors])