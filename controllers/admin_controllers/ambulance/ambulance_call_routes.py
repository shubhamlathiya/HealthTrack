import datetime
import io
import traceback
from decimal import Decimal

import pandas as pd
from flask import render_template, request, redirect, flash, jsonify, send_file, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle, Table, Paragraph, Spacer, SimpleDocTemplate
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_AMBULANCE_CALL_LIST, AMBULANCE_AMBULANCE_ADD_CALL, \
    AMBULANCE_AMBULANCE_DELETE_CALL, AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL, \
    AMBULANCE_AMBULANCE_RESTORE_CALL, ADMIN, AMBULANCE_AMBULANCE_CALL_LIST_PRINT, AMBULANCE_AMBULANCE_EXPORT_CALLS, \
    AMBULANCE_AMBULANCE_CALL_VIEW, AMBULANCE_AMBULANCE_ADD_PAYMENT_TO_CALL
from middleware.auth_middleware import token_required
from models import UserRole
# Corrected model imports based on updated names
from models.ambulanceModel import AmbulanceCall, Ambulance, Driver, AdditionalCharge, AmbulanceCategory, \
    AmbulanceChargeItem
from models.patientModel import Patient
from utils.config import db
from utils.create_new_patient import create_new_patient


@admin.route(AMBULANCE_AMBULANCE_CALL_LIST, methods=['GET'], endpoint='ambulance-call-list')
def ambulance_call_list():
    calls = AmbulanceCall.query.filter_by(is_deleted=False).order_by(AmbulanceCall.call_time.desc()).all()
    ambulances = Ambulance.query.filter_by(is_active=True, is_available=True).all()
    drivers = Driver.query.filter_by(is_active=True).all()
    deleted_calls = AmbulanceCall.query.filter_by(is_deleted=True).all()
    # Corrected model name
    charge_categories = AmbulanceCategory.query.filter_by(is_active=True).all()
    # Corrected model name
    charge_items = AmbulanceChargeItem.query.filter_by(is_active=True).all()

    return render_template("admin_templates/ambulance/ambulance-call-list.html",
                           calls=calls,
                           ambulances=ambulances,
                           drivers=drivers,
                           deleted_calls=deleted_calls,
                           charge_categories=charge_categories,
                           charge_items=charge_items,
                           ADMIN=ADMIN,
                           AMBULANCE_AMBULANCE_ADD_CALL=AMBULANCE_AMBULANCE_ADD_CALL,
                           AMBULANCE_AMBULANCE_CALL_VIEW=AMBULANCE_AMBULANCE_CALL_VIEW,
                           AMBULANCE_AMBULANCE_DELETE_CALL=AMBULANCE_AMBULANCE_DELETE_CALL,
                           AMBULANCE_AMBULANCE_RESTORE_CALL=AMBULANCE_AMBULANCE_RESTORE_CALL,
                           AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL=AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL,
                           AMBULANCE_AMBULANCE_CALL_LIST_PRINT=AMBULANCE_AMBULANCE_CALL_LIST_PRINT,
                           AMBULANCE_AMBULANCE_EXPORT_CALLS=AMBULANCE_AMBULANCE_EXPORT_CALLS,
                           datetime=datetime.datetime
                           )


@admin.route(AMBULANCE_AMBULANCE_ADD_CALL, methods=['GET'], endpoint='ambulance-add-call')
def add_ambulance_call():
    ambulances = Ambulance.query.filter_by(is_active=True, is_available=True).all()
    drivers = Driver.query.filter_by(is_active=True).all()
    # Corrected model name
    charge_categories = AmbulanceCategory.query.filter_by(is_active=True).all()
    # Corrected model name
    charge_items = AmbulanceChargeItem.query.filter_by(is_active=True).all()

    return render_template("admin_templates/ambulance/new-ambulance-call.html",
                           ambulances=ambulances,
                           drivers=drivers,
                           charge_categories=charge_categories,
                           charge_items=charge_items,
                           ADMIN=ADMIN,
                           AMBULANCE_AMBULANCE_ADD_CALL=AMBULANCE_AMBULANCE_ADD_CALL,
                           datetime=datetime.datetime
                           )


@admin.route(AMBULANCE_AMBULANCE_ADD_CALL, methods=['POST'], endpoint='ambulance-add-call-post')
def save_ambulance_call():
    try:
        print(request.form)  # For debugging, shows incoming form data

        # --- Patient Handling ---
        patient_record = None
        patient_id_str = request.form.get('patient_id')
        patient_name_val = None
        patient_age_val = None
        patient_gender_val = None

        if patient_id_str:
            # An existing patient was selected
            try:
                patient_id = int(patient_id_str)
                patient_record = Patient.query.get(patient_id)
                if not patient_record:
                    flash('Selected patient not found.', 'danger')
                    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

                # Use patient's actual data from the database
                patient_name_val = f"{patient_record.first_name} {patient_record.last_name}" if patient_record.last_name else patient_record.first_name
                patient_age_val = patient_record.age
                patient_gender_val = patient_record.gender

            except ValueError:
                flash('Invalid patient ID provided.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)
        else:
            # No patient_id means a new patient needs to be created
            patient_name_val = request.form.get('patient_name')
            patient_age_str = request.form.get('patient_age')
            patient_gender_val = request.form.get('patient_gender')
            patient_email_val = request.form.get('patient_email', '')
            patient_phone_val = request.form.get('patient_phone', '')

            if not patient_name_val or not patient_age_str or not patient_gender_val:
                flash('New patient name, age, and gender are required.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            try:
                patient_age_val = int(patient_age_str)
            except ValueError:
                flash('Patient age must be a valid number.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            # Assuming create_new_patient is a helper function that creates and returns a Patient object
            # and potentially adds it to the session but doesn't commit
            patient_record = create_new_patient({
                'first_name': patient_name_val.split(' ')[0],  # Adjust if patient_name can be full name
                'last_name': ' '.join(patient_name_val.split(' ')[1:]) if ' ' in patient_name_val else '',
                'email': patient_email_val,
                'phone': patient_phone_val,
                'age': patient_age_val,
                'gender': patient_gender_val
            })
            db.session.add(patient_record)
            db.session.flush()  # Flush to get the patient_record.id for linking

        # --- Create New Ambulance Call Record ---
        ambulance_call = AmbulanceCall()

        # Generate a unique call number
        today = datetime.datetime.now()
        last_call = AmbulanceCall.query.order_by(AmbulanceCall.id.desc()).first()
        sequence_num = 1 if not last_call else last_call.id + 1
        ambulance_call.call_number = f"AMB-{today.year}-{today.month:02d}{today.day:02d}-{sequence_num:03d}"

        # Assign patient details to the AmbulanceCall record
        ambulance_call.patient_id = patient_record.id
        ambulance_call.patient_name = patient_name_val
        ambulance_call.patient_age = patient_age_val
        ambulance_call.patient_gender = patient_gender_val

        # --- Assign Core Ambulance Call Details ---
        ambulance_call.pickup_location = request.form.get('pickup_location')
        ambulance_call.destination = request.form.get('destination', '')

        # Convert datetime strings to datetime objects
        call_time_str = request.form.get('call_time')
        # datetime.fromisoformat can handle microseconds directly, no trimming needed
        ambulance_call.call_time = datetime.datetime.fromisoformat(call_time_str) if call_time_str else None

        completion_time_str = request.form.get('completion_time')
        # Ensure completion_time is parsable, handle potential errors
        try:
            ambulance_call.completion_time = datetime.datetime.fromisoformat(
                completion_time_str) if completion_time_str else None
        except ValueError:
            flash("Invalid completion time format. Please use YYYY-MM-DDTHH:MM.", 'danger')
            return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

        # Convert numerical fields to floats/ints
        distance_str = request.form.get('distance')
        ambulance_call.distance = float(distance_str) if distance_str else 0.0

        ambulance_id_str = request.form.get('ambulance_id')
        ambulance_call.ambulance_id = int(ambulance_id_str) if ambulance_id_str else None

        driver_id_str = request.form.get('driver_id')
        ambulance_call.driver_id = int(driver_id_str) if driver_id_str else None

        ambulance_call.notes = request.form.get('notes', '')
        ambulance_call.status = 'Pending'  # Default status for a new call

        # --- Financial Calculations (Backend-Driven for Accuracy) ---
        # Fetch the selected ambulance to get its rates
        current_ambulance = Ambulance.query.get(ambulance_call.ambulance_id)

        ambulance_call.base_charge = current_ambulance.base_rate if current_ambulance else 0.0

        # Add the main ambulance_call object to the session
        db.session.add(ambulance_call)
        db.session.flush()  # Flush to ensure ambulance_call.id is available for AdditionalCharge entries

        # --- ADDITIONAL CHARGES HANDLING - ADAPTED FOR NEW FORM STRUCTURE ---
        total_additional_charges_calculated = 0.0

        # Loop through potential indices of charge_categories
        # Assuming charges are indexed from 0 upwards (e.g., charge_categories[0], charge_categories[1])
        i = 0
        while True:
            category_id_key = f'charge_categories[{i}][category_id]'
            charge_item_id_key = f'charge_categories[{i}][charge_id]'  # Note: 'charge_id' in your form data
            amount_key = f'charge_categories[{i}][amount]'
            note_key = f'charge_categories[{i}][note]'

            category_id_str = request.form.get(category_id_key)
            charge_item_id_str = request.form.get(charge_item_id_key)
            amount_str = request.form.get(amount_key)
            note = request.form.get(note_key, '')

            # If no more entries for this index, break the loop
            if not charge_item_id_str:  # Use charge_item_id as the primary indicator for an entry
                break

            try:
                # Convert to int/float and validate existence
                charge_item_id = int(charge_item_id_str)
                amount = float(amount_str)

                # Check if the AmbulanceChargeItem exists in the database
                existing_charge_item = AmbulanceChargeItem.query.get(charge_item_id)

                if existing_charge_item:
                    charge = AdditionalCharge(
                        call_id=ambulance_call.id,
                        charge_item_id=charge_item_id,
                        amount=amount,
                        notes=note
                    )
                    db.session.add(charge)
                    total_additional_charges_calculated += amount
                else:
                    print(
                        f"Warning: Skipping additional charge entry. Charge Item ID '{charge_item_id_str}' not found in AmbulanceChargeItem master data.")
                    flash(f"Warning: Charge item with ID '{charge_item_id_str}' not found. Skipping additional charge.",
                          'warning')

            except (ValueError, TypeError) as e:
                print(
                    f"Warning: Skipping invalid additional charge entry at index {i}. Details: {e}. Item ID: '{charge_item_id_str}', Amount: '{amount_str}'.")
                flash(f"Warning: Invalid format for an additional charge entry (index {i}). Skipping.", 'warning')
            except Exception as e:
                print(f"Unexpected error processing additional charge at index {i}: {e}")
                traceback.print_exc()
                flash(f"An unexpected error occurred with an additional charge entry (index {i}). Skipping.", 'warning')

            i += 1  # Move to the next index

        ambulance_call.additional_charges_total = total_additional_charges_calculated

        # --- Finalize Financial Calculations ---
        # Recalculate subtotal based on backend-derived values
        ambulance_call.subtotal = ambulance_call.base_charge + ambulance_call.additional_charges_total

        # Assign discount and tax percentages from the frontend, then recalculate amounts
        # Using .get with a default of '0' for safe float conversion
        ambulance_call.discount_percent = float(request.form.get('discount_percent', '0'))
        ambulance_call.discount_amount = float(request.form.get('discount_amount', '0'))

        # If discount percentage was applied, recalculate amount to ensure consistency
        if ambulance_call.discount_percent > 0:
            ambulance_call.discount_amount = ambulance_call.subtotal * (ambulance_call.discount_percent / 100)
        # Else: if discount_amount was entered by user directly, it remains as received from form

        ambulance_call.tax_percent = float(request.form.get('tax_percent', '0'))
        taxable_amount = ambulance_call.subtotal - ambulance_call.discount_amount
        ambulance_call.tax_amount = taxable_amount * (ambulance_call.tax_percent / 100)

        # Final total amount calculation
        ambulance_call.total_amount = taxable_amount + ambulance_call.tax_amount

        # Payment details - ensure 'paid_amount' and 'due_amount' are read correctly
        ambulance_call.payment_mode = request.form.get('payment_mode', 'Cash')
        ambulance_call.payment_amount = float(
            request.form.get('paid_amount', '0'))  # Use 'paid_amount' from your form data

        # If you have a 'due_amount' column in AmbulanceCall:
        # ambulance_call.due_amount = float(request.form.get('due_amount', '0'))

        # Commit all changes to the database
        db.session.commit()
        flash('Ambulance call added successfully!', 'success')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

    except Exception as e:
        db.session.rollback()  # Rollback changes if any error occurs
        traceback.print_exc()  # Print full traceback for debugging
        flash(f'Error adding ambulance call: {str(e)}', 'danger')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_CALL_VIEW + '/<int:call_id>', methods=['GET'], endpoint="view_ambulance_call")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def view_ambulance_call(current_user, call_id):
    """
    Displays the detailed view of a single ambulance call, including related patient,
    ambulance, driver, and billing information with additional charges.
    """
    # Eagerly load all necessary related data to avoid N+1 queries in the template
    call = AmbulanceCall.query.options(
        joinedload(AmbulanceCall.ambulance),  # Load related Ambulance object
        joinedload(AmbulanceCall.driver),  # Load related Driver object
        # Load AdditionalCharge entries and their associated ChargeItems
        joinedload(AmbulanceCall.additional_charge_entries).joinedload(AdditionalCharge.charge_item)
    ).get_or_404(call_id)

    # Calculate due amount. Use Decimal for precision in financial calculations.
    # Ensure call.total_amount and call.payment_amount are treated as Decimals
    # before calculation to avoid floating point inaccuracies.
    total_amount_decimal = Decimal(str(call.total_amount)) if call.total_amount is not None else Decimal('0.00')
    payment_amount_decimal = Decimal(str(call.payment_amount)) if call.payment_amount is not None else Decimal('0.00')
    due_amount = total_amount_decimal - payment_amount_decimal

    # Pass all necessary data to the template
    return render_template('admin_templates/ambulance/view_ambulance_call.html',
                           call=call,
                           due_amount=float(due_amount),  # Convert back to float for template display if needed
                           datetime=datetime.datetime,  # For using datetime in template
                           # Pass constants/route prefixes to the template for button URLs
                           ADMIN=ADMIN,
                           AMBULANCE_AMBULANCE_CALL_LIST=AMBULANCE_AMBULANCE_CALL_LIST,
                           AMBULANCE_AMBULANCE_PRINT_BILL=AMBULANCE_AMBULANCE_CALL_LIST_PRINT,
                           AMBULANCE_AMBULANCE_DELETE_CALL=AMBULANCE_AMBULANCE_DELETE_CALL,

                           AMBULANCE_AMBULANCE_ADD_PAYMENT_TO_CALL=AMBULANCE_AMBULANCE_ADD_PAYMENT_TO_CALL
                           )


@admin.route(AMBULANCE_AMBULANCE_ADD_PAYMENT_TO_CALL + '/<int:call_id>', methods=['POST'],
             endpoint='add_payment_to_call')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_payment_to_call(current_user, call_id):
    """
    Handles the submission of the 'Add Payment' modal for an ambulance call.
    Updates the payment amount, mode, and notes for the specific call.
    """
    call = AmbulanceCall.query.get_or_404(call_id)

    if request.method == 'POST':
        try:
            payment_amount_str = request.form.get('amount')
            payment_date_str = request.form.get('payment_date')
            payment_mode = request.form.get('payment_mode')
            note = request.form.get('note')

            # --- Input Validation ---
            if not payment_amount_str or not payment_date_str or not payment_mode:
                flash('Payment amount, date, and mode are required.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            try:
                new_payment_amount = Decimal(payment_amount_str)
            except (ValueError, TypeError):
                flash('Invalid payment amount. Please enter a valid number.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            try:
                payment_date = datetime.datetime.strptime(payment_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid payment date format.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            # Use the current due amount for validation, handling potential floating point precision
            current_total = Decimal(str(call.total_amount)) if call.total_amount is not None else Decimal('0.00')
            current_paid = Decimal(str(call.payment_amount)) if call.payment_amount is not None else Decimal('0.00')
            current_due = current_total - current_paid

            # Ensure the new payment doesn't exceed the current due amount (allowing for tiny floating point differences)
            if new_payment_amount <= Decimal('0'):
                flash('Payment amount must be greater than zero.', 'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            if new_payment_amount > current_due + Decimal('0.01'):  # Allow a tiny margin for float comparisons
                flash(f'Payment amount (₹{new_payment_amount:.2f}) cannot exceed the due amount (₹{current_due:.2f}).',
                      'danger')
                return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

            # --- Update AmbulanceCall fields ---
            # Add the new payment to the existing payment_amount
            call.payment_amount = float(current_paid + new_payment_amount)
            call.payment_mode = payment_mode  # You might want to store multiple payment records in a separate table for auditing

            # Append new payment notes, or create if none exist
            if note:
                if call.notes:
                    call.notes += f"\nPayment added on {payment_date.strftime('%Y-%m-%d')}: {note} (Mode: {payment_mode}, Amount: ₹{new_payment_amount:.2f})"
                else:
                    call.notes = f"Payment added on {payment_date.strftime('%Y-%m-%d')}: {note} (Mode: {payment_mode}, Amount: ₹{new_payment_amount:.2f})"

            # It's good practice to also update `updated_at` explicitly if not using `onupdate=db.func.now()`
            # call.updated_at = datetime.datetime.utcnow() # SQLAlchemy's onupdate usually handles this

            db.session.commit()
            flash('Payment recorded successfully!', 'success')

            # Redirect back to the call details page
            return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

        except Exception as e:
            db.session.rollback()  # Rollback changes in case of an error
            flash(f'An error occurred while recording payment: {str(e)}', 'danger')
            return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)

    # If it's not a POST request (e.g., direct GET to this endpoint), redirect or show an error
    flash('Invalid request method for payment.', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route('/get-charge-items/<int:category_id>', methods=['GET'])
def get_charge_items(category_id):
    # Corrected model name
    items = AmbulanceChargeItem.query.filter_by(category_id=category_id, is_active=True).all()
    # Corrected attribute from 'charge' to 'standard_charge'
    items_data = [{'id': item.id, 'name': item.name, 'standard_charge': item.standard_charge} for item in items]
    return jsonify(items_data)


# Define your route for printing the ambulance bill
@admin.route(AMBULANCE_AMBULANCE_CALL_LIST_PRINT + '/<int:call_id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name, UserRole.STAFF.name])  # Adjust roles as needed
def print_ambulance_bill(current_user, call_id):
    """
    Renders a print-friendly view of an ambulance call bill.
    Eagerly loads related data for efficient template rendering.
    """
    # Eagerly load all necessary relationships to avoid N+1 queries in the template
    call = AmbulanceCall.query.options(
        joinedload(AmbulanceCall.ambulance),
        joinedload(AmbulanceCall.driver),
        joinedload(AmbulanceCall.additional_charge_entries).joinedload(AdditionalCharge.charge_item)
    ).get_or_404(call_id)

    # Ensure the call is completed before allowing a bill print (optional but good practice)
    if call.status != 'Completed':
        flash('Cannot print bill for an incomplete ambulance call.', 'warning')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)  # Or appropriate redirect

    return render_template(
        'admin_templates/ambulance/ambulance_bill_print.html',  # Create this new template
        call=call,
        datetime=datetime.datetime  # Pass datetime for formatting
    )

@admin.route(AMBULANCE_AMBULANCE_DELETE_CALL + '/<int:id>', methods=['POST'], endpoint='delete-ambulance-call')
def delete_ambulance_call(id):
    call = AmbulanceCall.query.get_or_404(id)
    try:
        call.deleted_at = datetime.datetime.utcnow()
        call.is_deleted = True
        db.session.commit()
        flash('Ambulance call deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_RESTORE_CALL + '/<int:id>', methods=['POST'], endpoint='restore-ambulance-call')
def restore_ambulance_call(id):
    call = AmbulanceCall.query.get_or_404(id)
    try:
        call.deleted_at = None
        call.is_deleted = False
        db.session.commit()
        flash('Ambulance call Restore successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error Restore ambulance call: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_UPDATE_STATUS_CALL + '/<int:id>', methods=['POST'], endpoint='update-call-status')
def update_call_status(id):
    call = AmbulanceCall.query.get_or_404(id)
    new_status = request.form.get('status')

    try:
        call.status = new_status

        if new_status == 'Dispatched' and not call.dispatch_time:
            call.dispatch_time = datetime.datetime.utcnow()
            if call.ambulance:
                call.ambulance.is_available = False
        elif new_status == 'In Progress' and not call.arrival_time:
            call.arrival_time = datetime.datetime.utcnow()
        elif new_status == 'Completed' and not call.completion_time:
            call.completion_time = datetime.datetime.utcnow()
            if call.ambulance:
                call.ambulance.is_available = 1
            # The calculation here is simplified and does not account for additional charges, discount, tax
            # If full recalculation is needed on status update, it should be moved to a shared function
            # and called here, similar to add/edit call.
            if request.form.get('distance'):
                call.distance = float(request.form.get('distance'))
                if call.ambulance:
                    call.base_charge = call.ambulance.base_rate
                    # Removed ambulance.per_km_rate
                    call.distance_charge = 0.0  # Default to 0.0
                    call.total_amount = call.base_charge + call.distance_charge  # Simplified calculation

        elif new_status == 'Cancelled':
            if call.ambulance:
                call.ambulance.is_available = True

        db.session.commit()
        flash(f'Call status updated to {new_status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating call status: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)


@admin.route(AMBULANCE_AMBULANCE_EXPORT_CALLS, methods=['GET'], endpoint='export_ambulance_calls')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_ambulance_calls(current_user):
    # Get parameters from the request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    export_format = request.args.get('format')

    # --- 1. Validate and Parse Dates ---
    try:
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            # Default to a very old date if not provided
            start_date = datetime.date(1900, 1, 1)

        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to today if not provided
            end_date = datetime.date.today()

        # Adjust end_date to include the entire day (up to the last second)
        end_datetime_inclusive = datetime.datetime.combine(end_date, datetime.datetime.max.time())

        if start_date > end_date:
            flash('Start date cannot be after end date.', 'error')
            return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)  # Use url_for with blueprint endpoint
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)  # Use url_for with blueprint endpoint

    # --- 2. Query Data from Database (Filtered by Date Range) ---
    calls_query = AmbulanceCall.query.filter(
        AmbulanceCall.created_at >= start_date,
        AmbulanceCall.created_at <= end_datetime_inclusive,
        AmbulanceCall.is_deleted == False  # Assuming you want to exclude soft-deleted calls
    ).options(
        joinedload(AmbulanceCall.ambulance),  # Eager load ambulance data
        joinedload(AmbulanceCall.driver),  # Eager load driver data
        joinedload(AmbulanceCall.additional_charge_entries).joinedload(AdditionalCharge.charge_item)
        # Eager load additional charges and their items
    ).order_by(AmbulanceCall.created_at.asc()).all()

    # --- 3. Prepare Data for Export (Pandas DataFrame for flexibility) ---
    data_for_export = []
    for call in calls_query:
        # Calculate balance/refund/due amounts for the call
        total_billed = call.total_amount if call.total_amount is not None else 0.0
        payment_made = call.payment_amount if call.payment_amount is not None else 0.0

        balance_calc = Decimal(str(total_billed)) - Decimal(str(payment_made))

        refund_amount = 0.00
        balance_due = 0.00

        if balance_calc < Decimal('0'):
            refund_amount = float(abs(balance_calc))
        else:
            balance_due = float(balance_calc)

        # Get related names safely
        ambulance_name = call.ambulance.vehicle_name if call.ambulance else 'N/A'
        driver_name = f"{call.driver.name}" if call.driver else 'N/A'

        # Summarize additional charges for the export row
        additional_charges_summary = ", ".join([
            f"{entry.charge_item.name}: ₹{entry.amount:.2f}"
            for entry in call.additional_charge_entries
            if entry.charge_item  # Ensure charge_item is not None
        ])
        if not additional_charges_summary:
            additional_charges_summary = "None"

        data_for_export.append({
            'Call No': call.call_number,
            'Call Date': call.call_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Patient Name': call.patient_name,
            'Patient Age': call.patient_age,
            'Patient Gender': call.patient_gender,
            'Pickup Location': call.pickup_location,
            'Destination': call.destination,
            'Distance (km)': float(call.distance) if call.distance is not None else 0.0,
            'Ambulance': ambulance_name,
            'Driver': driver_name,
            'Base Charge': float(call.base_charge) if call.base_charge is not None else 0.0,
            'Additional Charges': additional_charges_summary,  # Summary of all additional charges
            'Total Add. Charges': float(
                call.additional_charges_total) if call.additional_charges_total is not None else 0.0,
            'Subtotal': float(call.subtotal) if call.subtotal is not None else 0.0,
            'Discount Amount': float(call.discount_amount) if call.discount_amount is not None else 0.0,
            'Tax Amount': float(call.tax_amount) if call.tax_amount is not None else 0.0,
            'Total Amount': float(call.total_amount) if call.total_amount is not None else 0.0,
            'Paid Amount': float(call.payment_amount) if call.payment_amount is not None else 0.0,
            'Refund Amount': refund_amount,
            'Balance Due': balance_due,
            'Payment Mode': call.payment_mode,
            'Status': call.status,
            'Notes': call.notes,
            'Completion Time': call.completion_time.strftime('%Y-%m-%d %H:%M:%S') if call.completion_time else 'N/A',
        })

    # Create DataFrame from the list of dictionaries
    df = pd.DataFrame(data_for_export)

    if df.empty:
        flash('No ambulance call records found for the selected date range.', 'warning')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)  # Use url_for with blueprint endpoint

    # --- 4. Generate Report in Selected Format ---
    filename_suffix = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

    if export_format == 'csv':
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=ambulance_calls_{filename_suffix}.csv"}
        )

    elif export_format == 'excel':
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='AmbulanceCalls')
        excel_buffer.seek(0)
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ambulance_calls_{filename_suffix}.xlsx'
        )

    elif export_format == 'pdf':
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                                topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        styles = getSampleStyleSheet()

        # Define styles for PDF content
        title_style = styles['Title']
        title_style.alignment = 1  # Center
        h2_style = styles['h2']
        h2_style.textColor = colors.HexColor('#2E86C1')
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 7
        normal_style.leading = 8  # Adjusted for more fields
        header_table_style = styles['h4']
        header_table_style.fontName = 'Helvetica-Bold'
        header_table_style.fontSize = 8
        header_table_style.alignment = 1  # Center align headers where appropriate

        elements = []

        # Title and Date Range
        elements.append(Paragraph("Ambulance Call Report", title_style))
        elements.append(
            Paragraph(f"From: {start_date.strftime('%Y-%m-%d')} To: {end_date.strftime('%Y-%m-%d')}", styles['h3']))
        elements.append(Spacer(1, 0.2 * inch))

        # Prepare data for PDF table (header + data rows)
        pdf_table_data = []
        pdf_table_data.append(
            [Paragraph(col, header_table_style) for col in df.columns.tolist()])  # Use DataFrame columns for headers

        for index, row in df.iterrows():
            row_list = []
            for col_name in df.columns:
                cell_value = row[col_name]
                # Format specific columns for currency
                if col_name in ['Base Charge', 'Total Add. Charges', 'Subtotal', 'Discount Amount', 'Tax Amount',
                                'Total Amount', 'Paid Amount', 'Refund Amount', 'Balance Due']:
                    row_list.append(Paragraph(f"₹{cell_value:.2f}", normal_style))
                elif col_name == 'Status':
                    status_color = '#28A745' if cell_value == 'Completed' else (
                        '#FFA500' if cell_value == 'Pending' or cell_value == 'In Progress' else '#DC3545')  # Green, Orange, Red
                    row_list.append(Paragraph(f'<font color="{status_color}"><b>{cell_value}</b></font>', normal_style))
                else:
                    row_list.append(Paragraph(str(cell_value), normal_style))
            pdf_table_data.append(row_list)

        # Calculate Column Widths for PDF Table (more complex due to many columns)
        # Dynamic width calculation adapted for more columns
        col_widths = []
        available_width = letter[0] - (2 * 0.5 * inch)  # Page width minus margins
        num_columns = len(df.columns)

        # Define a base width for common text columns and narrower for numbers/ids
        base_text_width_ratio = 0.06  # % of total width for average text column
        num_width_ratio = 0.03  # % of total width for number/amount column

        # Assign initial rough widths based on type/expected content
        for col_name in df.columns:
            if col_name in ['Call No', 'Patient Age', 'Distance (km)', 'Number of Items']:
                col_widths.append(available_width * num_width_ratio * 0.8)  # Slightly smaller
            elif col_name in ['Base Charge', 'Total Add. Charges', 'Subtotal', 'Discount Amount', 'Tax Amount',
                              'Total Amount', 'Paid Amount', 'Refund Amount', 'Balance Due']:
                col_widths.append(available_width * num_width_ratio * 1.2)  # Slightly larger for currency
            elif col_name in ['Call Date', 'Completion Time']:
                col_widths.append(available_width * base_text_width_ratio * 1.2)  # For datetime strings
            elif col_name in ['Patient Name', 'Pickup Location', 'Destination', 'Ambulance', 'Driver',
                              'Additional Charges', 'Notes']:
                col_widths.append(available_width * base_text_width_ratio * 1.5)  # More width for text fields
            else:
                col_widths.append(available_width * base_text_width_ratio)

        # Normalize and scale if total width exceeds available width
        total_initial_width = sum(col_widths)
        if total_initial_width > available_width:
            scaling_factor = available_width / total_initial_width
            col_widths = [w * scaling_factor for w in col_widths]
        # Ensure minimum width for any column to prevent squashing
        min_col_width = 0.3 * inch
        col_widths = [max(w, min_col_width) for w in col_widths]

        # Create Table and apply styling
        table = Table(pdf_table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),  # Header row background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align headers
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical align all cells

            # Align specific columns based on content
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),  # Distance (km) column (index 6) - Right align data rows
            ('ALIGN', (10, 1), (-1, -1), 'RIGHT'),
            # All financial columns (from index 10 to last) - Right align data rows

            # Example: Center align for Status
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Status column (index 1) - Center align data rows
        ]))

        elements.append(table)
        doc.build(elements)
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ambulance_calls_{filename_suffix}.pdf'
        )

    else:
        flash('Invalid export format requested.', 'error')
        return redirect(ADMIN + AMBULANCE_AMBULANCE_CALL_LIST)  # Use url_for with blueprint endpoint
