import os
from datetime import datetime

from flask import render_template, request, flash, redirect
from werkzeug.utils import secure_filename

from controllers.laboratory_controllers import laboratory
from models import PrescriptionTestReport, Prescription, Appointment
from models.doctorModel import Doctor
from models.patientModel import Patient
from utils.config import db


@laboratory.route('/test-reports', methods=['GET'])
def test_reports():
    # Get all test reports with related prescription, appointment, patient, and doctor info
    test_reports = db.session.query(PrescriptionTestReport)\
        .join(Prescription)\
        .join(Appointment, Prescription.appointment_id == Appointment.id)\
        .join(Patient, Appointment.patient_id == Patient.id)\
        .join(Doctor, Appointment.doctor_id == Doctor.id)\
        .options(
            db.joinedload(PrescriptionTestReport.prescription)
            .joinedload(Prescription.appointment)
            .joinedload(Appointment.patient),
            db.joinedload(PrescriptionTestReport.prescription)
            .joinedload(Prescription.appointment)
            .joinedload(Appointment.doctor)
        )\
        .order_by(PrescriptionTestReport.status, PrescriptionTestReport.id.desc())\
        .all()

    return render_template('laboratory_templates/test_reports/test_reports.html', test_reports=test_reports)

@laboratory.route('/test-report/<int:report_id>', methods=['GET'])
def view_test_report(report_id):
    test_report = db.session.query(PrescriptionTestReport) \
        .join(Prescription) \
        .join(Patient, Prescription.patient_id == Patient.id) \
        .join(Doctor, Prescription.doctor_id == Doctor.id) \
        .options(
        db.joinedload(PrescriptionTestReport.prescription)
        .joinedload(Prescription.patient),
        db.joinedload(PrescriptionTestReport.prescription)
        .joinedload(Prescription.doctor)
    ) \
        .filter(PrescriptionTestReport.id == report_id) \
        .first_or_404()

    return render_template('laboratory_templates/test_reports/view_test_report.html', test_report=test_report)


@laboratory.route('/test-report/<int:report_id>/update', methods=['POST'])
def update_test_report(report_id):
    test_report = PrescriptionTestReport.query.get_or_404(report_id)

    # Update status
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Completed']:
        test_report.status = new_status

    # Handle file upload
    if 'report_file' in request.files:
        file = request.files['report_file']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"report_{report_id}_{datetime.now().timestamp()}.pdf")
            file_path = os.path.join(UPLOAD_FOLDER, 'lab_reports', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            # Remove old file if exists
            if test_report.file_path and os.path.exists(test_report.file_path):
                os.remove(test_report.file_path)

            test_report.file_path = file_path

    db.session.commit()
    flash('Test report updated successfully', 'success')
    return redirect(url_for('laboratory.view_test_report', report_id=report_id))


@laboratory.route('/test-report/<int:report_id>/download', methods=['GET'])
def download_test_report(report_id):
    test_report = PrescriptionTestReport.query.get_or_404(report_id)

    if not test_report.file_path or not os.path.exists(test_report.file_path):
        flash('Report file not found', 'danger')
        return redirect(url_for('laboratory.view_test_report', report_id=report_id))

    return send_file(test_report.file_path, as_attachment=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'pdf'}
