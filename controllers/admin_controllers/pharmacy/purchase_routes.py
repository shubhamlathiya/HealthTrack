# Categories Routes
import datetime
import io
import traceback
from decimal import Decimal

import pandas as pd
from flask import render_template, send_file, Response
from flask import request, jsonify, redirect, url_for, flash
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, PHARMACY_PURCHASES_LIST, PHARMACY_PURCHASES_ADD, \
    PHARMACY_PURCHASES_VIEW, PHARMACY_PURCHASES_DELETE, PHARMACY_PURCHASES_PAYMENT, \
    PHARMACY_PURCHASES_PRINT, PHARMACY_PURCHASES_RESTORE, PHARMACY_PURCHASES_EXPORT, PHARMACY_STOCK_LEVELS
from middleware.auth_middleware import token_required
from models.medicineModel import Supplier, MedicinePurchase, Medicine, PurchaseItem, MedicineBatch, StockTransaction
from models.userModel import UserRole
from utils.config import db


def generate_next_number(model, prefix, number_field):
    last_record = model.query.order_by(model.id.desc()).first()
    if last_record:
        last_num = int(getattr(last_record, number_field).replace(prefix, ''))
        return f"{prefix}{last_num + 1:04d}"
    return f"{prefix}0001"


# Medicine Purchase Routes
@admin.route(PHARMACY_PURCHASES_LIST, methods=['GET'], endpoint='medicine_purchases')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def medicine_purchases(current_user):
    purchases = MedicinePurchase.query.filter_by(is_deleted=0).order_by(MedicinePurchase.purchase_date.desc()).all()
    deleted_purchases = MedicinePurchase.query.filter_by(is_deleted=1).order_by(
        MedicinePurchase.purchase_date.desc()).all()
    suppliers = Supplier.query.filter_by(is_deleted=0).order_by(Supplier.name).all()
    return render_template('admin_templates/pharmacy/purchases.html',
                           purchases=purchases,
                           suppliers=suppliers,
                           datetime=datetime.datetime,
                           archived_purchases=deleted_purchases,
                           ADMIN=ADMIN,
                           PHARMACY_PURCHASE_ADD=PHARMACY_PURCHASES_ADD,
                           PHARMACY_PURCHASE_VIEW=PHARMACY_PURCHASES_VIEW,
                           PHARMACY_PURCHASE_DELETE=PHARMACY_PURCHASES_DELETE,
                           PHARMACY_MEDICINE_PURCHASE_PAYMENT=PHARMACY_PURCHASES_PAYMENT,
                           PHARMACY_PURCHASE_RESTORE=PHARMACY_PURCHASES_RESTORE,
                           PHARMACY_MEDICINE_PURCHASES_PRINT=PHARMACY_PURCHASES_PRINT,
                           PHARMACY_PURCHASE_EXPORT=PHARMACY_PURCHASES_EXPORT,
                           )


@admin.route(PHARMACY_PURCHASES_ADD, methods=['POST'], endpoint='add_medicine_purchase')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_medicine_purchase(current_user):
    try:
        data = request.form
        print("Raw form data:", data)

        # Parse items from form data
        items = []
        item_indexes = set()
        for key in data.keys():
            if key.startswith("items[") and "][" in key:
                index = key.split("[")[1].split("]")[0]
                item_indexes.add(index)

        for index in sorted(item_indexes, key=int):
            item = {
                'medicine_id': int(data.get(f'items[{index}][medicine_id]')),
                'batch_no': data.get(f'items[{index}][batch_no]'),
                'expiry_date': data.get(f'items[{index}][expiry_date]'),
                'quantity': int(data.get(f'items[{index}][quantity]', 0)),
                'purchase_price': float(data.get(f'items[{index}][purchase_price]', 0)),
                'mrp': float(data.get(f'items[{index}][mrp]', 0)),
                'sale_price': float(data.get(f'items[{index}][sale_price]', 0)),
                'tax_rate': float(data.get(f'items[{index}][tax_rate]', 0) or 0),
                'tax_amount': float(data.get(f'items[{index}][tax_amount]', 0) or 0),
                'packing_qty': int(data.get(f'items[{index}][packing_qty]', 1))  # Optional
            }
            items.append(item)

        # Create the purchase record
        purchase = MedicinePurchase(
            bill_no=generate_next_number(MedicinePurchase, 'PUR', 'bill_no'),
            purchase_date=datetime.datetime.strptime(data['purchase_date'], '%Y-%m-%d'),
            supplier_id=int(data['supplier_id']),
            subtotal=float(data['subtotal']),
            discount_percent=float(data.get('discount_percent', 0)),
            discount_amount=float(data.get('discount_amount', 0)),
            tax_amount=float(data.get('tax_amount', 0)),
            total_amount=float(data['total_amount']),
            paid_amount=float(data.get('paid_amount', 0)),
            due_amount=float(data.get('due_amount', 0)),
            payment_mode=data.get('payment_mode', 'Cash'),
            payment_note=data.get('payment_note', ''),
            note=data.get('note', ''),
            created_by=current_user
        )
        db.session.add(purchase)
        db.session.flush()

        for item_data in items:
            medicine = Medicine.query.get(item_data['medicine_id'])
            if not medicine:
                continue

            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                medicine_id=item_data['medicine_id'],
                batch_no=item_data['batch_no'],
                expiry_date=datetime.datetime.strptime(item_data['expiry_date'], '%Y-%m-%d'),
                packing_qty=item_data['packing_qty'],
                quantity=item_data['quantity'],
                mrp=item_data['mrp'],
                purchase_price=item_data['purchase_price'],
                sale_price=item_data['sale_price'],
                tax_rate=item_data['tax_rate'],
                tax_amount=item_data['tax_amount'],
                amount=item_data['quantity'] * item_data['purchase_price']
            )
            db.session.add(purchase_item)
            db.session.flush()

            batch = MedicineBatch(
                medicine_id=item_data['medicine_id'],
                purchase_item_id=purchase_item.id,
                batch_no=item_data['batch_no'],
                expiry_date=datetime.datetime.strptime(item_data['expiry_date'], '%Y-%m-%d'),
                purchase_price=item_data['purchase_price'],
                selling_price=item_data['sale_price'],
                mrp=item_data['mrp'],
                tax_rate=item_data['tax_rate'],
                initial_quantity=item_data['quantity'],
                current_stock=item_data['quantity']
            )
            db.session.add(batch)

            # medicine.current_stock += item_data['quantity']
            db.session.add(batch)
            db.session.flush()  # ✅ Force batch.id to be generated

            transaction = StockTransaction(
                medicine_id=medicine.id,
                batch_id=batch.id,
                transaction_type='purchase',
                quantity=item_data['quantity'],
                balance=batch.current_stock,
                reference=f"Purchase {purchase.bill_no}",
                notes=f"Initial purchase of {item_data['quantity']} units",
                created_by=current_user
            )
            db.session.add(transaction)

        db.session.commit()
        flash('Purchase added successfully!', 'success')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)


    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # <-- Add this to print full error to console
        flash(f'Error adding purchase: {str(e)}', 'danger')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)


@admin.route(PHARMACY_PURCHASES_VIEW + '/<int:purchase_id>', methods=['GET'], endpoint='medicine-purchases/view')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def view_purchase(current_user, purchase_id):
    purchase = MedicinePurchase.query.get_or_404(purchase_id)
    items = PurchaseItem.query.filter_by(purchase_id=purchase_id).all()

    return render_template('admin_templates/pharmacy/purchase_view.html',
                           purchase=purchase,
                           items=items,
                           datetime=datetime.datetime,
                           ADMIN=ADMIN,
                           PHARMACY_MEDICINE_PURCHASE_PAYMENT=PHARMACY_PURCHASES_PAYMENT,
                           PHARMACY_MEDICINE_PURCHASES_PRINT=PHARMACY_PURCHASES_PRINT,
                           PHARMACY_PURCHASES_DELETE=PHARMACY_PURCHASES_DELETE,
                           PHARMACY_PURCHASES_LIST=PHARMACY_PURCHASES_LIST)


@admin.route(PHARMACY_PURCHASES_PAYMENT + '/<int:purchase_id>', methods=['POST'])
def add_purchase_payment(purchase_id):
    # Get the purchase record
    purchase = MedicinePurchase.query.get_or_404(purchase_id)

    # Check if purchase is deleted
    if purchase.is_deleted:
        flash('Cannot add payment to a deleted purchase', 'error')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)

    try:
        # Get form data
        amount = Decimal(request.form.get('amount'))
        print(amount)
        payment_date = datetime.datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d')
        payment_mode = request.form.get('payment_mode', 'Cash')
        note = request.form.get('note', '')

        # Validate payment amount
        if amount <= Decimal('0.00'):
            flash('Payment amount must be positive', 'error')
            return redirect(url_for('medicine_purchase_details', purchase_id=purchase_id))

        if amount > purchase.due_amount:
            flash('Payment amount cannot exceed due amount', 'error')
            return redirect(url_for('medicine_purchase_details', purchase_id=purchase_id))

        # Update purchase payment info
        purchase.paid_amount += amount
        purchase.due_amount = purchase.total_amount - purchase.paid_amount
        purchase.payment_mode = payment_mode
        purchase.payment_note = note
        purchase.updated_at = datetime.datetime.utcnow()

        db.session.commit()

        flash('Payment recorded successfully!', 'success')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)

    except ValueError as e:
        traceback.print_exc()
        flash('Invalid payment data provided', 'error')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash('An error occurred while recording payment', 'error')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)


@admin.route(PHARMACY_PURCHASES_DELETE + '/<int:purchase_id>', methods=['POST'], endpoint='medicine-purchases/delete')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_purchase(current_user, purchase_id):
    purchase = MedicinePurchase.query.options(db.joinedload(MedicinePurchase.items)).get_or_404(purchase_id)

    if purchase.is_deleted:
        flash('This purchase is already deleted.', 'warning')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)

    try:
        # Step 1: Soft-delete the main purchase record
        purchase.is_deleted = True
        purchase.deleted_at = datetime.datetime.utcnow()
        purchase.updated_at = datetime.datetime.utcnow()

        # Step 2: Process each purchase item to reverse stock and log transactions
        for item in purchase.items:
            # Soft-delete the purchase item
            item.is_deleted = True
            item.deleted_at = datetime.datetime.utcnow()
            item.updated_at = datetime.datetime.utcnow()

            batch = item.batch  # This directly gives you the MedicineBatch object

            if batch:  # Check if a batch was successfully linked
                # Update stock: Subtract the quantity from the batch's current_stock
                batch.current_stock -= item.quantity

                # Create a StockTransaction entry for this stock reduction
                stock_transaction = StockTransaction(
                    medicine_id=item.medicine_id,
                    batch_id=batch.id,  # Use batch.id now that we have the batch object
                    transaction_type='purchase_delete',
                    quantity=-item.quantity,  # Negative quantity indicates stock reduction
                    balance=batch.current_stock,  # New current stock of the batch *after* reduction
                    reference=f"Purchase Delete (Bill: {purchase.bill_no})",
                    notes=f"Stock reduced due to deletion of purchase (Purchase ID: {purchase.id})",
                    created_by=current_user  # Assuming StockTransaction has 'created_by_id' FK
                )
                db.session.add(stock_transaction)

            else:
                flash(
                    f'Warning: No batch found for item "{item.medicine.name}" (Batch No: {item.batch_no}) in purchase deletion. Stock reversal incomplete.',
                    'warning')

        db.session.commit()
        flash(f'Purchase {purchase.bill_no} soft-deleted and stock updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error deleting purchase {purchase.bill_no}: {str(e)}', 'danger')

    return redirect(ADMIN + PHARMACY_PURCHASES_LIST)  # Redirect to the main purchases list


@admin.route(PHARMACY_PURCHASES_RESTORE + '/<int:purchase_id>', methods=['POST'], endpoint='medicine-purchases/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_purchase(current_user, purchase_id):
    purchase = MedicinePurchase.query.options(db.joinedload(MedicinePurchase.items)).get_or_404(purchase_id)

    if not purchase.is_deleted:
        flash('This purchase is not deleted and cannot be restored.', 'warning')
        return redirect(ADMIN + PHARMACY_PURCHASES_LIST)

    try:
        # Step 1: Restore the main purchase record
        purchase.is_deleted = False
        purchase.deleted_at = None  # Clear deleted_at timestamp
        purchase.updated_at = datetime.datetime.utcnow()

        # Step 2: Process each purchase item to reverse soft-deletion and restore stock
        for item in purchase.items:
            # Only restore items that were part of this purchase and were marked deleted
            if item.is_deleted:
                item.is_deleted = False
                item.deleted_at = None
                item.updated_at = datetime.datetime.utcnow()

                batch = item.batch  # This directly gives you the MedicineBatch object

                if batch:  # Check if a batch was successfully linked
                    batch.current_stock += item.quantity

                    # Step 3: Create a StockTransaction entry for this stock increase
                    stock_transaction = StockTransaction(
                        medicine_id=item.medicine_id,
                        batch_id=batch.id,  # Use batch.id now that we have the batch object
                        transaction_type='purchase_restore',  # Clear type for audit trail
                        quantity=item.quantity,  # Positive quantity for stock incoming/restoration
                        balance=batch.current_stock,
                        # IMPORTANT: This is the new current stock of the batch *after* restoration
                        reference=f"Purchase Restore (Bill: {purchase.bill_no})",
                        notes=f"Stock restored due to purchase restoration (Purchase ID: {purchase.id})",
                        created_by=current_user  # Use current_user.id for FK
                    )
                    db.session.add(stock_transaction)
                else:
                    flash(
                        f'Warning: No batch found for item "{item.medicine.name}" (Batch No: {item.batch_no}) during restore. Stock not fully restored.',
                        'warning')

        db.session.commit()
        flash(f'Purchase {purchase.bill_no} and its associated items restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Log full traceback for debugging
        flash(f'Error restoring purchase {purchase.bill_no}: {str(e)}', 'danger')

    return redirect(ADMIN + PHARMACY_PURCHASES_LIST)  # Or PHARMACY_MEDICINE_PURCHASES_TRASH if applicable


@admin.route(PHARMACY_STOCK_LEVELS, methods=['GET'], endpoint='stock_levels')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def stock_levels(current_user):
    medicines = Medicine.query.filter_by(is_deleted=0).order_by(Medicine.name).all()

    # Categorize by stock status
    low_stock = [m for m in medicines if m.current_stock < m.min_level]
    normal_stock = [m for m in medicines if m.min_level <= m.current_stock < m.reorder_level]
    good_stock = [m for m in medicines if m.current_stock >= m.reorder_level]

    return render_template('admin_templates/pharmacy/stock_levels.html',
                           low_stock=low_stock,
                           normal_stock=normal_stock,
                           good_stock=good_stock,
                           ADMIN=ADMIN)


@admin.route('/medicine-batches/adjust/<int:batch_id>', methods=['POST'], endpoint='medicine-batches/adjust')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def adjust_batch_stock(current_user, batch_id):
    batch = MedicineBatch.query.get_or_404(batch_id)
    medicine = Medicine.query.get_or_404(batch.medicine_id)

    try:
        adjustment_type = request.form.get('adjustment_type')  # add or remove
        quantity = int(request.form.get('quantity'))
        notes = request.form.get('notes', '')

        if adjustment_type == 'add':
            batch.current_stock += quantity
            medicine.current_stock += quantity
        elif adjustment_type == 'remove':
            if batch.current_stock < quantity:
                flash('Cannot remove more stock than available!', 'danger')
                return redirect(ADMIN + f'/medicine-batches?medicine_id={batch.medicine_id}')

            batch.current_stock -= quantity
            medicine.current_stock -= quantity

        # Create transaction
        transaction = StockTransaction(
            medicine_id=batch.medicine_id,
            batch_id=batch.id,
            transaction_type='manual_adjustment',
            quantity=quantity if adjustment_type == 'add' else -quantity,
            balance=medicine.current_stock,
            reference=f"Manual Adjustment",
            notes=notes,
            user_id=current_user
        )
        db.session.add(transaction)
        db.session.commit()

        flash('Stock adjusted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adjusting stock: {str(e)}', 'danger')

    return redirect(ADMIN + f'/medicine-batches?medicine_id={batch.medicine_id}')


# API Endpoints for AJAX calls
@admin.route('/api/medicine-batches/<int:medicine_id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def get_medicine_batches_api(current_user, medicine_id):
    batches = MedicineBatch.query \
        .filter_by(medicine_id=medicine_id, is_deleted=0) \
        .filter(MedicineBatch.current_stock > 0) \
        .filter(MedicineBatch.expiry_date >= datetime.datetime.now().date()) \
        .order_by(MedicineBatch.expiry_date.asc()) \
        .all()

    return jsonify([{
        'id': b.id,
        'batch_no': b.batch_no,
        'expiry_date': b.expiry_date.isoformat(),
        'current_stock': b.current_stock,
        'selling_price': float(b.selling_price),
        'days_to_expiry': (b.expiry_date - datetime.datetime.now().date()).days
    } for b in batches])


@admin.route(PHARMACY_PURCHASES_PRINT + '/<int:purchase_id>', methods=['GET'])
def print_purchase_bill(purchase_id):
    purchase = MedicinePurchase.query.get_or_404(purchase_id)

    # Load items if not already loaded (good practice if not using eager loading)
    if not hasattr(purchase, 'items') or not purchase.items:
        items = PurchaseItem.query.filter_by(purchase_id=purchase_id).all()
        purchase.items = items  # Attach to the purchase object for consistent access

    return render_template(
        'admin_templates/pharmacy/purchase_print_view.html',  # <--- NEW TEMPLATE NAME
        purchase=purchase,
        items=purchase.items,  # Pass items explicitly for clarity
        datetime=datetime.datetime  # For date formatting in template
    )


@admin.route(PHARMACY_PURCHASES_EXPORT, methods=['GET'], endpoint='export_purchases')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_purchases(current_user):
    # Get parameters from the request
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    export_format = request.args.get('format')

    # --- 1. Validate and Parse Dates ---
    try:
        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = datetime.date(1900, 1, 1)  # Default to a very old date if not provided

        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = datetime.date.today()  # Default to today if not provided

        # Adjust end_date to include the entire day
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time())

        if start_date > end_date:
            flash('Start date cannot be after end date.', 'error')
            return redirect(url_for('admin.medicine_purchases_list'))  # Redirect back to list
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        return redirect(url_for('admin.medicine_purchases_list'))

    # --- 2. Query Data from Database (Filtered by Date Range) ---
    purchases_query = MedicinePurchase.query.filter(
        MedicinePurchase.purchase_date >= start_date,
        MedicinePurchase.purchase_date <= end_datetime,  # Use the adjusted end_datetime
        MedicinePurchase.is_deleted == False  # Exclude soft-deleted purchases
    ).options(
        joinedload(MedicinePurchase.supplier)  # Eager load supplier data
    ).order_by(MedicinePurchase.purchase_date.asc()).all()

    # --- 3. Prepare Data for Export (Pandas DataFrame for flexibility) ---
    data_for_export = []
    for purchase in purchases_query:
        # Calculate due amount if not directly stored or to confirm
        due_amount_calc = purchase.total_amount - purchase.paid_amount

        data_for_export.append({
            'Bill No': purchase.bill_no,
            'Purchase Date': purchase.purchase_date.strftime('%Y-%m-%d'),
            'Supplier': purchase.supplier.name if purchase.supplier else 'N/A',
            'Payment Mode': purchase.payment_mode,
            'Subtotal': float(purchase.subtotal),  # Convert Decimal to float for export
            'Discount Amount': float(purchase.discount_amount),
            'Tax Amount': float(purchase.tax_amount),
            'Total Amount': float(purchase.total_amount),
            'Paid Amount': float(purchase.paid_amount),
            'Due Amount': float(due_amount_calc),
            'Status': 'Paid' if due_amount_calc <= Decimal('0.01') else 'Due',
            'Note': purchase.note or ''
        })

    # Create DataFrame from the list of dictionaries
    df = pd.DataFrame(data_for_export)

    if df.empty:
        flash('No purchase records found for the selected date range.', 'warning')
        return redirect(url_for('admin.medicine_purchases_list'))

    # --- 4. Generate Report in Selected Format ---
    filename_suffix = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"

    if export_format == 'csv':
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        return Response(
            csv_buffer.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=purchases_{filename_suffix}.csv"}
        )

    elif export_format == 'excel':
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Purchases')
        excel_buffer.seek(0)
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'purchases_{filename_suffix}.xlsx'
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
        elements.append(Paragraph("Purchases Report", title_style))
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
                # Format specific columns
                if col_name in ['Subtotal', 'Discount Amount', 'Tax Amount', 'Total Amount', 'Paid Amount',
                                'Due Amount']:
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
                # Get the text content from the Paragraph object and measure its raw width
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
            # Align numeric columns to the right
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Subtotal to Due Amount
        ]))

        elements.append(table)
        doc.build(elements)
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'purchases_{filename_suffix}.pdf'
        )

    else:
        flash('Invalid export format requested.', 'error')
        return redirect(url_for('admin.medicine_purchases_list'))
