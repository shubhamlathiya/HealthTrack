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
from controllers.constant.adminPathConstant import ADMIN, AMBULANCE_CATEGORY_LIST, AMBULANCE_CATEGORY_ADD, \
    AMBULANCE_CATEGORY_EDIT, AMBULANCE_CATEGORY_DELETE, AMBULANCE_CATEGORY_RESTORE, AMBULANCE_CATEGORY_TOGGLE_STATUS, \
    AMBULANCE_CATEGORY_EXPORT, AMBULANCE_CATEGORY_IMPORT, AMBULANCE_CATEGORY_IMPORT_SAMPLE, \
    AJAX_GET_AMBULANCE_CATEGORY_DETAILS, AJAX_CHECK_AMBULANCE_CATEGORY_NAME
from middleware.auth_middleware import token_required
from models import UserRole
from models.ambulanceModel import AmbulanceCategory, AmbulanceChargeItem, Ambulance
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(AMBULANCE_CATEGORY_LIST, methods=['GET'], endpoint='ambulance-category-list')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def ambulance_category_list(current_use):
    # Assuming AmbulanceCategory is your model for ambulance categories
    categories = AmbulanceCategory.query.filter_by(is_deleted=0).order_by(AmbulanceCategory.name).all()
    archived_categories = AmbulanceCategory.query.filter_by(is_deleted=1).order_by(AmbulanceCategory.name).all()

    return render_template("admin_templates/ambulance/ambulance_category_list.html",
                           categories=categories,
                           archived_categories=archived_categories,
                           ADMIN=ADMIN,  # Assuming ADMIN is a base path
                           AMBULANCE_CATEGORY_ADD=AMBULANCE_CATEGORY_ADD,
                           AMBULANCE_CATEGORY_EDIT=AMBULANCE_CATEGORY_EDIT,
                           AMBULANCE_CATEGORY_DELETE=AMBULANCE_CATEGORY_DELETE,
                           AMBULANCE_CATEGORY_RESTORE=AMBULANCE_CATEGORY_RESTORE,
                           AMBULANCE_CATEGORY_TOGGLE_STATUS=AMBULANCE_CATEGORY_TOGGLE_STATUS,
                           AMBULANCE_CATEGORY_EXPORT=AMBULANCE_CATEGORY_EXPORT,
                           AMBULANCE_CATEGORY_IMPORT=AMBULANCE_CATEGORY_IMPORT,
                           AMBULANCE_CATEGORY_IMPORT_SAMPLE=AMBULANCE_CATEGORY_IMPORT_SAMPLE,
                           )


@admin.route(AMBULANCE_CATEGORY_ADD, methods=['POST'], endpoint='add-ambulance-category')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def add_ambulance_category():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Ambulance Category Name is required.', 'danger')
        return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

    try:
        # Check for duplicate name (case-insensitive, for non-deleted categories)
        if AmbulanceCategory.query.filter(AmbulanceCategory.name.ilike(name),
                                          AmbulanceCategory.is_deleted == False).first():
            flash('Ambulance category with this name already exists.', 'danger')
            return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

        new_category = AmbulanceCategory(
            name=name,
            description=description,
            is_active=True  # New categories are active by default
        )
        db.session.add(new_category)
        db.session.commit()
        flash('Ambulance category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding ambulance category: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


@admin.route(AMBULANCE_CATEGORY_EDIT + '/<int:id>', methods=['POST'], endpoint='edit-ambulance-category')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_ambulance_category(id):
    category = AmbulanceCategory.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_active = request.form.get('is_active', 'off') == 'on'

    if not name:
        flash('Ambulance Category Name is required.', 'danger')
        return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

    try:
        # Check for duplicate name (excluding current category and non-deleted ones)
        existing = AmbulanceCategory.query.filter(
            AmbulanceCategory.name.ilike(name),
            AmbulanceCategory.id != id,
            AmbulanceCategory.is_deleted == False
        ).first()

        if existing:
            flash('Another ambulance category with this name already exists.', 'danger')
            return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

        category.name = name
        category.description = description
        category.is_active = is_active
        db.session.commit()
        flash('Ambulance category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating ambulance category: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


@admin.route(AMBULANCE_CATEGORY_DELETE + '/<int:id>', methods=['POST'], endpoint='delete-ambulance-category')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_ambulance_category(id):
    category = AmbulanceCategory.query.get_or_404(id)
    try:
        # Check if category has associated active ambulances
        # Assuming your Ambulance model has a 'category_id' foreign key and 'is_deleted' field
        active_ambulances = Ambulance.query.filter_by(is_deleted=False).first()
        if active_ambulances:
            flash(f'Cannot delete category "{category.name}" because it has active ambulances associated with it.',
                  'danger')
            return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        category.is_active = False  # Deactivate when deleting
        db.session.commit()
        flash('Ambulance category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ambulance category: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


@admin.route(AMBULANCE_CATEGORY_RESTORE + '/<int:id>', methods=['POST'], endpoint='restore-ambulance-category')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_ambulance_category(id):
    category = AmbulanceCategory.query.get_or_404(id)
    try:
        category.is_deleted = False
        category.deleted_at = None
        category.is_active = True  # Activate when restoring
        db.session.commit()
        flash('Ambulance category restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring ambulance category: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


@admin.route(AMBULANCE_CATEGORY_TOGGLE_STATUS + '/<int:id>', methods=['POST'],
             endpoint='toggle-ambulance-category-status')
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def toggle_ambulance_category_status(id):
    category = AmbulanceCategory.query.get_or_404(id)
    try:
        category.is_active = not category.is_active
        db.session.commit()
        status_msg = "activated" if category.is_active else "deactivated"
        flash(f'Ambulance category {status_msg} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling ambulance category status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


@admin.route(AJAX_GET_AMBULANCE_CATEGORY_DETAILS + '/<int:id>', methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def get_ambulance_category_details(id):
    category = AmbulanceCategory.query.get_or_404(id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'is_active': category.is_active
    })


@admin.route(AJAX_CHECK_AMBULANCE_CATEGORY_NAME, methods=['POST'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def check_ambulance_category_name():
    name = request.form.get('name', '').strip()
    exclude_id = request.form.get('exclude_id')

    query = AmbulanceCategory.query.filter(AmbulanceCategory.name.ilike(name), AmbulanceCategory.is_deleted == False)
    if exclude_id:
        query = query.filter(AmbulanceCategory.id != int(exclude_id))

    exists = query.first() is not None
    return jsonify({'exists': exists})


# --- Export Ambulance Categories ---
@admin.route(AMBULANCE_CATEGORY_EXPORT + '/<format>', methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def export_ambulance_categories(format):
    categories = AmbulanceCategory.query.filter_by(is_deleted=False).order_by(AmbulanceCategory.name).all()

    data = []
    for category in categories:
        data.append({
            'ID': category.id,
            'Name': category.name,
            'Description': category.description if category.description else '',
            'Is Active': 'Yes' if category.is_active else 'No',
            'Created At': category.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Updated At': category.updated_at.strftime('%Y-%m-%d %H:%M:%S')
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
            download_name=f'ambulance_categories_export_{current_time}.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ambulance Categories')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ambulance_categories_export_{current_time}.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        title_text = "Ambulance Categories Report"
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
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        table = Table(pdf_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
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
            download_name=f'ambulance_categories_export_{current_time}.pdf'
        )

    flash('Invalid export format. Please choose csv, excel, or pdf.', 'danger')
    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)


# --- Sample Excel File Structure for Ambulance Categories ---
SAMPLE_AMBULANCE_CATEGORIES_EXCEL_STRUCTURE = [
    {
        "Name": "Private Ambulance",
        "Description": "Ambulances for private use or non-emergency transfers"
    },
    {
        "Name": "Emergency Response",
        "Description": "Ambulances designated for emergency and critical care"
    },
    {
        "Name": "Patient Transport",
        "Description": "Ambulances primarily for non-emergency patient transfers between facilities"
    }
]


# --- Download Sample Import File for Ambulance Categories ---
@admin.route(AMBULANCE_CATEGORY_IMPORT_SAMPLE, methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_ambulance_categories_import_file():
    df = pd.DataFrame(SAMPLE_AMBULANCE_CATEGORIES_EXCEL_STRUCTURE)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ambulance Categories Data')

        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING AMBULANCE CATEGORIES:",
            "",
            "1. Enter your category data in the 'Ambulance Categories Data' sheet.",
            "2. Required columns: 'Name'.",
            "3. Optional columns: 'Description'.",
            "4. 'Name' is used to identify existing categories for updates. Case-insensitive.",
            "5. Do not modify the column headers.",
            "6. Remove this instructions sheet before importing if you face issues (optional).",
            "7. Save the file as .xlsx format."
        ]
        for row_idx, line in enumerate(instructions):
            worksheet.write(row_idx, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_ambulance_categories.xlsx'
    )


# --- Import Ambulance Categories ---
@admin.route(AMBULANCE_CATEGORY_IMPORT, methods=['POST'], endpoint="import-ambulance-categories")
# @token_required(allowed_roles=[UserRole.ADMIN.name])
def import_ambulance_categories():
    if 'file' not in request.files:
        flash('No file selected for import.', 'danger')
        return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

    if not allowed_file(file.filename):
        flash('Invalid file type. Only Excel (.xlsx, .xls) and CSV (.csv) files are allowed.', 'danger')
        return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

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
            'description': 'description',
        }
        df.rename(columns=column_map, inplace=True)

        required_columns = ['name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing one or more required columns: {", ".join(missing)}. Please check the template.', 'danger')
            return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)

        success_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for row_idx, row_series in df.iterrows():
            row_data = row_series.to_dict()
            name_val = str(row_data.get('name', '')).strip()

            if not name_val:
                errors.append(f"Row {row_idx + 2}: 'Name' is empty. Skipping row.")
                skipped_count += 1
                continue

            try:
                # Check for existing category by name (case-insensitive, non-deleted)
                category = AmbulanceCategory.query.filter(
                    AmbulanceCategory.name.ilike(name_val),
                    AmbulanceCategory.is_deleted == False
                ).first()

                description_val = str(row_data.get('description', '')).strip() if pd.notna(
                    row_data.get('description')) else None

                if category:
                    # Update existing category
                    category.description = description_val
                    # is_active, is_deleted usually managed via UI
                    db.session.add(category)
                    updated_count += 1
                else:
                    # Create new category
                    new_category = AmbulanceCategory(
                        name=name_val,
                        description=description_val,
                        is_active=True,
                        is_deleted=False
                    )
                    db.session.add(new_category)
                    success_count += 1

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                errors.append(f"Row {row_idx + 2}: Error processing category '{name_val}' - {str(e)}")
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

    return redirect(ADMIN + AMBULANCE_CATEGORY_LIST)
