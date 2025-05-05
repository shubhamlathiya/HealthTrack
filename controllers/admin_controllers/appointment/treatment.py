from datetime import datetime

from flask import render_template, request, redirect, flash

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import TREATMENTS, TREATMENTS_ADD, ADMIN, TREATMENTS_EDIT, \
    TREATMENTS_DELETE, TREATMENTS_RESTORE, TREATMENTS_TOGGLE_STATUS
from models.departmentModel import Department
from models.treatmentModel import Treatment
from utils.config import db


# Treatment Management Routes
@admin.route(TREATMENTS, methods=['GET'], endpoint='treatments')
def treatments():
    active_treatments = Treatment.query.filter_by(is_deleted=False).all()
    deleted_treatments = Treatment.query.filter_by(is_deleted=True).all()
    departments = Department.query.all()
    return render_template('admin_templates/appointment/treatments.html',
                           treatments=active_treatments,
                           deleted_treatments=deleted_treatments,
                           departments=departments,
                           ADMIN=ADMIN,
                           TREATMENTS_ADD=TREATMENTS_ADD,
                           TREATMENTS_EDIT=TREATMENTS_EDIT,
                           TREATMENTS_TOGGLE_STATUS=TREATMENTS_TOGGLE_STATUS,
                           TREATMENTS_DELETE=TREATMENTS_DELETE,
                           TREATMENTS_RESTORE=TREATMENTS_RESTORE)


@admin.route(TREATMENTS_ADD, methods=['POST'], endpoint='add_treatment')
def add_treatment():
    try:
        treatment = Treatment(
            name=request.form.get('name'),
            description=request.form.get('description'),
            duration_minutes=int(request.form.get('duration_minutes')),
            base_price=float(request.form.get('base_price')),
            icon=request.form.get('icon'),
            department_id=int(request.form.get('department_id')),
            active=bool(int(request.form.get('active')))
        )
        db.session.add(treatment)
        db.session.commit()
        flash('Treatment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding treatment: {str(e)}', 'danger')
    return redirect(ADMIN + TREATMENTS)


@admin.route(TREATMENTS_EDIT + '/<int:treatment_id>', methods=['POST'], endpoint="edit_treatment")
def edit_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    try:
        treatment.name = request.form.get('name')
        treatment.description = request.form.get('description')
        treatment.duration_minutes = int(request.form.get('duration_minutes'))
        treatment.base_price = float(request.form.get('base_price'))
        treatment.icon = request.form.get('icon')
        treatment.department_id = int(request.form.get('department_id'))
        treatment.active = bool(int(request.form.get('active')))
        treatment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Treatment updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating treatment: {str(e)}', 'danger')
    return redirect(ADMIN + TREATMENTS)


@admin.route(TREATMENTS_TOGGLE_STATUS + '/<int:treatment_id>', methods=['POST'], endpoint="toggle_treatment_status")
def toggle_treatment_status(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    try:
        treatment.active = not treatment.active
        treatment.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Treatment {"activated" if treatment.active else "deactivated"} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing treatment status: {str(e)}', 'danger')
    return redirect(ADMIN + TREATMENTS)


@admin.route(TREATMENTS_DELETE + '/<int:treatment_id>', methods=['POST'], endpoint="delete_treatment")
def delete_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    try:
        treatment.is_deleted = True
        treatment.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Treatment archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving treatment: {str(e)}', 'danger')
    return redirect(ADMIN + TREATMENTS)


@admin.route(TREATMENTS_RESTORE + '/<int:treatment_id>', methods=['POST'], endpoint="restore_treatment")
def restore_treatment(treatment_id):
    treatment = Treatment.query.get_or_404(treatment_id)
    try:
        treatment.is_deleted = False
        treatment.deleted_at = None
        db.session.commit()
        flash('Treatment restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring treatment: {str(e)}', 'danger')
    return redirect(ADMIN + TREATMENTS)
