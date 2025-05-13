from datetime import datetime

from flask import render_template, request, redirect, flash, jsonify

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    BLOOD_BANK_REQUESTS, BLOOD_BANK_ADD_REQUEST, BLOOD_BANK_EDIT_REQUEST,
    BLOOD_BANK_DELETE_REQUEST, BLOOD_BANK_APPROVE_REQUEST, BLOOD_BANK_REJECT_REQUEST,
    BLOOD_BANK_COMPLETE_REQUEST, ADMIN
)
from models.bloodModel import (
    BloodRequest, BloodRequestItem, BloodTransfusion, BloodTransfusionItem,
    BloodType, BloodInventory
)
from utils.config import db


# ====================== BLOOD REQUEST ROUTES ======================

@admin.route(BLOOD_BANK_REQUESTS, methods=['GET'])
def blood_requests():
    requests = BloodRequest.query.filter_by(is_deleted=False).order_by(BloodRequest.request_date.desc()).all()
    return render_template("admin_templates/blood_bank/blood_requests.html",
                           requests=requests,
                           datetime=datetime,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_REQUEST=BLOOD_BANK_ADD_REQUEST,
                           BLOOD_BANK_EDIT_REQUEST=BLOOD_BANK_EDIT_REQUEST,
                           BLOOD_BANK_DELETE_REQUEST=BLOOD_BANK_DELETE_REQUEST,
                           BLOOD_BANK_APPROVE_REQUEST=BLOOD_BANK_APPROVE_REQUEST,
                           BLOOD_BANK_REJECT_REQUEST=BLOOD_BANK_REJECT_REQUEST,
                           BLOOD_BANK_COMPLETE_REQUEST=BLOOD_BANK_COMPLETE_REQUEST)


@admin.route(BLOOD_BANK_ADD_REQUEST, methods=['POST'])
def add_blood_request():
    try:
        data = request.form
        print(data)
        # Validate required fields
        if not data.get('department'):
            flash('Requester and department are required', 'danger')
            return redirect(ADMIN + BLOOD_BANK_REQUESTS)

        # Create new request
        new_request = BloodRequest(
            requester_id=data['requester_id'],
            patient_id=data.get('patient_id'),
            department=data['department'],
            status='Pending',
            priority=data.get('priority', 'Normal'),
            notes=data.get('notes')
        )

        db.session.add(new_request)
        db.session.flush()  # To get the ID for items

        # Add request items
        if 'items' in data:
            for item in data['items']:
                new_item = BloodRequestItem(
                    request_id=new_request.id,
                    blood_type=BloodType(item['blood_type']),
                    units_requested=float(item['units_requested'])
                )
                db.session.add(new_item)

        db.session.commit()
        flash('Blood request created successfully!', 'success')

        if request.is_json:
            return jsonify({'success': True, 'request_id': new_request.id})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)


@admin.route(BLOOD_BANK_EDIT_REQUEST + '/<int:request_id>', methods=['POST'])
def edit_blood_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)

    try:
        data = request.get_json() if request.is_json else request.form

        blood_request.patient_id = data.get('patient_id', blood_request.patient_id)
        blood_request.department = data.get('department', blood_request.department)
        blood_request.priority = data.get('priority', blood_request.priority)
        blood_request.notes = data.get('notes', blood_request.notes)
        blood_request.updated_at = datetime.utcnow()

        # Update items if provided
        if 'items' in data:
            # Delete existing items
            BloodRequestItem.query.filter_by(request_id=request_id).delete()

            # Add new items
            for item in data['items']:
                new_item = BloodRequestItem(
                    request_id=request_id,
                    blood_type=BloodType(item['blood_type']),
                    units_requested=float(item['units_requested'])
                )
                db.session.add(new_item)

        db.session.commit()
        flash('Blood request updated successfully!', 'success')

        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_APPROVE_REQUEST + '/<int:request_id>', methods=['POST'])
def approve_blood_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)

    try:
        data = request.get_json() if request.is_json else request.form

        # Validate inventory for each item
        for item in blood_request.items:
            if 'items' in data:
                # Find matching item in request data
                req_item = next((i for i in data['items'] if i['id'] == item.id), None)
                if req_item:
                    units_approved = float(req_item.get('units_approved', 0))
                    if units_approved > 0:
                        # Check inventory availability
                        inventory = BloodInventory.query.filter_by(
                            blood_type=item.blood_type,
                            is_deleted=False
                        ).filter(
                            BloodInventory.expiration_date > datetime.utcnow()
                        ).order_by(
                            BloodInventory.expiration_date
                        ).first()

                        if not inventory or inventory.units_available < units_approved:
                            raise ValueError(f'Not enough inventory for blood type {item.blood_type.value}')

                        item.units_approved = units_approved
                        item.inventory_id = inventory.id

                        # Deduct from inventory
                        inventory.units_available -= units_approved
                        if inventory.units_available <= 0:
                            inventory.is_deleted = True
                            inventory.deleted_at = datetime.utcnow()

        blood_request.status = 'Approved'
        blood_request.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Blood request approved successfully!', 'success')
        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error approving blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_REJECT_REQUEST + '/<int:request_id>', methods=['POST'])
def reject_blood_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)

    try:
        blood_request.status = 'Rejected'
        blood_request.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Blood request rejected successfully!', 'success')
        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_COMPLETE_REQUEST + '/<int:request_id>', methods=['POST'])
def complete_blood_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)

    try:
        if blood_request.status != 'Approved':
            raise ValueError('Only approved requests can be completed')

        # Create transfusion record
        transfusion = BloodTransfusion(
            patient_id=blood_request.patient_id,
            doctor_id=request.form.get('doctor_id'),  # Current user or specified doctor
            notes=f'Completed from request #{request_id}'
        )
        db.session.add(transfusion)
        db.session.flush()

        # Add transfusion items
        for item in blood_request.items:
            if item.units_approved > 0 and item.inventory_id:
                transfusion_item = BloodTransfusionItem(
                    transfusion_id=transfusion.id,
                    blood_type=item.blood_type,
                    units_used=item.units_approved,
                    inventory_id=item.inventory_id
                )
                db.session.add(transfusion_item)

        blood_request.status = 'Completed'
        blood_request.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Blood request completed successfully!', 'success')
        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error completing blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_DELETE_REQUEST + '/<int:request_id>', methods=['POST'])
def delete_blood_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)

    try:
        if blood_request.status == 'Completed':
            raise ValueError('Completed requests cannot be deleted')

        blood_request.is_deleted = True
        blood_request.deleted_at = datetime.utcnow()
        db.session.commit()

        flash('Blood request deleted successfully!', 'success')
        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_REQUESTS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting blood request: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)

# ====================== BLOOD TRANSFUSION ROUTES ======================


# ====================== DEPARTMENT ROUTES ======================

# @admin.route('/departments/blood-requests', methods=['GET'])
# def department_blood_requests():
#     # Get requests for the current user's department
#     department = current_user.department  # Assuming current_user is available
#     requests = BloodRequest.query.filter_by(
#         department=department,
#         is_deleted=False
#     ).order_by(
#         BloodRequest.request_date.desc()
#     ).all()
#
#     return render_template("department_templates/blood_requests.html",
#                            requests=requests,
#                            datetime=datetime)


# ====================== PATIENT ROUTES ======================

# @admin.route('/patients/<int:patient_id>/blood-transfusions', methods=['GET'])
# def patient_blood_transfusions(patient_id):
#     patient = Patient.query.get_or_404(patient_id)
#     transfusions = BloodTransfusion.query.filter_by(
#         patient_id=patient_id,
#         is_deleted=False
#     ).order_by(
#         BloodTransfusion.transfusion_date.desc()
#     ).all()
#
#     return render_template("patient_templates/blood_transfusions.html",
#                            patient=patient,
#                            transfusions=transfusions,
#                            datetime=datetime)
