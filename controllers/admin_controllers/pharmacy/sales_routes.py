import datetime
import io
import traceback
from decimal import Decimal

import pandas as pd
from flask import render_template, request, jsonify, flash, redirect, send_file, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import TableStyle, Table, Paragraph, Spacer, SimpleDocTemplate
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, PHARMACY_SALES_ADD, PHARMACY_SALES_EXPORT, \
    PHARMACY_SALES_PRINT, PHARMACY_SALES_VIEW, PHARMACY_SALES_DELETE, PHARMACY_SALES_RESTORE, PHARMACY_SALES_LIST
from middleware.auth_middleware import token_required
from models import UserRole, Patient
from models.doctorModel import Doctor
from models.medicineModel import MedicineSale, MedicineBatch, MedicineSaleItem, StockTransaction
from utils.config import db


def generate_bill_number():
    last_sale = MedicineSale.query.order_by(MedicineSale.id.desc()).first()  # Assuming ID is sequential
    if last_sale and last_sale.bill_no and last_sale.bill_no.startswith('INV-'):
        try:
            # Attempt to parse the numeric part from the last bill_no
            parts = last_sale.bill_no.split('-')
            if len(parts) == 2 and parts[1].isdigit():  # Handles INV-N format
                last_sequence_num = int(parts[1])
            elif len(parts) == 3 and parts[2].isdigit() and len(parts[1]) == 8:  # Handles INV-YYYYMMDD-N format
                last_sequence_num = int(parts[2])
            else:
                last_sequence_num = 0
        except ValueError:
            last_sequence_num = 0
    else:
        last_sequence_num = 0

    next_sequence = last_sequence_num + 1
    bill_number = f"INV-{next_sequence:06d}"  # Formats as 000001, 000002, etc. with leading zeros
    return bill_number


@admin.route(PHARMACY_SALES_LIST, methods=['GET'], endpoint="sales_list")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def sales_list(current_user):
    sales = MedicineSale.query.options(
        db.joinedload(MedicineSale.doctor),  # For doctor name
        # For user who created sale
        db.joinedload(MedicineSale.items)
    ).filter_by(is_deleted=0).order_by(MedicineSale.created_at.desc()).all()

    sales_data = []
    for sale in sales:

        if hasattr(sale, 'patient') and sale.patient:
            patient_name = f"{sale.patient.first_name} {sale.patient.last_name}"
        else:

            patient_name = f"ID: {sale.patient_id}"

        doctor_name = "N/A"
        if sale.doctor:
            doctor_name = f"{sale.doctor.first_name} {sale.doctor.last_name}"

        balance_amount = sale.net_amount - sale.payment_amount
        refund_amount = 0.00
        balance_due = 0.00

        if balance_amount < 0:
            refund_amount = abs(balance_amount)
        else:
            balance_due = balance_amount

        sales_data.append({
            'id': sale.id,
            'bill_no': sale.bill_no,
            'patient_id': sale.patient_id,  # Keep ID for reference
            'patient_name': patient_name,
            'sale_date': sale.created_at.strftime('%Y-%m-%d %I:%M %p'),
            'doctor_name': doctor_name,
            'total_amount': sale.total_amount,
            'discount_amount': sale.discount_amount,
            'net_amount': sale.net_amount,
            'paid_amount': sale.payment_amount,
            'refund_amount': refund_amount,
            'balance_due': balance_due,
            'items_count': len(sale.items) if sale.items else 0,
            'status': 'Paid' if balance_due <= 0.01 else 'Due'  # Add a status for display
        })

    # Fetch archived sales (is_deleted=True)
    archived_sales_query = MedicineSale.query.options(
        db.joinedload(MedicineSale.doctor),
        db.joinedload(MedicineSale.items)
    ).filter_by(is_deleted=True).order_by(MedicineSale.created_at.desc())

    archived_sales_orm = archived_sales_query.all()  # Get ORM objects for archived sales

    archived_sales_data = []
    for sale in archived_sales_orm:

        if hasattr(sale, 'patient') and sale.patient:
            patient_name = f"{sale.patient.first_name} {sale.patient.last_name}"
        else:

            patient_name = f"ID: {sale.patient_id}"

        doctor_name = "N/A"
        if sale.doctor:
            doctor_name = f"{sale.doctor.first_name} {sale.doctor.last_name}"

        net_amount = Decimal(sale.net_amount)
        payment_amount = Decimal(sale.payment_amount)

        balance_amount = net_amount - payment_amount
        refund_amount = Decimal('0.00')
        balance_due = Decimal('0.00')

        if balance_amount < 0:
            refund_amount = abs(balance_amount)
        else:
            balance_due = balance_amount

        archived_sales_data.append({  # Append to the new list
            'id': sale.id,
            'bill_no': sale.bill_no,
            'patient_id': sale.patient_id,
            'patient_name': patient_name,
            'sale_date': sale.created_at,  # Pass datetime object directly
            'doctor_name': doctor_name,
            'total_amount': sale.total_amount,
            'discount_amount': sale.discount_amount,
            'net_amount': net_amount,
            'paid_amount': payment_amount,
            'refund_amount': refund_amount,
            'balance_due': balance_due,
            'items_count': len(sale.items) if sale.items else 0,
            'status': 'Paid' if balance_due <= Decimal('0.01') else 'Due',
            'is_deleted': sale.is_deleted
        })
    return render_template('admin_templates/pharmacy/sales_list.html',
                           sales=sales_data,
                           datetime=datetime.datetime,
                           archived_sales=archived_sales_data,
                           ADMIN=ADMIN,
                           PHARMACY_SALES_ADD=PHARMACY_SALES_ADD,
                           PHARMACY_SALES_EXPORT=PHARMACY_SALES_EXPORT,
                           PHARMACY_SALES_PRINT=PHARMACY_SALES_PRINT,
                           PHARMACY_SALES_VIEW=PHARMACY_SALES_VIEW,
                           PHARMACY_SALES_DELETE=PHARMACY_SALES_DELETE,
                           PHARMACY_SALES_RESTORE=PHARMACY_SALES_RESTORE)


@admin.route(PHARMACY_SALES_ADD, methods=['GET', 'POST'], endpoint="new_sale")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def new_sale(current_user):
    if request.method == 'POST':
        try:

            patient_id = request.form.get('patient_id')
            if not patient_id:
                raise ValueError("Patient ID is required.")
            try:
                patient_id = int(patient_id)
            except ValueError:
                raise ValueError("Invalid Patient ID format.")

            # Handle doctor_id: convert empty string to None
            doctor_id_from_form = request.form.get('doctor_id')
            doctor_id = int(doctor_id_from_form) if doctor_id_from_form else None

            # Get numeric values, defaulting to 0 or appropriate types
            total_amount = float(request.form.get('total_amount', 0))
            discount_amount = float(request.form.get('discount_amount', 0))
            tax_amount = float(request.form.get('tax_amount', 0))
            net_amount = float(request.form.get('net_amount', 0))
            payment_amount = float(request.form.get('payment_amount', 0))

            # Create the main MedicineSale record
            sale = MedicineSale(
                prescription_no=request.form.get('prescription_no'),
                patient_id=patient_id,
                bill_no=generate_bill_number(),
                case_id=request.form.get('case_id'),
                doctor_id=doctor_id,
                note=request.form.get('note'),
                total_amount=total_amount,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                net_amount=net_amount,
                payment_mode=request.form.get('payment_mode', 'Cash'),
                payment_amount=payment_amount,
                created_by=current_user,

            )
            db.session.add(sale)
            db.session.flush()  # Flush to get the sale.id for sale items

            # --- Process Sale Items ---
            medicine_ids = request.form.getlist('medicine_id[]')
            batch_ids = request.form.getlist('batch_id[]')
            quantities = request.form.getlist('quantity[]')
            sale_prices = request.form.getlist('sale_price[]')
            tax_rates = request.form.getlist('tax_rate[]')
            amounts = request.form.getlist('amount[]')  # This is the total for each item including its tax

            # Ensure all lists have the same length for proper iteration
            if not (len(medicine_ids) == len(batch_ids) == len(quantities) ==
                    len(sale_prices) == len(tax_rates) == len(amounts)):
                raise ValueError("Mismatch in number of item fields. Please check your form data.")

            if not medicine_ids:  # Check if no items were added
                raise ValueError("No medicine items added to the sale.")

            for i in range(len(medicine_ids)):
                med_id = int(medicine_ids[i])
                bat_id = int(batch_ids[i])
                qty = int(quantities[i])
                s_price = float(sale_prices[i])
                t_rate = float(tax_rates[i])
                amt = float(amounts[i])

                # Fetch batch to validate and update stock
                batch = MedicineBatch.query.get(bat_id)
                if not batch:
                    raise ValueError(f"Batch with ID {bat_id} not found.")

                # Further validate: Does the batch belong to the selected medicine?
                if batch.medicine_id != med_id:
                    raise ValueError(f"Batch {batch.batch_no} does not belong to medicine ID {med_id}.")

                if batch.current_stock < qty:
                    raise ValueError(
                        f"Not enough stock for {batch.medicine.name} (Batch: {batch.batch_no}). Available: {batch.current_stock}, Requested: {qty}")

                # Also check expiry date if not already filtered by API
                if batch.expiry_date and batch.expiry_date <= datetime.date.today():
                    raise ValueError(
                        f"Cannot sell expired medicine: {batch.medicine.name} (Batch: {batch.batch_no} expired on {batch.expiry_date.strftime('%Y-%m-%d')}).")

                item = MedicineSaleItem(
                    sale_id=sale.id,
                    medicine_id=med_id,
                    batch_id=bat_id,
                    quantity=qty,
                    sale_price=s_price,
                    tax_rate=t_rate,
                    amount=amt  # This is the total amount for THIS item including its tax
                )
                db.session.add(item)

                # Update batch stock
                batch.current_stock -= qty

                stock_transaction = StockTransaction(
                    medicine_id=med_id,
                    batch_id=bat_id,
                    transaction_type='sale',
                    quantity=qty,
                    balance=batch.current_stock,
                    reference=f"Sale #{sale.bill_no}",
                    notes=f"Sold {qty} units for Sale ID: {sale.id}",
                    created_by=current_user
                )
                db.session.add(stock_transaction)
            db.session.commit()
            flash(f'Sale {sale.bill_no} recorded successfully!', 'success')
            return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect to view the new sale

        except ValueError as ve:
            db.session.rollback()
            flash(f'Validation Error: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()  # Print full traceback to console for debugging
            flash(f'An unexpected error occurred: {str(e)}', 'error')

    # For GET request or if POST fails and we need to re-render the form
    doctors = Doctor.query.order_by(Doctor.first_name).all()
    return render_template('admin_templates/pharmacy/new_sale.html',
                           doctors=doctors,
                           datetime=datetime.datetime,
                           ADMIN=ADMIN,
                           PHARMACY_SALES_ADD=PHARMACY_SALES_ADD)


@admin.route(PHARMACY_SALES_VIEW + '/<int:sale_id>', methods=['GET'], endpoint="view_sale")
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Add token_required for security
def view_sale(current_user, sale_id):
    # Eagerly load related data to avoid N+1 queries
    sale = MedicineSale.query.options(
        db.joinedload(MedicineSale.items).joinedload(MedicineSaleItem.medicine),
        db.joinedload(MedicineSale.items).joinedload(MedicineSaleItem.batch),
        db.joinedload(MedicineSale.doctor)
    ).get_or_404(sale_id)

    due_amount = sale.net_amount - sale.payment_amount

    return render_template('admin_templates/pharmacy/view_sale.html',
                           sale=sale,
                           items=sale.items,  # Pass items explicitly for loop
                           due_amount=due_amount,
                           datetime=datetime.datetime,  # For using datetime in template
                           ADMIN=ADMIN,
                           PHARMACY_SALES_LIST=PHARMACY_SALES_LIST,
                           PHARMACY_SALES_PRINT=PHARMACY_SALES_PRINT,
                           PHARMACY_SALES_DELETE=PHARMACY_SALES_DELETE                           )


@admin.route(PHARMACY_SALES_DELETE + '/<int:sale_id>', methods=['POST'], endpoint='medicine-sales/delete')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_sale(current_user, sale_id):
    sale = MedicineSale.query.options(db.joinedload(MedicineSale.items)).get_or_404(sale_id)

    if sale.is_deleted:
        flash('This sale is already deleted.', 'warning')
        return redirect(ADMIN + PHARMACY_SALES_LIST)  # Assuming an endpoint for sales list

    try:

        sale.is_deleted = True
        sale.deleted_at = datetime.datetime.utcnow()
        sale.updated_at = datetime.datetime.utcnow()

        for item in sale.items:

            item.is_deleted = True
            item.deleted_at = datetime.datetime.utcnow()
            item.updated_at = datetime.datetime.utcnow()

            batch = item.batch

            if batch:
                batch.current_stock += item.quantity

                # Create a StockTransaction entry for this stock increase
                stock_transaction = StockTransaction(
                    medicine_id=item.medicine_id,
                    batch_id=batch.id,
                    transaction_type='sale_delete',  # Indicating stock return due to sale deletion
                    quantity=item.quantity,  # Positive quantity for stock incoming/return
                    balance=batch.current_stock,  # New current stock of the batch *after* increase
                    reference=f"Sale Delete (Bill: {sale.bill_no})",
                    notes=f"Stock returned due to deletion of sale (Sale ID: {sale.id})",
                    created_by=current_user  # Use current_user.id for FK
                )
                db.session.add(stock_transaction)
            else:
                flash(
                    f'Warning: No batch found for sale item for Medicine ID {item.medicine_id} in sale deletion. Stock reversal incomplete.',
                    'warning')

        db.session.commit()
        flash(f'Sale {sale.bill_no} soft-deleted and stock updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error deleting sale {sale.bill_no}: {str(e)}', 'danger')

    return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect to the main sales list


# (Imports are the same as the delete_sale route above)

@admin.route(PHARMACY_SALES_RESTORE + '/<int:sale_id>', methods=['POST'], endpoint='medicine-sales/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_sale(current_user, sale_id):
    # Eager load sale items for efficiency
    sale = MedicineSale.query.options(db.joinedload(MedicineSale.items)).get_or_404(sale_id)

    if not sale.is_deleted:
        flash('This sale is not deleted and cannot be restored.', 'warning')
        return redirect(ADMIN + PHARMACY_SALES_LIST)

    try:
        # Step 1: Restore the main MedicineSale record
        sale.is_deleted = False
        sale.deleted_at = None
        sale.updated_at = datetime.datetime.utcnow()

        # Step 2: Process each sale item to reverse soft-deletion and re-deduct stock
        for item in sale.items:
            # Only restore items that were part of this sale and were marked deleted
            if item.is_deleted:
                item.is_deleted = False
                item.deleted_at = None
                item.updated_at = datetime.datetime.utcnow()

                # Get the associated MedicineBatch directly via the relationship
                batch = item.batch  # MedicineSaleItem model has 'batch' relationship

                if batch:  # Ensure batch exists
                    # Stock reversal: When a sale is restored, the stock previously put back (during deletion) should be re-deducted.
                    if batch.current_stock < item.quantity:
                        # This is a critical check: prevent negative stock if not enough is available for restoration
                        db.session.rollback()  # Rollback all changes
                        flash(
                            f'Error restoring sale {sale.bill_no}: Not enough stock for {item.medicine.name} (Batch: {batch.batch_no}). Available: {batch.current_stock}, Needed: {item.quantity}.',
                            'danger')
                        return redirect(ADMIN + PHARMACY_SALES_LIST)

                    batch.current_stock -= item.quantity

                    # Create a StockTransaction entry for this stock decrease
                    stock_transaction = StockTransaction(
                        medicine_id=item.medicine_id,
                        batch_id=batch.id,
                        transaction_type='sale_restore',  # Indicating stock removal due to sale restoration
                        quantity=-item.quantity,  # Negative quantity for stock outgoing/re-deduction
                        balance=batch.current_stock,
                        # New current stock of the batch *after* re-deduction
                        reference=f"Sale Restore (Bill: {sale.bill_no})",
                        notes=f"Stock re-deducted due to restoration of sale (Sale ID: {sale.id})",
                        created_by=current_user
                    )
                    db.session.add(stock_transaction)
                else:
                    flash(
                        f'Warning: No batch found for sale item for Medicine ID {item.medicine_id} during restore. Stock not fully re-deducted.',
                        'warning')

        db.session.commit()
        flash(f'Sale {sale.bill_no} and its associated items restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error restoring sale {sale.bill_no}: {str(e)}', 'danger')

    return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect to the main sales list


@admin.route('/api/medicine/<int:medicine_id>/batches')
def get_medicine_batches(medicine_id):
    batches = MedicineBatch.query.filter_by(
        medicine_id=medicine_id,
        is_deleted=False
    ).filter(
        MedicineBatch.expiry_date >= datetime.datetime.now().date(),
        MedicineBatch.current_stock > 0
    ).order_by(MedicineBatch.expiry_date).all()

    batches_data = [{
        'id': b.id,
        'batch_no': b.batch_no,
        'expiry_date': b.expiry_date.strftime('%Y-%m-%d'),
        'current_stock': b.current_stock,
        'sale_price': float(b.selling_price),
        'mrp': float(b.mrp)
    } for b in batches]

    return jsonify(batches_data)


@admin.route(PHARMACY_SALES_PRINT + '/<int:sale_id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Add token_required if print view needs auth
def print_sale_bill(current_user, sale_id):
    # Eagerly load the sale, its items, and related medicine, doctor, and patient data
    sale = MedicineSale.query.options(
        joinedload(MedicineSale.items).joinedload(MedicineSaleItem.medicine),  # Load items and their medicines
        joinedload(MedicineSale.doctor),  # Load doctor details
    ).get_or_404(sale_id)

    patients = Patient.query.filter_by(patient_id=sale.patient_id).first()
    return render_template(
        'admin_templates/pharmacy/sale_print_view.html',
        patients=patients,  # Create this new template!
        sale=sale,
        items=sale.items,  # Access items directly from the sale object
        datetime=datetime  # Pass datetime module for date formatting in template
    )


@admin.route(PHARMACY_SALES_EXPORT, methods=['GET'], endpoint='export_sales')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_sales(current_user):
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
            return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect back to sales list
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(ADMIN + PHARMACY_SALES_LIST)

    # --- 2. Query Data from Database (Filtered by Date Range) ---
    sales_query = MedicineSale.query.filter(
        MedicineSale.created_at >= start_date,
        MedicineSale.created_at <= end_datetime_inclusive,  # Use the adjusted end_datetime_inclusive
        # Assuming you don't have is_deleted for sales, or add it if you do
        # MedicineSale.is_deleted == False
    ).options(
        joinedload(MedicineSale.doctor),  # Eager load doctor data
        joinedload(MedicineSale.items)  # Eager load sale items (if you need item details in export)
    ).order_by(MedicineSale.created_at.asc()).all()

    # --- 3. Prepare Data for Export (Pandas DataFrame for flexibility) ---
    data_for_export = []
    for sale in sales_query:
        # Calculate balance/refund as needed, similar to how it's done in sales_list
        balance_amount = sale.net_amount - sale.payment_amount
        refund_amount = 0.00
        balance_due = 0.00

        if balance_amount < 0:
            refund_amount = abs(balance_amount)
        else:
            balance_due = balance_amount

        # Get patient and doctor names safely
        patient_name = 'N/A'
        doctor_name = f"{sale.doctor.first_name} {sale.doctor.last_name}" if sale.doctor else 'N/A'

        data_for_export.append({
            'Bill No': sale.bill_no,
            'Sale Date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Include time for sales if desired
            'Patient Name': patient_name,
            'Doctor Name': doctor_name,
            'Net Amount': float(sale.net_amount),
            'Paid Amount': float(sale.payment_amount),
            'Refund Amount': float(refund_amount),
            'Balance Due': float(balance_due),
            'Status': 'Paid' if balance_due <= Decimal('0.01') else 'Due',
            'Number of Items': len(sale.items) if sale.items else 0  # Example for item count
            # Add more fields if needed, e.g., 'Discount Amount', 'Tax Amount' if they exist on MedicineSale
        })

    # Create DataFrame from the list of dictionaries
    df = pd.DataFrame(data_for_export)

    if df.empty:
        flash('No sales records found for the selected date range.', 'warning')
        return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect back to sales list

    # --- 4. Generate Report in Selected Format ---
    filename_suffix = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

    if export_format == 'csv':
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=sales_{filename_suffix}.csv"}
        )

    elif export_format == 'excel':
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sales')
        excel_buffer.seek(0)
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'sales_{filename_suffix}.xlsx'
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
        normal_style.fontSize = 8
        normal_style.leading = 9
        header_table_style = styles['h4']
        header_table_style.fontName = 'Helvetica-Bold'
        header_table_style.fontSize = 9
        header_table_style.alignment = 1  # Center align headers where appropriate

        elements = []

        # Title and Date Range
        elements.append(Paragraph("Sales Report", title_style))
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
                if col_name in ['Net Amount', 'Paid Amount', 'Refund Amount', 'Balance Due']:
                    row_list.append(Paragraph(f"₹{cell_value:.2f}", normal_style))
                elif col_name == 'Status':
                    status_color = '#28A745' if cell_value == 'Paid' else '#FFA500'  # Green for paid, orange for due
                    row_list.append(Paragraph(f'<font color="{status_color}"><b>{cell_value}</b></font>', normal_style))
                else:
                    row_list.append(Paragraph(str(cell_value), normal_style))
            pdf_table_data.append(row_list)

        # Calculate Column Widths for PDF Table
        col_widths = []
        available_width = letter[0] - 2 * 0.5 * inch  # Page width minus margins
        min_col_width = 0.5 * inch
        padding_per_side = 0.05 * inch

        for col_idx in range(len(pdf_table_data[0])):
            max_content_width_in_points = 0
            for row in pdf_table_data:
                if isinstance(row[col_idx], Paragraph):
                    text_to_measure = row[col_idx].text
                else:
                    text_to_measure = str(row[col_idx])

                width = stringWidth(text_to_measure, normal_style.fontName, normal_style.fontSize)
                if width > max_content_width_in_points:
                    max_content_width_in_points = width

            estimated_col_width = max_content_width_in_points + (2 * padding_per_side)
            col_widths.append(max(estimated_col_width, min_col_width))

        total_estimated_width = sum(col_widths)
        if total_estimated_width > available_width:
            scaling_factor = available_width / total_estimated_width
            col_widths = [w * scaling_factor for w in col_widths]

        # Create Table and apply styling
        table = Table(pdf_table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Align numeric columns to the right - adjust column indices if you add/remove columns
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Example for 'Net Amount' onwards
        ]))

        elements.append(table)
        doc.build(elements)
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'sales_{filename_suffix}.pdf'
        )

    else:
        flash('Invalid export format requested.', 'error')
        return redirect(ADMIN + PHARMACY_SALES_LIST)  # Redirect back to sales list
