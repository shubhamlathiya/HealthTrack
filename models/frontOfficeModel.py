from datetime import datetime

from utils.config import db


class Visitor(db.Model):
    """
    SQLAlchemy Model for managing hospital visitors.
    Tracks visitor details, purpose, and entry/exit times.
    """
    __tablename__ = 'visitors'  # Explicit table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(100), nullable=True)  # Phone or Email
    purpose = db.Column(db.String(100), nullable=False)  # e.g., 'Visiting Patient', 'General Inquiry', 'Delivery'
    person_department_visiting = db.Column(db.String(100), nullable=False)
    patient_relation = db.Column(db.String(50), nullable=True)  # e.g., 'Family', 'Friend'
    entry_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=True)
    visitor_pass_id = db.Column(db.String(50), unique=True, nullable=True)
    id_proof_type = db.Column(db.String(50), nullable=True)  # e.g., 'Aadhar', 'Driver\'s License'
    id_proof_number = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Visitor {self.name} ({self.purpose})>'


class CallLog(db.Model):
    """
    SQLAlchemy Model for logging phone calls in the front office.
    Tracks incoming/outgoing calls, caller details, and summaries.
    """
    __tablename__ = 'call_logs'  # Explicit table name

    id = db.Column(db.Integer, primary_key=True)
    call_datetime = db.Column(db.DateTime, default=datetime.now, nullable=False)
    call_type = db.Column(db.String(20), nullable=False)  # 'Incoming' or 'Outgoing'
    caller_recipient_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    purpose_of_call = db.Column(db.String(100), nullable=False)  # e.g., 'Patient Inquiry', 'Appointment', 'Emergency'
    spoke_to_staff = db.Column(db.String(100), nullable=False)  # Name of hospital staff
    call_duration_minutes = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.Text, nullable=False)
    follow_up_required = db.Column(db.Boolean, default=False, nullable=False)
    follow_up_date = db.Column(db.Date, nullable=True)  # For follow-up scheduling

    def __repr__(self):
        return f'<CallLog {self.call_type} from/to {self.caller_recipient_name}>'


class PostalItem(db.Model):
    """
    SQLAlchemy Model for tracking received and dispatched postal items.
    Handles letters, parcels, couriers, etc.
    """
    __tablename__ = 'postal_items'  # Explicit table name

    id = db.Column(db.Integer, primary_key=True)
    item_datetime = db.Column(db.DateTime, default=datetime.now, nullable=False)
    direction = db.Column(db.String(20), nullable=False)  # 'Received' or 'Dispatched'
    sender_receiver_name = db.Column(db.String(100), nullable=False)  # Sender (if received), Receiver (if dispatched)
    tracking_number = db.Column(db.String(100), nullable=True)
    item_type = db.Column(db.String(50), nullable=False)  # e.g., 'Letter', 'Parcel', 'Courier'
    internal_recipient_sender = db.Column(db.String(100), nullable=True)  # Internal dept/staff for received/sent items
    external_address = db.Column(db.Text, nullable=True)  # Full address for dispatched items
    handled_by_staff = db.Column(db.String(100), nullable=False)  # Front office staff who processed it
    courier_service = db.Column(db.String(100), nullable=True)  # e.g., 'India Post', 'DTDC'
    delivery_status = db.Column(db.String(50), nullable=True)  # For received items: 'Pending Delivery', 'Delivered'
    delivery_to_recipient_datetime = db.Column(db.DateTime, nullable=True)  # When received item was handed over
    remarks = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PostalItem {self.direction} {self.item_type} ({self.sender_receiver_name})>'


class Complaint(db.Model):
    """
    SQLAlchemy Model for logging and managing complaints received in the hospital.
    Includes complaint details, status, and resolution information.
    """
    __tablename__ = 'complaints'  # Explicit table name

    id = db.Column(db.Integer, primary_key=True)
    complaint_datetime = db.Column(db.DateTime, default=datetime.now, nullable=False)
    complainant_name = db.Column(db.String(100), nullable=False)
    complainant_contact = db.Column(db.String(100), nullable=True)  # Phone or Email
    complainant_type = db.Column(db.String(50), nullable=False)  # 'Patient', 'Family', 'Visitor', 'Staff', 'Other'
    patient_id = db.Column(db.String(50), nullable=True)  # Optional: Link to a patient ID
    category = db.Column(db.String(100), nullable=False)  # e.g., 'Staff Behavior', 'Medical Care', 'Facility Issue'
    details = db.Column(db.Text, nullable=False)  # Full description of the complaint
    severity = db.Column(db.String(20), nullable=False)  # 'Low', 'Medium', 'High', 'Urgent'
    assigned_to = db.Column(db.String(100), nullable=True)  # Department or staff member assigned
    status = db.Column(db.String(50), default='New', nullable=False)  # 'New', 'In Progress', 'Resolved', 'Escalated'
    resolution_datetime = db.Column(db.DateTime, nullable=True)
    resolution_details = db.Column(db.Text, nullable=True)
    resolved_by = db.Column(db.String(100), nullable=True)  # Staff member who resolved it
    feedback_given = db.Column(db.Boolean, default=False, nullable=False)  # Was feedback received on resolution?

    def __repr__(self):
        return f'<Complaint {self.category} - {self.status}>'

#
# @app.route('/visitors', methods=['POST'])
# def add_visitor():
#     """Endpoint to add a new visitor."""
#     data = request.json
#     try:
#         new_visitor = Visitor(
#             name=data['name'],
#             contact_info=data.get('contact_info'),
#             purpose=data['purpose'],
#             person_department_visiting=data['person_department_visiting'],
#             patient_relation=data.get('patient_relation'),
#             visitor_pass_id=data.get('visitor_pass_id'),
#             id_proof_type=data.get('id_proof_type'),
#             id_proof_number=data.get('id_proof_number'),
#             remarks=data.get('remarks')
#         )
#         db.session.add(new_visitor)
#         db.session.commit()
#         return jsonify({"message": "Visitor added successfully!", "id": new_visitor.id}), 201
#     except KeyError as e:
#         db.session.rollback()
#         return jsonify({"error": f"Missing required field: {e.args[0]}"}), 400
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500
#
# @app.route('/visitors', methods=['GET'])
# def get_visitors():
#     """Endpoint to retrieve all visitors."""
#     visitors = Visitor.query.all()
#     # Convert visitors to a list of dictionaries for JSON serialization
#     visitors_data = []
#     for visitor in visitors:
#         visitors_data.append({
#             'id': visitor.id,
#             'name': visitor.name,
#             'contact_info': visitor.contact_info,
#             'purpose': visitor.purpose,
#             'person_department_visiting': visitor.person_department_visiting,
#             'patient_relation': visitor.patient_relation,
#             'entry_time': visitor.entry_time.isoformat(),
#             'exit_time': visitor.exit_time.isoformat() if visitor.exit_time else None,
#             'visitor_pass_id': visitor.visitor_pass_id,
#             'id_proof_type': visitor.id_proof_type,
#             'id_proof_number': visitor.id_proof_number,
#             'remarks': visitor.remarks
#         })
#     return jsonify(visitors_data), 200
#
# # You would add similar GET, POST, PUT, DELETE routes for CallLog, PostalItem, and Complaint models.
# # For example, to retrieve all call logs:
# @app.route('/call_logs', methods=['GET'])
# def get_call_logs():
#     call_logs = CallLog.query.all()
#     logs_data = []
#     for log in call_logs:
#         logs_data.append({
#             'id': log.id,
#             'call_datetime': log.call_datetime.isoformat(),
#             'call_type': log.call_type,
#             'caller_recipient_name': log.caller_recipient_name,
#             'phone_number': log.phone_number,
#             'purpose_of_call': log.purpose_of_call,
#             'spoke_to_staff': log.spoke_to_staff,
#             'call_duration_minutes': log.call_duration_minutes,
#             'summary': log.summary,
#             'follow_up_required': log.follow_up_required,
#             'follow_up_date': log.follow_up_date.isoformat() if log.follow_up_date else None
#         })
#     return jsonify(logs_data), 200
