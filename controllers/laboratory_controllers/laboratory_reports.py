from datetime import datetime

from flask import render_template, request, flash, redirect, jsonify
from sqlalchemy import or_

from controllers.constant.laboratoryPathConstant import LAB_REPORTS, LAB_REPORTS_ADD, LAB_REPORTS_EDIT, \
    LAB_REPORTS_TOGGLE, LAB_REPORTS_DELETE, LAB_REPORTS_RESTORE, LABORATORY
from controllers.laboratory_controllers import laboratory
from models.LaboratoryTestReport import LaboratoryTestReport
from models.departmentModel import Department
from models.medicineModel import Medicine
from utils.config import db


@laboratory.route(LAB_REPORTS, methods=['GET'], endpoint='lab_reports')
def lab_reports():
    active_reports = LaboratoryTestReport.query.filter_by(is_deleted=False).all()
    deleted_reports = LaboratoryTestReport.query.filter_by(is_deleted=True).all()
    departments = Department.query.all()
    return render_template('laboratory_templates/reports/laboratory_reports.html',
                           reports=active_reports,
                           deleted_reports=deleted_reports,
                           departments=departments,
                           ADMIN=LABORATORY,
                           LAB_REPORTS_ADD=LAB_REPORTS_ADD,
                           LAB_REPORTS_EDIT=LAB_REPORTS_EDIT,
                           LAB_REPORTS_TOGGLE=LAB_REPORTS_TOGGLE,
                           LAB_REPORTS_DELETE=LAB_REPORTS_DELETE,
                           LAB_REPORTS_RESTORE=LAB_REPORTS_RESTORE)


@laboratory.route(LAB_REPORTS_ADD, methods=['POST'], endpoint='add_lab_report')
def add_lab_report():
    try:
        report = LaboratoryTestReport(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            department_id=int(request.form.get('department_id')),
            is_active=bool(int(request.form.get('is_active', 1))))
        db.session.add(report)
        db.session.commit()
        flash('Laboratory test report added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding laboratory test report: {str(e)}', 'danger')
    return redirect(LABORATORY + LAB_REPORTS)


@laboratory.route(LAB_REPORTS_EDIT + '/<int:report_id>', methods=['POST'], endpoint="edit_lab_report")
def edit_lab_report(report_id):
    report = LaboratoryTestReport.query.get_or_404(report_id)
    try:
        report.name = request.form.get('name')
        report.description = request.form.get('description')
        report.price = float(request.form.get('price'))
        report.department_id = int(request.form.get('department_id'))
        report.is_active = bool(int(request.form.get('is_active', 1)))
        report.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Laboratory test report updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating laboratory test report: {str(e)}', 'danger')
    return redirect(LABORATORY + LAB_REPORTS)


@laboratory.route(LAB_REPORTS_TOGGLE + '/<int:report_id>', methods=['POST'], endpoint="toggle_lab_report_status")
def toggle_lab_report_status(report_id):
    report = LaboratoryTestReport.query.get_or_404(report_id)
    try:
        report.is_active = not report.is_active
        report.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Laboratory test report {"activated" if report.is_active else "deactivated"} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing laboratory test report status: {str(e)}', 'danger')
    return redirect(LABORATORY + LAB_REPORTS)


@laboratory.route(LAB_REPORTS_DELETE + '/<int:report_id>', methods=['POST'], endpoint="delete_lab_report")
def delete_lab_report(report_id):
    report = LaboratoryTestReport.query.get_or_404(report_id)
    try:
        report.is_deleted = True
        report.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Laboratory test report archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving laboratory test report: {str(e)}', 'danger')
    return redirect(LABORATORY + LAB_REPORTS)


@laboratory.route(LAB_REPORTS_RESTORE + '/<int:report_id>', methods=['POST'], endpoint="restore_lab_report")
def restore_lab_report(report_id):
    report = LaboratoryTestReport.query.get_or_404(report_id)
    try:
        report.is_deleted = False
        report.deleted_at = None
        db.session.commit()
        flash('Laboratory test report restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring laboratory test report: {str(e)}', 'danger')
    return redirect(LABORATORY + LAB_REPORTS)


@laboratory.route('/api/lab-reports/search')
def search_lab_reports():
    search_term = request.args.get('q', '').strip()

    if not search_term:
        return jsonify([])

    reports = LaboratoryTestReport.query.filter(
        LaboratoryTestReport.name.ilike(f'%{search_term}%'),
        LaboratoryTestReport.is_active == True
    ).limit(10).all()
    print(reports)
    return jsonify([{
        'id': report.id,
        'name': report.name,
        'price': report.price,
        'description': report.description
    } for report in reports])


@laboratory.route('/api/medicines/search')
def search_medicines():
    search_term = request.args.get('q', '').strip()

    if not search_term:
        return jsonify([])

    medicines = Medicine.query.filter(
        or_(
            Medicine.name.ilike(f'%{search_term}%'),
            Medicine.medicine_number.ilike(f'%{search_term}%')
        ),
    ).limit(10).all()

    return jsonify([{
        'id': med.id,
        'name': med.name,
        'medicine_number': med.medicine_number
    } for med in medicines])
