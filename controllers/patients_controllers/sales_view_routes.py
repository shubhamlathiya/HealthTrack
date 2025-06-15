import datetime
from decimal import Decimal

from flask import render_template, abort

from controllers.constant.adminPathConstant import PHARMACY_SALES_VIEW
from controllers.constant.patientPathConstant import PHARMACY_SALES_LIST, PHARMACY_SALES_PRINT, PATIENT
from controllers.patients_controllers import patients
from middleware.auth_middleware import token_required
from models import UserRole, MedicineSale, Patient, MedicineSaleItem
from utils.config import db


# --- Sales List (Admin Only) ---
@patients.route(PHARMACY_SALES_LIST, methods=['GET'], endpoint="sales_list")
@token_required(allowed_roles=[UserRole.PATIENT.name])
def sales_list(current_user):
    """
    Retrieves and displays a list of all medicine sales for administrators.
    Includes both active and archived sales.
    """
    # Fetch active sales
    patient = Patient.query.filter_by(user_id=current_user).first()

    sales = MedicineSale.query.options(
        db.joinedload(MedicineSale.doctor),
        db.joinedload(MedicineSale.items)
    ).filter_by(patient_id=patient.patient_id, is_deleted=False).order_by(MedicineSale.created_at.desc()).all()

    sales_data = []
    for sale in sales:

        doctor_name = "N/A"
        if sale.doctor:
            doctor_name = f"{sale.doctor.first_name} {sale.doctor.last_name}"

        # Ensure Decimal types for calculations to avoid floating-point issues
        net_amount = Decimal(str(sale.net_amount))
        payment_amount = Decimal(str(sale.payment_amount))

        balance_amount = net_amount - payment_amount
        refund_amount = Decimal('0.00')
        balance_due = Decimal('0.00')

        if balance_amount < 0:
            refund_amount = abs(balance_amount)
        else:
            balance_due = balance_amount

        sales_data.append({
            'id': sale.id,
            'bill_no': sale.bill_no,
            'patient_id': sale.patient_id,
            'patient_name': f"{patient.first_name} {patient.last_name}",
            'sale_date': sale.created_at.strftime('%Y-%m-%d %I:%M %p'),
            'doctor_name': doctor_name,
            'total_amount': sale.total_amount,
            'discount_amount': sale.discount_amount,
            'net_amount': net_amount,
            'paid_amount': payment_amount,
            'refund_amount': refund_amount,
            'balance_due': balance_due,
            'items_count': len(sale.items) if sale.items else 0,
            'status': 'Paid' if balance_due <= Decimal('0.01') else 'Due'
        })




    return render_template('patient_templates/invoice/invoice_list.html',
                           sales=sales_data,
                           datetime=datetime.datetime,
                           PATIENT=PATIENT,
                           PHARMACY_SALES_PRINT=PHARMACY_SALES_PRINT,
                           PHARMACY_SALES_VIEW=PHARMACY_SALES_VIEW,
                          )


@patients.route(PHARMACY_SALES_VIEW + '/<int:sale_id>', methods=['GET'], endpoint="view_sale_for_patient")
@token_required(allowed_roles=[UserRole.PATIENT.name]) # This would be a new decorator for patient authentication
def view_sale(current_user, sale_id):
    """
    Allows a patient to view a specific medicine sale bill,
    only if the bill belongs to them.
    """
    # Eagerly load related data
    sale = MedicineSale.query.options(
        db.joinedload(MedicineSale.items).joinedload(MedicineSaleItem.medicine),
        db.joinedload(MedicineSale.items).joinedload(MedicineSaleItem.batch),
        db.joinedload(MedicineSale.doctor)
    ).filter_by(id=sale_id, is_deleted=False).first()

    if not sale:
        # If the sale doesn't exist or doesn't belong to the patient
        abort(404, description="Sale not found or you don't have permission to view this sale.")

    due_amount = sale.net_amount - sale.payment_amount

    return render_template('patient_templates/invoice/invoice_details.html',
                           sale=sale,
                           items=sale.items,
                           due_amount=due_amount,
                           datetime=datetime.datetime,
                           PATIENT=PATIENT,  # Consider if 'ADMIN' constants are relevant for patient view
                           PHARMACY_SALES_LIST=PHARMACY_SALES_LIST,  # This link might lead to an admin list, reconsider
                           PHARMACY_SALES_PRINT=PHARMACY_SALES_PRINT,
                           )


@patients.route(PHARMACY_SALES_PRINT + '/<int:sale_id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.PATIENT.name])  # This would be a new decorator for patient authentication
def print_sale_bill(current_user, sale_id):
    """
    Allows a patient to print a specific medicine sale bill,
    only if the bill belongs to them.
    """
    # Eagerly load the sale, its items, and related medicine, doctor, and patient data
    sale = MedicineSale.query.options(
        db.joinedload(MedicineSale.items).joinedload(MedicineSaleItem.medicine),
        db.joinedload(MedicineSale.doctor),
    ).filter_by(id=sale_id, is_deleted=False).first()

    if not sale:
        # If the sale doesn't exist or doesn't belong to the patient
        abort(404, description="Bill not found or you don't have permission to print this bill.")

    patients = Patient.query.filter_by(patient_id=sale.patient_id).first()
    if not patients:
        abort(500, description="Patient details not found for this bill.")

    return render_template(
        'admin_templates/pharmacy/sale_print_view.html',
        patients=patients,
        sale=sale,
        items=sale.items,
        datetime=datetime
    )
