from datetime import datetime, timedelta
from flask import render_template, request, redirect, flash, jsonify
from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    BLOOD_BANK_INVENTORY, ADMIN,
    BLOOD_BANK_ADD_INVENTORY, BLOOD_BANK_EDIT_INVENTORY,
    BLOOD_BANK_DELETE_INVENTORY, BLOOD_BANK_RESTORE_INVENTORY
)
from models.bloodModel import BloodInventory, BloodType, BloodDonor
from utils.config import db


@admin.route(BLOOD_BANK_INVENTORY, methods=['GET'], endpoint='blood_bank_inventory')
def blood_bank_inventory():
    inventory = BloodInventory.query.filter_by(is_deleted=False).all()
    deleted_inventory = BloodInventory.query.filter_by(is_deleted=True).all()

    # Calculate summary by blood type
    blood_type_summary = {}
    for bt in BloodType:
        total_units = sum(
            inv.units_available for inv in inventory
            if inv.blood_type == bt and inv.expiration_date > datetime.utcnow()
        )
        expiring_soon = sum(
            inv.units_available for inv in inventory
            if inv.blood_type == bt and
            inv.expiration_date > datetime.utcnow() and
            inv.expiration_date <= datetime.utcnow() + timedelta(days=7)
        )
        blood_type_summary[bt.value] = {
            'total': total_units,
            'expiring_soon': expiring_soon
        }

    return render_template("admin_templates/blood_bank/blood_inventory.html",
                           inventory=inventory,
                           deleted_inventory=deleted_inventory,
                           blood_type_summary=blood_type_summary,
                           datetime=datetime,
                           BloodType=BloodType,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_INVENTORY=BLOOD_BANK_ADD_INVENTORY,
                           BLOOD_BANK_EDIT_INVENTORY=BLOOD_BANK_EDIT_INVENTORY,
                           BLOOD_BANK_DELETE_INVENTORY=BLOOD_BANK_DELETE_INVENTORY,
                           BLOOD_BANK_RESTORE_INVENTORY=BLOOD_BANK_RESTORE_INVENTORY)


@admin.route(BLOOD_BANK_ADD_INVENTORY, methods=['POST'], endpoint="add_blood_inventory")
def add_blood_inventory():
    try:
        # Validate required fields
        required_fields = ['blood_type', 'units_available', 'expiration_date']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

        # Get donation_id if provided
        donation_id = request.form.get('donation_id')
        if donation_id:
            donation = BloodDonor.query.filter_by(id=donation_id, is_deleted=False).first()
            if not donation:
                flash('Invalid donation ID provided', 'danger')
                return redirect(request.url)

        # Create new inventory item
        new_inventory = BloodInventory(
            blood_type=BloodType(request.form['blood_type']),
            units_available=float(request.form['units_available']),
            donation_id=donation_id,
            expiration_date=datetime.strptime(request.form['expiration_date'], '%Y-%m-%d'),
            storage_location=request.form.get('storage_location')
        )

        db.session.add(new_inventory)
        db.session.commit()

        flash('Blood inventory item added successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding inventory item: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_INVENTORY)


@admin.route(BLOOD_BANK_EDIT_INVENTORY + '/<int:inventory_id>', methods=['POST'])
def edit_blood_inventory(inventory_id):
    inventory = BloodInventory.query.get_or_404(inventory_id)

    try:
        # Update inventory information
        inventory.blood_type = BloodType(request.form['blood_type'])
        inventory.units_available = float(request.form['units_available'])
        inventory.expiration_date = datetime.strptime(request.form['expiration_date'], '%Y-%m-%d')
        inventory.storage_location = request.form.get('storage_location')

        # Update donation reference if changed
        donation_id = request.form.get('donation_id')
        if donation_id:
            donation = BloodDonor.query.filter_by(id=donation_id, is_deleted=False).first()
            if not donation:
                flash('Invalid donation ID provided', 'danger')
                return redirect(request.url)
            inventory.donation_id = donation_id
        else:
            inventory.donation_id = None

        inventory.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Inventory item updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating inventory item: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_INVENTORY)


@admin.route(BLOOD_BANK_DELETE_INVENTORY + '/<int:inventory_id>', methods=['POST'])
def delete_blood_inventory(inventory_id):
    inventory = BloodInventory.query.get_or_404(inventory_id)

    try:
        # Check if inventory is referenced in requests or transfusions
        if inventory.request_items or inventory.transfusion_items:
            flash('Cannot delete inventory item that is referenced in requests or transfusions', 'danger')
            return redirect(ADMIN + BLOOD_BANK_INVENTORY)

        inventory.is_deleted = True
        inventory.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Inventory item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory item: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_INVENTORY)


@admin.route(BLOOD_BANK_RESTORE_INVENTORY + '/<int:inventory_id>', methods=['POST'])
def restore_blood_inventory(inventory_id):
    inventory = BloodInventory.query.get_or_404(inventory_id)

    try:
        inventory.is_deleted = False
        inventory.deleted_at = None
        db.session.commit()
        flash('Inventory item restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring inventory item: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_INVENTORY)


# Additional utility routes
@admin.route('/blood-inventory/summary', methods=['GET'])
def blood_inventory_summary():
    inventory = BloodInventory.query.filter_by(is_deleted=False).all()

    summary = {}
    for bt in BloodType:
        total_units = sum(
            inv.units_available for inv in inventory
            if inv.blood_type == bt and inv.expiration_date > datetime.utcnow()
        )
        expiring_soon = sum(
            inv.units_available for inv in inventory
            if inv.blood_type == bt and
            inv.expiration_date > datetime.utcnow() and
            inv.expiration_date <= datetime.utcnow() + timedelta(days=7)
        )
        summary[bt.value] = {
            'total': total_units,
            'expiring_soon': expiring_soon
        }

    return jsonify(summary)


# @admin.route('/blood-inventory/expiring', methods=['GET'])
# def expiring_blood_inventory():
#     # Get inventory expiring in the next 7 days
#     expiring = BloodInventory.query.filter(
#         BloodInventory.expiration_date > datetime.utcnow(),
#         BloodInventory.expiration_date <= datetime.utcnow() + timedelta(days=7),
#         BloodInventory.is_deleted == False
#     ).all()
#
#     return render_template("admin_templates/blood_bank/expiring_inventory.html",
#                            expiring_inventory=expiring,
#                            datetime=datetime)