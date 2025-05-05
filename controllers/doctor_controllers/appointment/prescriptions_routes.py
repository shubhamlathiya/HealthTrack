from datetime import datetime, timedelta

from flask import request, jsonify, flash, redirect
from sqlalchemy.exc import SQLAlchemyError

from controllers.doctor_controllers import doctors
from middleware.auth_middleware import token_required
from models.appointmentModel import Appointment
from models.doctorModel import Doctor
from models.prescriptionModel import Prescription, PrescriptionMedication, MedicationTiming, PrescriptionTestReport
from utils.config import db


@doctors.route('/appointments/rebook/<int:appointment_id>', methods=['POST'])
@token_required
def rebook_appointment(current_user, appointment_id):
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        data = request.get_json()


        doctors = Doctor.query.filter_by(user_id=current_user).first()
        if appointment.doctor_id != doctors.id:
            flash("You can only rebook your own appointments", "danger")
            return redirect(request.url)

        new_date =data.get('date')
        time_slot = data.get('time_slot')
        reason = data.get('reason', appointment.reason)

        if not all([new_date, time_slot]):
            flash("Please select both date and time", "danger")
            return redirect(request.url)

        start_time = datetime.strptime(time_slot, '%H:%M').time()
        end_time = (datetime.strptime(time_slot, '%H:%M') + timedelta(minutes=30)).time()
        # Create new appointment (rebook)
        new_appointment = Appointment(
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            date=datetime.strptime(new_date, '%Y-%m-%d').date(),
            start_time=start_time,
            end_time=end_time,
            status='scheduled',
            reason=reason
        )

        # Update old appointment status
        appointment.status = 'Completed'

        db.session.add(new_appointment)
        db.session.commit()

        flash("Appointment successfully rebooked", "success")
        # Send notification to patient here if needed

        return jsonify({
            'success': True,
            'message': 'Appointment successfully rebooked',
            'redirect_url': request.url
        })

    except Exception as e:
        db.session.rollback()
        flash(f"Error rebooking appointment: {str(e)}", "danger")
        return redirect(request.url)


@doctors.route('/appointments/forward/<int:appointment_id>', methods=['POST'])
@token_required
def forward_appointment(current_user, appointment_id):
    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        doctors = Doctor.query.filter_by(user_id=current_user).first()
        if appointment.doctor_id != doctors.id:
            return jsonify({'success': False, 'error': 'You can only forward your own appointments'}), 403
        #
        data = request.get_json()
        print(data)
        forward_to_doctor_id = data['forward_to_doctor_id']
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['time_slot'], '%H:%M').time()
        end_time = (datetime.strptime(data['time_slot'], '%H:%M') + timedelta(minutes=30)).time()

        # Create new forwarded appointment
        new_appointment = Appointment(
            patient_id=appointment.patient_id,
            doctor_id=forward_to_doctor_id,
            original_doctor_id=appointment.doctor_id,
            date=new_date,
            start_time=start_time,
            end_time=end_time,
            status='scheduled',
            reason=data.get('reason', appointment.reason),
            original_appointment_id=appointment.id
        )

        # Update old appointment status
        appointment.status = 'forwarded'
        appointment.forwarded_to = new_appointment.id

        db.session.add(new_appointment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Appointment successfully forwarded',
            'redirect_url': request.url
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@doctors.route('/add-generate-prescriptions', methods=['POST'])
def create_prescription():
    try:
        data = request.get_json()
        print(data)
        # Validate required fields
        if not all(key in data for key in ['appointment_id', 'medications']):
            return jsonify({'error': 'Missing required fields'}), 400

        # Begin transaction
        db.session.begin()

        # Create prescription
        prescription = Prescription(
            appointment_id=data['appointment_id'],
            notes=data.get('notes', ''),
            status='Issued'
        )
        db.session.add(prescription)
        db.session.flush()  # Get the prescription ID

        # Add medications
        for med_data in data['medications']:
            medication = PrescriptionMedication(
                prescription_id=prescription.id,
                name=med_data['name'],
                dosage=med_data['dosage'],
                meal_instructions=med_data['meal_instructions']
            )
            db.session.add(medication)
            db.session.flush()  # Get the medication ID

            # Add timings
            for timing in med_data['timing']:
                db.session.add(MedicationTiming(
                    medication_id=medication.id,
                    timing=timing
                ))

        # Add test reports if any
        for report_data in data.get('test_reports', []):
            db.session.add(PrescriptionTestReport(
                prescription_id=prescription.id,
                report_name=report_data['report_name'],
                report_notes=report_data.get('report_notes', ''),
                price=report_data['price'],
                status='Pending'
            ))

        # Update appointment status
        appointment = Appointment.query.get(data['appointment_id'])
        if not appointment:
            return jsonify({'error': 'Appointment not found'}), 404

        appointment.status = 'Completed'

        db.session.commit()

        return jsonify({
            'success': True,
            'redirect_url': request.url,
            'message': 'Prescription created successfully',
            'prescription_id': prescription.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@doctors.route('/prescriptions/<int:prescription_id>', methods=['GET'])
def get_prescription(prescription_id):
    try:
        prescription = Prescription.query.get(prescription_id)
        if not prescription or prescription.is_deleted:
            return jsonify({'error': 'Prescription not found'}), 404

        # Build response
        response = {
            'id': prescription.id,
            'appointment_id': prescription.appointment_id,
            'notes': prescription.notes,
            'status': prescription.status,
            'created_at': prescription.created_at.isoformat(),
            'medications': [],
            'test_reports': []
        }

        # Add medications
        for med in prescription.medications:
            medication = {
                'name': med.name,
                'dosage': med.dosage,
                'meal_instructions': med.meal_instructions,
                'timing': [t.timing for t in med.timings]
            }
            response['medications'].append(medication)

        # Add test reports
        for report in prescription.test_reports:
            test_report = {
                'report_name': report.report_name,
                'report_notes': report.report_notes,
                'price': report.price,
                'status': report.status,
                'file_path': report.file_path
            }
            response['test_reports'].append(test_report)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
