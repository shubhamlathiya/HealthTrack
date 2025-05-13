from datetime import datetime

from flask import render_template, request, flash, redirect, jsonify

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import BLOOD_BANK_TRANSFUSIONS, BLOOD_BANK_ADD_TRANSFUSION, ADMIN, \
    BLOOD_BANK_EDIT_TRANSFUSION, BLOOD_BANK_DELETE_TRANSFUSION
from models.bloodModel import BloodTransfusion, BloodInventory, BloodTransfusionItem, BloodType
from utils.config import db


@admin.route(BLOOD_BANK_TRANSFUSIONS, methods=['GET'])
def blood_transfusions():
    transfusions = BloodTransfusion.query.filter_by(is_deleted=False).order_by(
        BloodTransfusion.transfusion_date.desc()).all()
    deleted_transfusions = BloodTransfusion.query.filter_by(is_deleted=True).order_by(
        BloodTransfusion.transfusion_date.desc()).all()
    return render_template("admin_templates/blood_bank/blood_transfusions.html",
                           transfusions=transfusions,
                           datetime=datetime,
                           deleted_transfusions=deleted_transfusions,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_TRANSFUSION=BLOOD_BANK_ADD_TRANSFUSION,
                           BLOOD_BANK_EDIT_TRANSFUSION=BLOOD_BANK_EDIT_TRANSFUSION,
                           BLOOD_BANK_DELETE_TRANSFUSION=BLOOD_BANK_DELETE_TRANSFUSION)


@admin.route(BLOOD_BANK_ADD_TRANSFUSION, methods=['POST'])
def add_blood_transfusion():
    try:
        data = request.get_json() if request.is_json else request.form

        # Validate required fields
        if not data.get('patient_id') or not data.get('doctor_id'):
            flash('Patient and doctor are required', 'danger')
            return redirect(request.url)

        # Create new transfusion
        new_transfusion = BloodTransfusion(
            patient_id=data['patient_id'],
            doctor_id=data['doctor_id'],
            notes=data.get('notes'),
            adverse_reaction=data.get('adverse_reaction', False),
            reaction_details=data.get('reaction_details')
        )

        db.session.add(new_transfusion)
        db.session.flush()  # To get the ID for items

        # Add transfusion items and deduct from inventory
        if 'items' in data:
            for item in data['items']:
                # Verify inventory
                inventory = BloodInventory.query.get(item['inventory_id'])
                if not inventory or inventory.is_deleted or inventory.units_available < float(item['units_used']):
                    raise ValueError(f'Invalid inventory for blood type {item["blood_type"]}')

                # Create transfusion item
                new_item = BloodTransfusionItem(
                    transfusion_id=new_transfusion.id,
                    blood_type=BloodType(item['blood_type']),
                    units_used=float(item['units_used']),
                    inventory_id=item['inventory_id']
                )
                db.session.add(new_item)

                # Update inventory
                inventory.units_available -= float(item['units_used'])
                if inventory.units_available <= 0:
                    inventory.is_deleted = True
                    inventory.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Blood transfusion recorded successfully!', 'success')

        if request.is_json:
            return jsonify({'success': True, 'transfusion_id': new_transfusion.id})
        return redirect(ADMIN + BLOOD_BANK_TRANSFUSIONS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error recording blood transfusion: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_EDIT_TRANSFUSION + '/<int:transfusion_id>', methods=['POST'])
def edit_blood_transfusion(transfusion_id):
    transfusion = BloodTransfusion.query.get_or_404(transfusion_id)

    try:
        data = request.get_json() if request.is_json else request.form

        transfusion.patient_id = data.get('patient_id', transfusion.patient_id)
        transfusion.doctor_id = data.get('doctor_id', transfusion.doctor_id)
        transfusion.notes = data.get('notes', transfusion.notes)
        transfusion.adverse_reaction = data.get('adverse_reaction', transfusion.adverse_reaction)
        transfusion.reaction_details = data.get('reaction_details', transfusion.reaction_details)
        transfusion.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Blood transfusion updated successfully!', 'success')

        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_TRANSFUSIONS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating blood transfusion: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)


@admin.route(BLOOD_BANK_DELETE_TRANSFUSION + '/<int:transfusion_id>', methods=['POST'])
def delete_blood_transfusion(transfusion_id):
    transfusion = BloodTransfusion.query.get_or_404(transfusion_id)

    try:
        # Return units to inventory
        for item in transfusion.items:
            if item.inventory:
                item.inventory.units_available += item.units_used
                if item.inventory.is_deleted and item.inventory.units_available > 0:
                    item.inventory.is_deleted = False
                    item.inventory.deleted_at = None

        transfusion.is_deleted = True
        transfusion.deleted_at = datetime.utcnow()
        db.session.commit()

        flash('Blood transfusion deleted successfully!', 'success')
        if request.is_json:
            return jsonify({'success': True})
        return redirect(ADMIN + BLOOD_BANK_TRANSFUSIONS)

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting blood transfusion: {str(e)}', 'danger')
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(request.url)
