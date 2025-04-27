import random
import string
from datetime import datetime

from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import (
    BLOOD_BANK_STOCK, ADMIN, BLOOD_BANK_EDIT_STOCK,
    BLOOD_BANK_ADD_STOCK, BLOOD_BANK_RESTORE_STOCK,
    BLOOD_BANK_DELETE_STOCK
)
from models.bloodModel import BloodProduct
from utils.config import db


# Helper Functions
def generate_batch_number():
    """Generate unique batch number with timestamp and random string"""
    now = datetime.now()
    return f"BATCH-{now.strftime('%Y%m%d-%H%M%S')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"


def calculate_product_status(expiry_date):
    """Calculate product status based on expiry date"""
    days_remaining = (expiry_date - datetime.now().date()).days
    if days_remaining <= 0:
        return 'Expired'
    elif days_remaining <= 7:
        return 'Near Expiry'
    return 'Fresh'


# Stock Management Routes
@admin.route(BLOOD_BANK_STOCK, methods=['GET'], endpoint='blood_bank_stock')
def blood_bank_stock():
    products = BloodProduct.query.filter_by(is_deleted=False).all()
    deleted_products = BloodProduct.query.filter_by(is_deleted=True).all()

    # Update status for all products
    for product in products:
        product.status = calculate_product_status(product.expiry_date)

    return render_template('admin_templates/blood_bank/blood_stock.html',
                           blood_products=products,
                           deleted_blood_products=deleted_products,
                           ADMIN=ADMIN,
                           BLOOD_BANK_ADD_STOCK=BLOOD_BANK_ADD_STOCK,
                           BLOOD_BANK_EDIT_STOCK=BLOOD_BANK_EDIT_STOCK,
                           BLOOD_BANK_DELETE_STOCK=BLOOD_BANK_DELETE_STOCK,
                           BLOOD_BANK_RESTORE_STOCK=BLOOD_BANK_RESTORE_STOCK)


@admin.route(BLOOD_BANK_ADD_STOCK, methods=['POST'], endpoint='blood_bank_add_stock')
def blood_bank_add_stock():
    try:
        # Validate required fields
        required_fields = ['product_code', 'blood_type', 'component_type',
                           'quantity', 'collection_date', 'expiry_date',
                           'storage_location']
        if not all(request.form.get(field) for field in required_fields):
            flash('Please fill in all required fields', 'danger')
            return redirect(request.url)

        # Create new product
        new_product = BloodProduct(
            product_code=request.form['product_code'],
            blood_type=request.form['blood_type'],
            component_type=request.form['component_type'],
            quantity=int(request.form['quantity']),
            collection_date=datetime.strptime(request.form['collection_date'], '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date(),
            storage_location=request.form['storage_location'],
            batch_number=generate_batch_number(),
            notes=request.form.get('notes', ''),
            status=calculate_product_status(datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date())
        )

        db.session.add(new_product)
        db.session.commit()
        flash(f'Blood product added successfully! Batch: {new_product.batch_number}', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding product: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_STOCK)


@admin.route(BLOOD_BANK_EDIT_STOCK + '/<int:product_id>', methods=['POST'], endpoint='blood_bank_edit_stock')
def blood_bank_edit_stock(product_id):
    product = BloodProduct.query.get_or_404(product_id)
    try:
        # Update editable fields only
        product.blood_type = request.form['blood_type']
        product.component_type = request.form['component_type']
        product.quantity = int(request.form['quantity'])
        product.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        product.storage_location = request.form['storage_location']
        product.notes = request.form.get('notes', '')
        product.status = calculate_product_status(product.expiry_date)
        product.updated_at = datetime.now()

        db.session.commit()
        flash('Blood product updated successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating product: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_STOCK)


@admin.route(BLOOD_BANK_DELETE_STOCK + '/<int:product_id>', methods=['POST'], endpoint='blood_bank_delete_stock')
def blood_bank_delete_stock(product_id):
    product = BloodProduct.query.get_or_404(product_id)
    try:
        product.is_deleted = True
        product.deleted_at = datetime.now()
        db.session.commit()
        flash('Blood product archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving product: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_STOCK)


@admin.route(BLOOD_BANK_RESTORE_STOCK + '/<int:product_id>', methods=['POST'], endpoint='blood_bank_restore_stock')
def blood_bank_restore_stock(product_id):
    product = BloodProduct.query.get_or_404(product_id)
    try:
        product.is_deleted = False
        product.deleted_at = None
        product.status = calculate_product_status(product.expiry_date)
        db.session.commit()
        flash('Blood product restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring product: {str(e)}', 'danger')
    return redirect(ADMIN + BLOOD_BANK_STOCK)