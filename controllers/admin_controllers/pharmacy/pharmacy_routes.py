import datetime
import io

import pandas as pd
from flask import render_template, request, flash, redirect, send_file, jsonify
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import PHARMACY_MEDICINE_BATCHES, PHARMACY_STOCK_TRANSACTIONS, \
    PHARMACY_MEDICINES_LIST, ADMIN, PHARMACY_MEDICINE_ADD, PHARMACY_MEDICINE_EDIT, PHARMACY_MEDICINE_DELETE, \
    PHARMACY_MEDICINE_RESTORE, PHARMACY_MEDICINE_DISPENSE, PHARMACY_MEDICINE_EXPORT, PHARMACY_MEDICINE_IMPORT, \
    PHARMACY_MEDICINE_IMPORT_SAMPLE
from middleware.auth_middleware import token_required
from models.medicineModel import Medicine, StockTransaction, MedicineCategory, MedicineCompany, MedicineGroup, \
    MedicineUnit, MedicineBatch
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


# Utility functions
def generate_next_number(model, prefix, number_field):
    last_record = model.query.order_by(model.id.desc()).first()
    if last_record:
        last_num = int(getattr(last_record, number_field).replace(prefix, ''))
        return f"{prefix}{last_num + 1:04d}"
    return f"{prefix}0001"


@admin.route(PHARMACY_MEDICINES_LIST, methods=['GET'], endpoint='medicine-list')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def pharmacy_medicine_list(current_user):
    medicines = Medicine.query.filter_by(is_deleted=0).order_by(Medicine.name).all()
    categories = MedicineCategory.query.filter_by(is_deleted=0).order_by(MedicineCategory.name).all()
    companies = MedicineCompany.query.filter_by(is_deleted=0).order_by(MedicineCompany.name).all()
    groups = MedicineGroup.query.filter_by(is_deleted=0).order_by(MedicineGroup.name).all()
    units = MedicineUnit.query.filter_by(is_deleted=0).order_by(MedicineUnit.name).all()
    archived_medicines = Medicine.query.filter_by(is_deleted=1).order_by(Medicine.deleted_at.desc()).all()

    return render_template('admin_templates/pharmacy/medicine_inventory.html',
                           medicines=medicines,
                           categories=categories,
                           companies=companies,
                           groups=groups,
                           units=units,
                           datetime=datetime.datetime,
                           timedelta=datetime.timedelta,
                           archived_medicines=archived_medicines,
                           ADMIN=ADMIN,
                           PHARMACY_MEDICINE_ADD=PHARMACY_MEDICINE_ADD,
                           PHARMACY_MEDICINE_EDIT=PHARMACY_MEDICINE_EDIT,
                           PHARMACY_MEDICINE_DELETE=PHARMACY_MEDICINE_DELETE,
                           PHARMACY_MEDICINE_RESTORE=PHARMACY_MEDICINE_RESTORE,
                           PHARMACY_MEDICINE_DISPENSE=PHARMACY_MEDICINE_DISPENSE,
                           PHARMACY_MEDICINE_EXPORT=PHARMACY_MEDICINE_EXPORT,
                           PHARMACY_MEDICINE_IMPORT=PHARMACY_MEDICINE_IMPORT,
                           PHARMACY_MEDICINE_SAMPLE_IMPORT=PHARMACY_MEDICINE_IMPORT_SAMPLE,
                           PHARMACY_MEDICINE_BATCHES=PHARMACY_MEDICINE_BATCHES,
                           PHARMACY_STOCK_TRANSACTIONS=PHARMACY_STOCK_TRANSACTIONS)

@admin.route(PHARMACY_MEDICINE_ADD, methods=['POST'], endpoint='medicine-add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_medicine(current_user):
    try:
        medicine = Medicine(
            medicine_number=generate_next_number(Medicine, 'MED', 'medicine_number'),
            name=request.form.get('name'),
            description=request.form.get('description'),
            composition=request.form.get('composition'),
            category_id=request.form.get('category_id'),
            company_id=request.form.get('company_id'),
            group_id=request.form.get('group_id'),
            unit_id=request.form.get('unit_id'),
            min_level=int(request.form.get('min_level', 0)),
            reorder_level=int(request.form.get('reorder_level', 10)),
            box_packing=int(request.form.get('box_packing', 1)),
            rack_number=request.form.get('rack_number'),
            default_tax_rate=float(request.form.get('default_tax_rate', 0)),
            vat_account=request.form.get('vat_account'),
            default_purchase_price=float(request.form.get('default_purchase_price', 0)),
            default_selling_price=float(request.form.get('default_selling_price', 0)),
            default_mrp=float(request.form.get('default_mrp', 0)),
            barcode=request.form.get('barcode')
        )

        db.session.add(medicine)
        db.session.flush()  # Get medicine.id without committing

        # Record initial stock if provided
        initial_stock = int(request.form.get('initial_stock', 0))
        if initial_stock > 0:
            transaction = StockTransaction(
                medicine_id=medicine.id,
                transaction_type='initial',
                quantity=initial_stock,
                balance=initial_stock,
                notes='Initial stock',
                user_id=current_user
            )
            medicine.current_stock = initial_stock
            db.session.add(transaction)

        db.session.commit()
        flash('Medicine added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

@admin.route(PHARMACY_MEDICINE_EDIT + '/<int:id>', methods=['POST'], endpoint='medicine-edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        medicine.name = request.form.get('name')
        medicine.description = request.form.get('description')
        medicine.composition = request.form.get('composition')
        medicine.category_id = request.form.get('category_id')
        medicine.company_id = request.form.get('company_id')
        medicine.group_id = int(request.form.get('group_id'))
        medicine.unit_id = request.form.get('unit_id')
        medicine.min_level = int(request.form.get('min_level', 0))
        medicine.reorder_level = int(request.form.get('reorder_level', 10))
        medicine.box_packing = int(request.form.get('box_packing', 1))
        medicine.rack_number = request.form.get('rack_number')
        medicine.default_tax_rate = float(request.form.get('default_tax_rate', 0))
        medicine.vat_account = request.form.get('vat_account')
        medicine.default_purchase_price = float(request.form.get('default_purchase_price', 0))
        medicine.default_selling_price = float(request.form.get('default_selling_price', 0))
        medicine.default_mrp = float(request.form.get('default_mrp', 0))
        medicine.barcode = request.form.get('barcode')

        db.session.commit()
        flash('Medicine updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

@admin.route(PHARMACY_MEDICINE_DELETE + '/<int:id>', methods=['POST'], endpoint='medicine-delete')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        # Soft delete associated transactions
        StockTransaction.query.filter_by(medicine_id=id).update({
            'is_deleted': True,
            'deleted_at': datetime.datetime.utcnow()
        })

        medicine.is_deleted = True
        medicine.deleted_at = datetime.datetime.utcnow()
        db.session.commit()
        flash('Medicine deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting medicine: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)


@admin.route(PHARMACY_MEDICINE_RESTORE + '/<int:id>', methods=['POST'], endpoint='medicine-restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)
    try:
        # Restore associated transactions
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
    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)


# Export medicines
@admin.route(PHARMACY_MEDICINE_EXPORT + '/<format>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_medicines(current_user, format):
    medicines = Medicine.query.filter_by(is_deleted=0).all()

    # Prepare data for export
    data = []
    for med in medicines:
        data.append({
            'Medicine Number': med.medicine_number,
            'Name': med.name,
            'Description': med.description,
            'Category': med.category.name if med.category else '',
            'Company': med.company.name if med.company else '',
            'Group': med.group.name if med.group else '',
            'Unit': med.unit.name if med.unit else '',
            'Current Stock': med.current_stock,
            'Min Level': med.min_level,
            'Reorder Level': med.reorder_level,
            'Purchase Price': med.default_purchase_price,
            'Selling Price': med.default_selling_price,
            'MRP': med.default_mrp,
            'Tax Rate': med.default_tax_rate,
            'Barcode': med.barcode,
            'Created At': med.created_at.strftime('%Y-%m-%d %H:%M')
        })

    df = pd.DataFrame(data)

    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='medicines.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Medicines')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='medicines.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()

        styles = getSampleStyleSheet()

        # Define a normal style for table content that allows wrapping
        normal_style = styles['Normal']
        normal_style.fontName = "Helvetica"
        normal_style.fontSize = 8  # Slightly smaller font for dense inventory reports
        normal_style.leading = 9  # Line spacing for wrapped text

        # Define a bold style for table headers
        header_style = styles['h3']
        header_style.fontName = "Helvetica-Bold"
        header_style.fontSize = 9  # Slightly smaller font for headers

        # Title setup
        title_text = "Medicines Inventory Report"
        title = Paragraph(title_text, styles['Title'])

        # --- Prepare PDF data with Paragraph objects for wrapping ---
        pdf_data = []
        # Add header row, ensuring headers are also Paragraphs for consistency in styling
        pdf_data.append([Paragraph(col, header_style) for col in df.columns.tolist()])

        # Add data rows, wrapping all cell content in Paragraphs
        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = letter[0] - LEFT_MARGIN - RIGHT_MARGIN

        col_widths = []
        min_col_width_per_column = 0.6 * inch
        padding_per_side = 0.08 * inch

        for col_idx in range(len(df.columns)):
            max_content_width_in_points = 0
            for row in pdf_data:
                # Get the text content from the Paragraph object and measure its raw width
                if isinstance(row[col_idx], Paragraph):
                    text_to_measure = row[col_idx].text
                else:
                    text_to_measure = str(row[col_idx])

                # Use stringWidth for precise text width calculation
                width = stringWidth(text_to_measure, normal_style.fontName, normal_style.fontSize)
                if width > max_content_width_in_points:
                    max_content_width_in_points = width

            # Add padding to the estimated content width
            estimated_col_width = max_content_width_in_points + (2 * padding_per_side)

            # Ensure it meets a minimum width for very short content or empty cells
            estimated_col_width = max(estimated_col_width, min_col_width_per_column)
            col_widths.append(estimated_col_width)

        total_estimated_width = sum(col_widths)
        if total_estimated_width > AVAILABLE_WIDTH:
            scaling_factor = AVAILABLE_WIDTH / total_estimated_width
            col_widths = [w * scaling_factor for w in col_widths]

        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))  # Add a small spacer after the title

        # Create table with calculated column widths
        table = Table(pdf_data, colWidths=col_widths)

        # Table Style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),  # Header font size for style
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),  # Reduced padding
            ('TOPPADDING', (0, 0), (-1, 0), 6),  # Reduced padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),  # Light grey for data rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Finer grid lines
            ('LEFTPADDING', (0, 0), (-1, -1), 5),  # Reduced padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),  # Reduced padding
            # Note: FONTNAME/FONTSIZE for data rows are controlled by Paragraph's normal_style
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='medicines_inventory_report.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)


# Sample Excel file structure for import
SAMPLE_MEDICINE_STRUCTURE = [
    {
        "Name": "Paracetamol 500mg",
        "Description": "Pain reliever and fever reducer",
        "Category": "Pain Relievers",
        "Company": "ABC Pharma",
        "Group": "Analgesics",
        "Unit": "Tablet",
        "Min Level": 100,
        "Reorder Level": 200,
        "Purchase Price": 0.50,
        "Selling Price": 1.00,
        "MRP": 1.20,
        "Tax Rate": 5.0,
        "Barcode": "123456789012"
    }
]


# Download sample import file
@admin.route(PHARMACY_MEDICINE_IMPORT_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_medicine_file(current_user):
    df = pd.DataFrame(SAMPLE_MEDICINE_STRUCTURE)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Medicines')
        # Add instructions
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING MEDICINES:",
            "",
            "1. Use the 'Medicines' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: All other columns",
            "4. For category, company, group, and unit - use existing names exactly",
            "5. Do not modify the column headers",
            "6. Remove these instructions before importing",
            "7. Save the file as .xlsx format"
        ]

        for row, line in enumerate(instructions):
            worksheet.write(row, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_medicines.xlsx'
    )


# Import medicines
@admin.route(PHARMACY_MEDICINE_IMPORT, methods=['POST'], endpoint="import_medicines")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_medicines(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Validate columns
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

        # Process each row
        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                if not name or pd.isna(name):
                    error_count += 1
                    continue

                # Get related IDs
                category = MedicineCategory.query.filter_by(name=row.get('Category', '')).first()
                company = MedicineCompany.query.filter_by(name=row.get('Company', '')).first()
                group = MedicineGroup.query.filter_by(name=row.get('Group', '')).first()
                unit = MedicineUnit.query.filter_by(name=row.get('Unit', '')).first()

                print(f"category : {category}")
                # Check if medicine exists
                existing = Medicine.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        # Update existing medicine
                        existing.description = row.get('Description', existing.description)
                        existing.composition = row.get('Composition', existing.composition)
                        existing.category_id = category.id if category else existing.category_id
                        existing.company_id = company.id if company else existing.company_id
                        existing.group_id = group.id if group else existing.group_id
                        existing.unit_id = unit.id if unit else existing.unit_id
                        existing.min_level = int(row.get('Min Level', existing.min_level))
                        existing.reorder_level = int(row.get('Reorder Level', existing.reorder_level))
                        existing.default_purchase_price = float(
                            row.get('Purchase Price', existing.default_purchase_price))
                        existing.default_selling_price = float(row.get('Selling Price', existing.default_selling_price))
                        existing.default_mrp = float(row.get('MRP', existing.default_mrp))
                        existing.default_tax_rate = float(row.get('Tax Rate', existing.default_tax_rate))
                        existing.barcode = row.get('Barcode', existing.barcode)
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Create new medicine
                    new_medicine = Medicine(
                        medicine_number=generate_next_number(Medicine, 'MED', 'medicine_number'),
                        name=name,
                        description=row.get('Description', ''),
                        composition=row.get('Composition', ''),
                        category_id=category.id if category else None,
                        company_id=company.id if company else None,
                        group_id=group.id if group else None,
                        unit_id=unit.id if unit else None,
                        min_level=int(row.get('Min Level', 0)),
                        reorder_level=int(row.get('Reorder Level', 10)),
                        default_purchase_price=float(row.get('Purchase Price', 0)),
                        default_selling_price=float(row.get('Selling Price', 0)),
                        default_mrp=float(row.get('MRP', 0)),
                        default_tax_rate=float(row.get('Tax Rate', 0)),
                        barcode=row.get('Barcode', '')
                    )
                    db.session.add(new_medicine)
                    success_count += 1

                db.session.commit()

            except Exception as e:
                error_count += 1
                db.session.rollback()
                continue

        flash(f'Import completed: {success_count} successful, {error_count} failed',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

@admin.route('/medicines/forward-post/<int:id>', methods=['GET'])
def forward_to_post(id):
    return f'''
    <form id="forwardForm" action="/admin/pharmacy/transactions-medicine" method="post">
        <input type="hidden" name="medicine_id" value="{id}" />
    </form>
    <script>document.getElementById("forwardForm").submit();</script>
    '''


@admin.route(PHARMACY_MEDICINE_DISPENSE + '/<int:id>', methods=['POST'], endpoint='medicine-dispense')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def dispense_medicine(current_user, id):
    medicine = Medicine.query.get_or_404(id)

    try:
        quantity_to_dispense = int(request.form.get('quantity'))
        notes = request.form.get('notes', '').strip()
        reference = request.form.get('reference', '').strip()

        if quantity_to_dispense <= 0:
            flash('Quantity to dispense must be positive.', 'warning')
            return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

        if medicine.current_stock < quantity_to_dispense:
            flash(f'Not enough stock. Only {medicine.current_stock} units of {medicine.name} available.', 'danger')
            return redirect(ADMIN + PHARMACY_MEDICINES_LIST)

        remaining_qty_to_process = quantity_to_dispense

        eligible_batches = MedicineBatch.query.filter(
            MedicineBatch.medicine_id == medicine.id,
            MedicineBatch.is_deleted == False,
            MedicineBatch.expiry_date >= datetime.datetime.today(),  # Only non-expired batches
            MedicineBatch.current_stock > 0
        ).order_by(MedicineBatch.expiry_date.asc(), MedicineBatch.created_at.asc()).all()

        batches_affected = []

        # Iterate through batches and dispense stock
        for batch in eligible_batches:
            if remaining_qty_to_process <= 0:
                break  # All quantity dispensed

            # Determine how much to take from the current batch
            qty_from_this_batch = min(remaining_qty_to_process, batch.current_stock)

            # Update batch stock
            batch.current_stock -= qty_from_this_batch

            # Track remaining quantity needed
            remaining_qty_to_process -= qty_from_this_batch

            # Store batch and dispensed quantity for transaction logging
            batches_affected.append({
                'batch_obj': batch,
                'dispensed_qty': qty_from_this_batch
            })

        # Final check if all quantity was dispensed (should be caught by initial check but good for safety)
        if remaining_qty_to_process > 0:
            flash(
                f'Could not fully dispense {quantity_to_dispense} units. Only {quantity_to_dispense - remaining_qty_to_process} units were dispensed due to batch availability issues.',
                'danger')
            db.session.rollback()  # Rollback any partial updates
            return redirect(f"/admin/medicines/forward-post/{id}")

        # Create StockTransaction records for each affected batch
        for item in batches_affected:
            batch_obj = item['batch_obj']
            dispensed_qty = item['dispensed_qty']

            transaction = StockTransaction(
                medicine_id=medicine.id,
                batch_id=batch_obj.id,  # Link to the specific batch affected
                transaction_type='dispense',
                quantity=-dispensed_qty,  # Negative quantity for outgoing stock
                balance=batch_obj.current_stock,  # Stock balance of this specific batch AFTER dispense
                notes=notes,
                reference=reference,
                created_by=current_user  # Use current_user.id for the foreign key
            )
            db.session.add(transaction)

        db.session.commit()
        flash(f'Successfully dispensed {quantity_to_dispense} units of {medicine.name}.', 'success')

    except ValueError as ve:
        db.session.rollback()
        flash(f'Validation Error: {str(ve)}', 'danger')
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()  # Log full traceback to console for debugging
        flash(f'Error dispensing medicine: {str(e)}', 'danger')

    return redirect(ADMIN + PHARMACY_MEDICINES_LIST)


# Batch Management Routes
@admin.route(PHARMACY_MEDICINE_BATCHES, methods=['GET'], endpoint='medicine_batches')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def medicine_batches(current_user):
    medicine_id = request.args.get('medicine_id')
    status = request.args.get('status', 'all')  # all, active, expired

    query = MedicineBatch.query.filter_by(is_deleted=0)

    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)

    if status == 'active':
        query = query.filter(MedicineBatch.expiry_date >= datetime.datetime.now().date())
    elif status == 'expired':
        query = query.filter(MedicineBatch.expiry_date < datetime.datetime.now().date())

    batches = query.order_by(MedicineBatch.expiry_date.asc()).all()

    return render_template('admin_templates/pharmacy/batches.html',
                           batches=batches,
                           datetime=datetime.datetime,
                           ADMIN=ADMIN)


@admin.route(PHARMACY_STOCK_TRANSACTIONS, methods=['GET'], endpoint='stock_transactions')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def stock_transactions(current_user):
    medicine_id = request.args.get('medicine_id')
    batch_id = request.args.get('batch_id')

    query = StockTransaction.query

    if medicine_id:
        query = query.filter_by(medicine_id=medicine_id)
    if batch_id:
        query = query.filter_by(batch_id=batch_id)

    transactions = query.order_by(StockTransaction.created_at.desc()).all()

    return render_template('admin_templates/pharmacy/stock_transactions.html',
                           transactions=transactions,
                           ADMIN=ADMIN)


@admin.route('/api/medicines/search')
def search_medicines():
    search_term = request.args.get('q', '').strip()

    if not search_term:
        return jsonify([])

    medicines = Medicine.query.filter(
        or_(
            Medicine.name.ilike(f'%{search_term}%'),
            Medicine.medicine_number.ilike(f'%{search_term}%')
        ),
        Medicine.is_deleted == False
    ).options(
        joinedload(Medicine.category),
        joinedload(Medicine.company),
        joinedload(Medicine.group),
        joinedload(Medicine.unit)
    ).limit(10).all()

    return jsonify([{
        'id': med.id,
        'name': med.name,
        'medicine_number': med.medicine_number,
        'default_selling_price': float(med.default_selling_price) if med.default_selling_price else None,
        'default_mrp': float(med.default_mrp) if med.default_mrp else None,
        'category': med.category.name if med.category else None,
        'company': med.company.name if med.company else None,
        'group': med.group.name if med.group else None,
        'unit': med.unit.name if med.unit else None,
        'current_stock': med.current_stock,
        'status': med.status
    } for med in medicines])
