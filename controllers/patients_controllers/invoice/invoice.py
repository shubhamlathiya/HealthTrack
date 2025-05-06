from datetime import datetime

from flask import render_template, redirect, url_for, flash

from controllers.patients_controllers import patients
from models.patientModel import PatientPayment, Patient
from models.roomModel import RoomCharge
from utils.config import db


@patients.route('/invoices')
def invoice_list():
    # Get all non-deleted payments
    payments = PatientPayment.query.filter_by(is_deleted=False).all()
    return render_template('patient_templates/invoice/invoice_list.html', payments=payments)


@patients.route('/invoice/<int:payment_id>')
def invoice_details(payment_id):
    # Get the payment details
    payment = PatientPayment.query.get_or_404(payment_id)
    patient = Patient.query.get(payment.patient_id)
    room_charge = RoomCharge.query.get(payment.room_charge_id) if payment.room_charge_id else None

    return render_template('patient_templates/invoice/invoice_details.html',
                           payment=payment,
                           patient=patient,
                           room_charge=room_charge)


@patients.route('/invoice/pay/<int:payment_id>')
def pay_invoice(payment_id):
    payment = PatientPayment.query.get_or_404(payment_id)
    payment.status = 'paid'
    payment.payment_date = datetime.now()
    db.session.commit()
    flash('Payment marked as paid successfully!', 'success')
    return redirect(url_for('invoice_details', payment_id=payment_id))
