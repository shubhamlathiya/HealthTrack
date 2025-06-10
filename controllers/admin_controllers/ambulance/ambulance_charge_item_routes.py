import io
from datetime import datetime

import pandas as pd
from flask import render_template, request, redirect, flash, jsonify, send_file
from reportlab.lib import colors
# ReportLab imports for PDF export
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy.orm import joinedload

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, AMBULANCE_ITEM_LIST, AMBULANCE_ITEM_EDIT, AMBULANCE_ITEM_ADD, \
    AMBULANCE_ITEM_DELETE, AMBULANCE_ITEM_RESTORE, AMBULANCE_ITEM_TOGGLE_STATUS, AMBULANCE_ITEM_EXPORT, \
    AMBULANCE_ITEM_IMPORT, AMBULANCE_ITEM_IMPORT_SAMPLE, AJAX_GET_AMBULANCE_ITEM_DETAILS, AJAX_CHECK_AMBULANCE_ITEM_NAME
from models.ambulanceModel import AmbulanceCategory, AmbulanceChargeItem
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(AMBULANCE_ITEM_LIST, methods=['GET'], endpoint='ambulance-item-list')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def ambulance_charge_item_list():
    charge_items = AmbulanceChargeItem.query.options(
        joinedload(AmbulanceChargeItem.category)  # Eager load category
    ).filter_by(is_deleted=0).order_by(AmbulanceChargeItem.name).all()

    archived_items = AmbulanceChargeItem.query.options(
        joinedload(AmbulanceChargeItem.category)
    ).filter_by(is_deleted=1).order_by(AmbulanceChargeItem.name).all()

    # For 'Add Item' and 'Edit Item' modals, need active ambulance categories
    categories = AmbulanceCategory.query.filter_by(is_active=1, is_deleted=0).order_by(
        AmbulanceCategory.name).all()

    return render_template("admin_templates/ambulance/ambulance_charge_item_list.html",
                           charge_items=charge_items,
                           archived_items=archived_items,
                           categories=categories,
                           ADMIN=ADMIN,
                           AMBULANCE_ITEM_ADD=AMBULANCE_ITEM_ADD,
                           AMBULANCE_ITEM_EDIT=AMBULANCE_ITEM_EDIT,
                           AMBULANCE_ITEM_DELETE=AMBULANCE_ITEM_DELETE,
                           AMBULANCE_ITEM_RESTORE=AMBULANCE_ITEM_RESTORE,
                           AMBULANCE_ITEM_TOGGLE_STATUS=AMBULANCE_ITEM_TOGGLE_STATUS,
                           AMBULANCE_ITEM_EXPORT=AMBULANCE_ITEM_EXPORT,
                           AMBULANCE_ITEM_IMPORT=AMBULANCE_ITEM_IMPORT,
                           AMBULANCE_ITEM_IMPORT_SAMPLE=AMBULANCE_ITEM_IMPORT_SAMPLE,
                           )


@admin.route(AMBULANCE_ITEM_ADD, methods=['POST'], endpoint='add-ambulance-item')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def add_ambulance_charge_item():
    name = request.form.get('name', '').strip()
    standard_charge = request.form.get('standard_charge')
    category_id = request.form.get('category_id')

    if not name or not standard_charge or not category_id:
        flash('Name, Standard Charge, and Category for Ambulance Charge Item are required.', 'danger')
        return redirect(ADMIN + AMBULANCE_ITEM_LIST)

    try:
        standard_charge_float = float(standard_charge)
        if standard_charge_float < 0:
            flash('Standard Charge cannot be negative.', 'danger')
            return redirect(ADMIN + AMBULANCE_ITEM_LIST)

        # Check for duplicate item name within the same category
        existing = AmbulanceChargeItem.query.filter(
            AmbulanceChargeItem.name.ilike(name),
            AmbulanceChargeItem.category_id == int(category_id),
            AmbulanceChargeItem.is_deleted == False
        ).first()
        if existing:
            flash('Ambulance Charge Item with this name already exists in this category.', 'danger')
            return redirect(ADMIN + AMBULANCE_ITEM_LIST)

        new_item = AmbulanceChargeItem(
            name=name,
            standard_charge=standard_charge_float,
            category_id=int(category_id),
            is_active=True  # New items are active by default
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Ambulance Charge Item added successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid format for Standard Charge.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding Ambulance Charge Item: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


@admin.route(AMBULANCE_ITEM_EDIT + '/<int:id>', methods=['POST'], endpoint='edit-ambulance-item')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_ambulance_charge_item(id):
    item = AmbulanceChargeItem.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    standard_charge = request.form.get('standard_charge')
    category_id = request.form.get('category_id')
    is_active = request.form.get('is_active', 'off') == 'on'

    if not name or not standard_charge or not category_id:
        flash('Name, Standard Charge, and Category for Ambulance Charge Item are required.', 'danger')
        return redirect(ADMIN + AMBULANCE_ITEM_LIST)

    try:
        standard_charge_float = float(standard_charge)
        if standard_charge_float < 0:
            flash('Standard Charge cannot be negative.', 'danger')
            return redirect(ADMIN + AMBULANCE_ITEM_LIST)

        # Check for duplicate item name within the same category (excluding current item)
        existing = AmbulanceChargeItem.query.filter(
            AmbulanceChargeItem.name.ilike(name),
            AmbulanceChargeItem.category_id == int(category_id),
            AmbulanceChargeItem.id != id,
            AmbulanceChargeItem.is_deleted == False
        ).first()
        if existing:
            flash('Ambulance Charge Item with this name already exists in this category.', 'danger')
            return redirect(ADMIN + AMBULANCE_ITEM_LIST)

        item.name = name
        item.standard_charge = standard_charge_float
        item.category_id = int(category_id)
        item.is_active = is_active
        db.session.commit()
        flash('Ambulance Charge Item updated successfully!', 'success')
    except ValueError:
        db.session.rollback()
        flash('Invalid format for Standard Charge.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating Ambulance Charge Item: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


@admin.route(AMBULANCE_ITEM_DELETE + '/<int:id>', methods=['POST'], endpoint='delete-ambulance-item')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_ambulance_charge_item(id):
    item = AmbulanceChargeItem.query.get_or_404(id)
    try:
        # In a real application, you might add checks here if this charge item
        # is referenced in any completed ambulance calls or billing records.
        item.is_deleted = True
        item.deleted_at = datetime.utcnow()
        item.is_active = False  # Deactivate when deleting
        db.session.commit()
        flash('Ambulance Charge Item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting Ambulance Charge Item: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


@admin.route(AMBULANCE_ITEM_RESTORE + '/<int:id>', methods=['POST'], endpoint='restore-ambulance-item')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_ambulance_charge_item(id):
    item = AmbulanceChargeItem.query.get_or_404(id)
    try:
        item.is_deleted = False
        item.deleted_at = None
        item.is_active = True  # Activate when restoring
        db.session.commit()
        flash('Ambulance Charge Item restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring Ambulance Charge Item: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


@admin.route(AMBULANCE_ITEM_TOGGLE_STATUS + '/<int:id>', methods=['POST'], endpoint='toggle-ambulance-item-status')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def toggle_ambulance_charge_item_status(id):
    item = AmbulanceChargeItem.query.get_or_404(id)
    try:
        item.is_active = not item.is_active
        db.session.commit()
        status_msg = "activated" if item.is_active else "deactivated"
        flash(f'Ambulance Charge Item {status_msg} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling Ambulance Charge Item status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


@admin.route(AJAX_GET_AMBULANCE_ITEM_DETAILS + '/<int:id>', methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def get_ambulance_charge_item_details(id):
    item = AmbulanceChargeItem.query.get_or_404(id)
    return jsonify({
        'id': item.id,
        'name': item.name,
        'standard_charge': item.standard_charge,
        'category_id': item.category_id,
        'is_active': item.is_active
    })


@admin.route(AJAX_CHECK_AMBULANCE_ITEM_NAME, methods=['POST'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def check_ambulance_charge_item_name():
    name = request.form.get('name', '').strip()
    exclude_id = request.form.get('exclude_id')
    category_id = request.form.get('category_id')  # Essential for uniqueness within category

    query = AmbulanceChargeItem.query.filter(
        AmbulanceChargeItem.name.ilike(name),
        AmbulanceChargeItem.is_deleted == False
    )

    if category_id:  # Name should be unique within a category
        query = query.filter_by(category_id=int(category_id))

    if exclude_id:
        query = query.filter(AmbulanceChargeItem.id != int(exclude_id))

    exists = query.first() is not None
    return jsonify({'exists': exists})


# --- Export Ambulance Charge Items ---
@admin.route(AMBULANCE_ITEM_EXPORT + '/<format>', methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def export_ambulance_charge_items(format):
    items = AmbulanceChargeItem.query.options(joinedload(AmbulanceChargeItem.category)).filter_by(
        is_deleted=False).order_by(
        AmbulanceChargeItem.name).all()

    data = []
    for item in items:
        data.append({
            'ID': item.id,
            'Name': item.name,
            'Standard Charge': item.standard_charge,
            'Category': item.category.name if item.category else 'N/A',  # Include category name
            'Is Active': 'Yes' if item.is_active else 'No',
            'Created At': item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Updated At': item.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ambulance_charge_items_export_{current_time}.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ambulance Charge Items')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ambulance_charge_items_export_{current_time}.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 8
        normal_style.leading = 9

        title_text = "Ambulance Charge Items Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        header_row = [Paragraph(col, styles['h3']) for col in df.columns.tolist()]
        pdf_data.append(header_row)

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = A4
        LEFT_MARGIN = 0.5 * inch
        RIGHT_MARGIN = 0.5 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns
        # Example for custom widths:
        # col_widths = [
        #     0.05 * AVAILABLE_WIDTH, # ID
        #     0.25 * AVAILABLE_WIDTH, # Name
        #     0.15 * AVAILABLE_WIDTH, # Standard Charge
        #     0.20 * AVAILABLE_WIDTH, # Category
        #     0.10 * AVAILABLE_WIDTH, # Is Active
        #     0.10 * AVAILABLE_WIDTH, # Created At
        #     0.10 * AVAILABLE_WIDTH, # Updated At
        # ]

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        table = Table(pdf_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ambulance_charge_items_export_{current_time}.pdf'
        )

    flash('Invalid export format. Please choose csv, excel, or pdf.', 'danger')
    return redirect(ADMIN + AMBULANCE_ITEM_LIST)


# --- Sample Excel File Structure for Ambulance Charge Items ---
SAMPLE_AMBULANCE_CHARGE_ITEMS_EXCEL_STRUCTURE = [
    {
        "Name": "Standard Emergency Response",
        "Standard Charge": 1500.00,
        "Category Name": "Emergency Response"
    },
    {
        "Name": "Oxygen Cylinder Supply",
        "Standard Charge": 250.00,
        "Category Name": "Medical Supplies"  # This category should exist in AmbulanceCategory
    },
    {
        "Name": "Paramedic Support (Per Hour)",
        "Standard Charge": 500.00,
        "Category Name": "Professional Services"
    }
]


# --- Download Sample Import File for Ambulance Charge Items ---
@admin.route(AMBULANCE_ITEM_IMPORT_SAMPLE, methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_ambulance_charge_items_import_file():
    df = pd.DataFrame(SAMPLE_AMBULANCE_CHARGE_ITEMS_EXCEL_STRUCTURE)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ambulance Items Data')

        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING AMBULANCE CHARGE ITEMS:",
            "",
            "1. Enter your item data in the 'Ambulance Items Data' sheet.",
            "2. Required columns: 'Name', 'Standard Charge', 'Category Name'.",
            "3. 'Name' should be unique within each 'Category Name'.",
            "4. 'Standard Charge' should be a numeric value.",
            "5. 'Category Name' must match an existing Ambulance Category. If not found, the item will be skipped with an error.",
            "6. Do not modify the column headers.",
            "7. Remove this instructions sheet before importing if you face issues (optional).",
            "8. Save the file as .xlsx format."
        ]
        for row_idx, line in enumerate(instructions):
            worksheet.write(row_idx, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_ambulance_charge_items.xlsx'
    )


# --- Import Ambulance Charge Items ---
@admin.route(AMBULANCE_ITEM_IMPORT, methods=['POST'], endpoint="import-ambulance-items")
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def import_ambulance_charge_items():
    if 'file' not in request.files:
        flash('No file selected for import.', 'danger')
        return redirect(ADMIN + AMBULANCE_ITEM_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(ADMIN + AMBULANCE_ITEM_LIST)

    if not allowed_file(file.filename):
        flash('Invalid file type. Only Excel (.xlsx, .xls) and CSV (.csv) files are allowed.', 'danger')
        return redirect(ADMIN + AMBULANCE_ITEM_LIST)

    try:
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            df = pd.read_csv(stream)
        else:  # Assume Excel
            df = pd.read_excel(file)

        # Normalize column names for robust matching
        df.columns = df.columns.str.lower().str.replace('[^a-z0-9]+', '', regex=True)

        column_map = {
            'name': 'name',
            'standardcharge': 'standard_charge',
            'categoryname': 'category_name',  # Custom column for import logic
        }
        df.rename(columns=column_map, inplace=True)

        required_columns = ['name', 'standard_charge', 'category_name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing one or more required columns: {", ".join(missing)}. Please check the template.', 'danger')
            return redirect(ADMIN + AMBULANCE_ITEM_LIST)

        success_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for row_idx, row_series in df.iterrows():
            row_data = row_series.to_dict()
            name_val = str(row_data.get('name', '')).strip()
            category_name_val = str(row_data.get('category_name', '')).strip()

            if not name_val or not category_name_val:
                errors.append(f"Row {row_idx + 2}: 'Name' or 'Category Name' is empty. Skipping row.")
                skipped_count += 1
                continue

            try:
                # Find Ambulance Category
                category = AmbulanceCategory.query.filter(
                    AmbulanceCategory.name.ilike(category_name_val),
                    AmbulanceCategory.is_deleted == False
                ).first()

                if not category:
                    errors.append(
                        f"Row {row_idx + 2}: Ambulance Category '{category_name_val}' not found. Skipping item '{name_val}'.")
                    skipped_count += 1
                    continue

                # Prepare standard_charge
                standard_charge_val = float(str(row_data.get('standard_charge')).strip())
                if standard_charge_val < 0:
                    errors.append(
                        f"Row {row_idx + 2}: 'Standard Charge' for '{name_val}' cannot be negative. Skipping.")
                    skipped_count += 1
                    continue

                # Find existing item (based on name AND category, assuming name is unique within category)
                item = AmbulanceChargeItem.query.filter(
                    AmbulanceChargeItem.name.ilike(name_val),
                    AmbulanceChargeItem.category_id == category.id,
                    AmbulanceChargeItem.is_deleted == False
                ).first()

                if item:
                    # Update existing item
                    item.standard_charge = standard_charge_val
                    # is_active, is_deleted usually managed via UI
                    db.session.add(item)
                    updated_count += 1
                else:
                    # Create new item
                    new_item = AmbulanceChargeItem(
                        name=name_val,
                        standard_charge=standard_charge_val,
                        category_id=category.id,
                        is_active=True,
                        is_deleted=False
                    )
                    db.session.add(new_item)
                    success_count += 1

                db.session.commit()
            except ValueError as ve:
                db.session.rollback()
                errors.append(f"Row {row_idx + 2}: Data conversion error for '{name_val}' - {str(ve)}")
                skipped_count += 1
            except Exception as e:
                db.session.rollback()
                errors.append(f"Row {row_idx + 2}: Error processing item '{name_val}' - {str(e)}")
                skipped_count += 1

        if success_count > 0 or updated_count > 0:
            flash(f'Import completed! Added: {success_count}, Updated: {updated_count}, Skipped: {skipped_count}.',
                  'success')
        else:
            flash(f'Import completed with no new or updated records. Skipped: {skipped_count}.', 'info')

        if errors:
            flash('Some rows had errors during import. Please review the messages below:', 'warning')
            for error_msg in errors:
                flash(error_msg, 'warning')

    except pd.errors.EmptyDataError:
        flash('The uploaded file is empty.', 'danger')
    except pd.errors.ParserError:
        flash('Could not parse the file. Please check its format.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred during import: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_ITEM_LIST)
