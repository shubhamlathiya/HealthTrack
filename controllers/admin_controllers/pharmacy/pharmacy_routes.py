from datetime import datetime, timedelta

from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import PHARMACY_MEDICINE_LIST, PHARMACY_MEDICINE_ADD, ADMIN, \
    PHARMACY_MEDICINE_EDIT, PHARMACY_MEDICINE_DELETE, PHARMACY_MEDICINE_RESTOCK, PHARMACY_MEDICINE_TRANSACTIONS, \
    PHARMACY_MEDICINE_DISPENSE, PHARMACY_MEDICINE_RESTORE
from middleware.auth_middleware import token_required
from models.medicineModel import Medicine, StockTransaction, MedicineCategory, MedicineCompany
from utils.config import db


@admin.route(PHARMACY_MEDICINE_LIST, methods=['GET'], endpoint='medicine-list')
@token_required
def pharmacy_medicine_list(current_user):
    medicines = Medicine.query.filter_by(is_deleted=0).order_by(Medicine.name).all()
    categories = MedicineCategory.query.filter_by(is_deleted=0).order_by(MedicineCategory.name).all()
    companies = MedicineCompany.query.filter_by(is_deleted=0).order_by(MedicineCompany.name).all()
    archived_medicines = Medicine.query.filter_by(is_deleted=1).order_by(Medicine.deleted_at.desc()).all()

    return render_template('admin_templates/pharmacy/medicine_inventory.html', medicines=medicines,
                           categories=categories, companies=companies, datetime=datetime,
                           timedelta=timedelta, archived_medicines=archived_medicines)


@admin.route(PHARMACY_MEDICINE_ADD, methods=['POST'], endpoint='medicine-add')
@token_required
def add_medicine(current_user):
    print(current_user)
    print(request.form)
    try:
        last_case = Medicine.query.order_by(Medicine.id.desc()).first()
        medicine_number = f"{int(last_case.id) + 1000 if last_case else 1000}"
        # Create new medicine
        medicine = Medicine(
            medicine_number=medicine_number,
            name=request.form.get('name'),
            description=request.form.get('description'),
            category_id=request.form.get('category_id'),
            company_id=request.form.get('company_id'),
            purchase_price=float(request.form.get('purchase_price')),
            selling_price=float(request.form.get('selling_price')),
            purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date(),
            current_stock=int(request.form.get('current_stock')),
            min_stock_level=int(request.form.get('min_stock_level')),
            location=request.form.get('location'),
            barcode=request.form.get('barcode')
        )

        db.session.add(medicine)
        db.session.flush()  # get medicine.id without committing

        # Record initial stock transaction
        if int(request.form.get('current_stock')) > 0:
            transaction = StockTransaction(
                medicine_id=medicine.id,
                transaction_type='initial',
                quantity=int(request.form.get('current_stock')),
                balance=int(request.form.get('current_stock')),
                notes='Initial stock',
                user_id=current_user
            )
            db.session.add(transaction)

        db.session.commit()
        flash('Medicine added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)


@admin.route(PHARMACY_MEDICINE_EDIT + '/<int:id>', methods=['POST'], endpoint='medicine-edit')
@token_required
def edit_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        medicine.name = request.form.get('name')
        medicine.description = request.form.get('description')
        medicine.category_id = request.form.get('category_id')
        medicine.company_id = request.form.get('company_id')
        medicine.purchase_price = float(request.form.get('purchase_price'))
        medicine.selling_price = float(request.form.get('selling_price'))
        medicine.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date()
        medicine.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
        medicine.min_stock_level = int(request.form.get('min_stock_level'))
        medicine.location = request.form.get('location')
        medicine.barcode = request.form.get('barcode')

        db.session.commit()
        flash('Medicine updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)


@admin.route(PHARMACY_MEDICINE_DELETE + '/<int:id>', methods=['POST'], endpoint='medicine-delete')
@token_required
def delete_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        # Delete associated transactions first
        StockTransaction.query.filter_by(medicine_id=id).update({
            'is_deleted': True,
            'deleted_at': datetime.utcnow()
        })

        medicine.is_deleted = True
        medicine.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Medicine deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)


@admin.route(PHARMACY_MEDICINE_RESTOCK + '/<int:id>', methods=['POST'], endpoint='medicine-restock')
@token_required
def restock_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        quantity = int(request.form.get('quantity'))
        if quantity <= 0:
            flash('Quantity must be positive', 'warning')
            return redirect("/admin/medicines")

        medicine.current_stock += quantity

        transaction = StockTransaction(
            medicine_id=id,
            transaction_type='restock',
            quantity=quantity,
            balance=medicine.current_stock,
            notes=request.form.get('notes', ''),
            reference=request.form.get('reference', ''),
            user_id=current_user
        )

        db.session.add(transaction)
        db.session.commit()
        flash(f'Successfully restocked {quantity} units of {medicine.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restocking medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)


@admin.route(PHARMACY_MEDICINE_TRANSACTIONS + '/<int:id>', methods=['POST'], endpoint='medicine-transactions123')
@token_required
def transactions_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)

    try:
        transaction_type = request.form.get('transaction_type', '')
        quantity = int(request.form.get('quantity'))
        reference = request.form.get('reference', '')
        notes = request.form.get('notes', '')

        if quantity <= 0:
            flash('Quantity must be positive', 'warning')
            return redirect(f"/admin/medicines/forward-post/{id}")

        if transaction_type in ["dispense", "loss"] and medicine.current_stock < quantity:
            flash(f'Not enough stock. Only {medicine.current_stock} units available', 'danger')
            return redirect(f"/admin/medicines/forward-post/{id}")

        # Handle each transaction type
        if transaction_type == "dispense":
            medicine.current_stock -= quantity
            txn_quantity = -quantity
            flash_msg = f'Successfully dispensed {quantity} units of {medicine.name}'
        elif transaction_type == "restock":
            medicine.current_stock += quantity
            txn_quantity = quantity
            flash_msg = f'Successfully restocked {quantity} units of {medicine.name}'
        elif transaction_type == "return":
            medicine.current_stock += quantity
            txn_quantity = -quantity
            flash_msg = f'Successfully returned {quantity} units of {medicine.name}'
        elif transaction_type == "loss":
            medicine.current_stock -= quantity
            txn_quantity = -quantity
            flash_msg = f'Successfully recorded loss of {quantity} units of {medicine.name}'
        else:
            flash("Invalid transaction type", "danger")
            return redirect(f"/admin/medicines/forward-post/{id}")

        # Create stock transaction
        transaction = StockTransaction(
            medicine_id=id,
            transaction_type=transaction_type,
            quantity=txn_quantity,
            balance=medicine.current_stock,
            notes=notes,
            reference=reference,
            user_id=current_user
        )

        db.session.add(transaction)
        db.session.commit()
        flash(flash_msg, 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error processing medicine transaction: {str(e)}', 'danger')

    return redirect(f"/admin/medicines/forward-post/{id}")


@admin.route('/medicines/forward-post/<int:id>', methods=['GET'])
def forward_to_post(id):
    return f'''
    <form id="forwardForm" action="/admin/pharmacy/transactions-medicine" method="post">
        <input type="hidden" name="medicine_id" value="{id}" />
    </form>
    <script>document.getElementById("forwardForm").submit();</script>
    '''


@admin.route(PHARMACY_MEDICINE_DISPENSE + '/<int:id>', methods=['POST'], endpoint='medicine-dispense')
@token_required
def dispense_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        quantity = int(request.form.get('quantity'))
        if quantity <= 0:
            flash('Quantity must be positive', 'warning')
            return redirect("/admin/medicines")

        if medicine.current_stock < quantity:
            flash(f'Not enough stock. Only {medicine.current_stock} units available', 'danger')
            return redirect("/admin/medicines")

        medicine.current_stock -= quantity

        transaction = StockTransaction(
            medicine_id=id,
            transaction_type='dispense',
            quantity=-quantity,
            balance=medicine.current_stock,
            notes=request.form.get('notes', ''),
            reference=request.form.get('reference', ''),
            user_id=current_user
        )

        db.session.add(transaction)
        db.session.commit()
        flash(f'Successfully dispensed {quantity} units of {medicine.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error dispensing medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)


@admin.route(PHARMACY_MEDICINE_TRANSACTIONS, methods=['POST'], endpoint='medicine-transactions')
@token_required
def medicine_transactions(current_user):
    medicine_id = request.form.get('medicine_id')
    medicine = Medicine.query.get_or_404(medicine_id)
    transactions = StockTransaction.query.filter_by(medicine_id=medicine_id).order_by(
        StockTransaction.created_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_transactions.html', medicine=medicine,
                           transactions=transactions, datetime=datetime,
                           timedelta=timedelta)


@admin.route(PHARMACY_MEDICINE_RESTORE + '/<int:id>', methods=['POST'])
@token_required
def restore_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        StockTransaction.query.filter_by(medicine_id=id).update({
            'is_deleted': False,
            'deleted_at': None
        })
        medicine.is_deleted = False
        medicine.deleted_at = None
        db.session.commit()
        flash('Medicine restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_LIST)
