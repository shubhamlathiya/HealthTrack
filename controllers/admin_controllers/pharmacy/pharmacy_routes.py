from datetime import datetime

from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import PHARMACY_MEDICINE_LIST
from models.medicineModel import Medicine, StockTransaction, MedicineCategory, MedicineCompany
from utils.config import db


@admin.route(PHARMACY_MEDICINE_LIST, methods=['GET'], endpoint='medicine-list')
def pharmacy_medicine_list():
    return render_template("admin_templates/pharmacy/medicine_list.html")


@admin.route('/medicines' , methods=['GET'])
def medicine_inventory():
    medicines = Medicine.query.order_by(Medicine.name).all()
    return render_template('admin_templates/pharmacy/medicine_inventory.html', medicines=medicines)


@admin.route('/medicines/add', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        try:
            # Create new medicine
            medicine = Medicine(
                medicine_number=request.form.get('medicine_number'),
                name=request.form.get('name'),
                description=request.form.get('description'),
                category_id=request.form.get('category_id'),
                company_id=request.form.get('company_id'),
                purchase_price=float(request.form.get('purchase_price')),
                selling_price=float(request.form.get('selling_price')),
                purchase_date=datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date(),
                current_stock=int(request.form.get('initial_stock')),
                min_stock_level=int(request.form.get('min_stock_level')),
                location=request.form.get('location'),
                barcode=request.form.get('barcode')
            )

            db.session.add(medicine)

            # Record initial stock transaction
            if int(request.form.get('initial_stock')) > 0:
                transaction = StockTransaction(
                    medicine_id=medicine.id,
                    transaction_type='initial',
                    quantity=int(request.form.get('initial_stock')),
                    balance=int(request.form.get('initial_stock')),
                    notes='Initial stock',
                    user_id=current_user.id
                )
                db.session.add(transaction)

            db.session.commit()
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('admin.medicine_inventory'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding medicine: {str(e)}', 'danger')

    categories = MedicineCategory.query.order_by(MedicineCategory.name).all()
    companies = MedicineCompany.query.order_by(MedicineCompany.name).all()
    return render_template('admin_templates/pharmacy/add_medicine.html', categories=categories, companies=companies)


@admin.route('/medicines/<int:id>/edit', methods=['GET', 'POST'])
def edit_medicine(id):
    medicine = Medicine.query.get_or_404(id)

    if request.method == 'POST':
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
            return redirect(url_for('admin.medicine_inventory'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating medicine: {str(e)}', 'danger')

    categories = MedicineCategory.query.order_by(MedicineCategory.name).all()
    companies = MedicineCompany.query.order_by(MedicineCompany.name).all()
    return render_template('admin_templates/pharmacy/edit_medicine.html', medicine=medicine, categories=categories, companies=companies)


@admin.route('/medicines/<int:id>/delete', methods=['POST'])
def delete_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    try:
        # Delete associated transactions first
        StockTransaction.query.filter_by(medicine_id=id).delete()
        db.session.delete(medicine)
        db.session.commit()
        flash('Medicine deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medicine: {str(e)}', 'danger')
    return redirect(url_for('admin.medicine_inventory'))


@admin.route('/medicines/<int:id>/restock', methods=['POST'])
def restock_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    try:
        quantity = int(request.form.get('quantity'))
        if quantity <= 0:
            flash('Quantity must be positive', 'warning')
            return redirect(url_for('admin.medicine_inventory'))

        medicine.current_stock += quantity

        transaction = StockTransaction(
            medicine_id=id,
            transaction_type='restock',
            quantity=quantity,
            balance=medicine.current_stock,
            notes=request.form.get('notes', ''),
            user_id=current_user.id
        )

        db.session.add(transaction)
        db.session.commit()
        flash(f'Successfully restocked {quantity} units of {medicine.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restocking medicine: {str(e)}', 'danger')
    return redirect(url_for('admin.medicine_inventory'))


@admin.route('/medicines/<int:id>/dispense', methods=['POST'])
def dispense_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    try:
        quantity = int(request.form.get('quantity'))
        if quantity <= 0:
            flash('Quantity must be positive', 'warning')
            return redirect(url_for('admin.medicine_inventory'))

        if medicine.current_stock < quantity:
            flash(f'Not enough stock. Only {medicine.current_stock} units available', 'danger')
            return redirect(url_for('admin.medicine_inventory'))

        medicine.current_stock -= quantity

        transaction = StockTransaction(
            medicine_id=id,
            transaction_type='dispense',
            quantity=-quantity,
            balance=medicine.current_stock,
            notes=request.form.get('notes', ''),
            reference=request.form.get('reference', ''),
            user_id=current_user.id
        )

        db.session.add(transaction)
        db.session.commit()
        flash(f'Successfully dispensed {quantity} units of {medicine.name}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error dispensing medicine: {str(e)}', 'danger')
    return redirect(url_for('admin.medicine_inventory'))


@admin.route('/medicines/<int:id>/transactions')
def medicine_transactions(id):
    medicine = Medicine.query.get_or_404(id)
    transactions = StockTransaction.query.filter_by(medicine_id=id).order_by(StockTransaction.created_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_transactions.html', medicine=medicine, transactions=transactions)