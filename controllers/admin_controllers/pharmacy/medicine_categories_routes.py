# Categories Routes
import io
from datetime import datetime

import pandas as pd
from flask import render_template, request, flash, redirect, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, PHARMACY_CATEGORIES, PHARMACY_CATEGORIES_ADD, \
    PHARMACY_CATEGORIES_EDIT, PHARMACY_CATEGORIES_DELETE, PHARMACY_CATEGORIES_RESTORE, PHARMACY_CATEGORIES_EXPORT, \
    PHARMACY_CATEGORIES_IMPORT, PHARMACY_CATEGORIES_IMPORT_SAMPLE
from middleware.auth_middleware import token_required
from models.medicineModel import MedicineCategory
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(PHARMACY_CATEGORIES, methods=['GET'], endpoint='medicine-categories')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def medicine_categories(current_user):
    categories = MedicineCategory.query.filter_by(is_deleted=0).order_by(MedicineCategory.name).all()
    archived_categories = MedicineCategory.query.filter_by(is_deleted=1).order_by(
        MedicineCategory.deleted_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_categories.html', categories=categories,
                           archived_categories=archived_categories,
                           ADMIN=ADMIN,
                           PHARMACY_CATEGORIES_ADD=PHARMACY_CATEGORIES_ADD,
                           PHARMACY_CATEGORIES_EDIT=PHARMACY_CATEGORIES_EDIT,
                           PHARMACY_CATEGORIES_DELETE=PHARMACY_CATEGORIES_DELETE,
                           PHARMACY_CATEGORIES_RESTORE=PHARMACY_CATEGORIES_RESTORE,
                           PHARMACY_CATEGORIES_EXPORT=PHARMACY_CATEGORIES_EXPORT,
                           PHARMACY_CATEGORIES_IMPORT=PHARMACY_CATEGORIES_IMPORT,
                           PHARMACY_CATEGORIES_IMPORT_SAMPLE=PHARMACY_CATEGORIES_IMPORT_SAMPLE)


@admin.route(PHARMACY_CATEGORIES_ADD, methods=['POST'], endpoint='medicine-categories/add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_medicine_category(current_user):
    try:
        category_name = request.form.get('name')
        category_description = request.form.get('description')

        # Check if a category with this name already exists
        # We also check if it's not soft-deleted, assuming 'is_deleted' is a column.
        existing_category = MedicineCategory.query.filter(
            MedicineCategory.name == category_name,
            MedicineCategory.is_deleted == False
        ).first()

        if existing_category:
            flash(f'Medicine category "{category_name}" already exists.', 'warning')
            return redirect(ADMIN + PHARMACY_CATEGORIES)  # Redirect back to the categories list or add form

        # If category does not exist, proceed to add
        category = MedicineCategory(
            name=category_name,
            description=category_description
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Rollback changes if any error occurs
        import traceback
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'Error adding category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_CATEGORIES)


@admin.route(PHARMACY_CATEGORIES_EDIT + '/<int:id>', methods=['POST'],
             endpoint='medicine-categories/<int:id>/edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_CATEGORIES)


@admin.route(PHARMACY_CATEGORIES_DELETE + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_CATEGORIES)


@admin.route(PHARMACY_CATEGORIES_RESTORE + '/<int:id>', methods=['POST'],
             endpoint='medicine-categories/<int:id>/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.is_deleted = False
        category.deleted_at = None
        db.session.commit()
        flash('Category restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_CATEGORIES)


# Export categories
@admin.route(PHARMACY_CATEGORIES_EXPORT + '/<format>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_categories(current_user, format):
    categories = MedicineCategory.query.filter_by(deleted_at=None).all()

    # Prepare data for export
    data = []
    for category in categories:
        data.append({
            'Name': category.name,
            'Description': category.description,
            'Medicines Count': len(category.medicines),
            'Created At': category.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated At': category.updated_at.strftime('%Y-%m-%d %H:%M')
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
            download_name='medicine_categories.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Categories')
            # No need for writer.save()
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='medicine_categories.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()

        styles = getSampleStyleSheet()

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10  # Line spacing

        title_text = "Medicine Categories Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        # Add header row
        pdf_data.append(
            [Paragraph(col, styles['h3']) for col in df.columns.tolist()])  # Use h3 or similar for header bolding

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                # Wrap all cell content in a Paragraph object using our defined normal_style
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter  # Start with a standard page size for overall dimensions
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)

        col_widths = []
        if 'Category Name' in df.columns and 'Description' in df.columns:
            col_widths.append(0.3 * AVAILABLE_WIDTH)  # For 'Category Name'
            col_widths.append(0.7 * AVAILABLE_WIDTH)  # For 'Description'
        else:
            # Fallback if column names are different or more columns
            col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        # Ensure col_widths list matches the number of columns in your data
        if len(col_widths) != num_columns:
            # Fallback to equal distribution if specific mapping fails
            col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Create table with calculated column widths
        table = Table(pdf_data, colWidths=col_widths)  # Pass the calculated column widths

        # Table Style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),  # Light grey for data rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Finer grid lines
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
            download_name='medicine_categories.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + PHARMACY_CATEGORIES)


# Sample Excel file structure for import
SAMPLE_EXCEL_STRUCTURE = [
    {
        "Name": "Antibiotics",
        "Description": "Medicines that fight bacterial infections"
    },
    {
        "Name": "Pain Relievers",
        "Description": "Medicines for pain management"
    }
]


# Download sample import file
@admin.route(PHARMACY_CATEGORIES_IMPORT_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_import_file(current_user):
    df = pd.DataFrame(SAMPLE_EXCEL_STRUCTURE)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Categories')
        # Add instructions
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING CATEGORIES:",
            "",
            "1. Use the 'Categories' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: 'Description'",
            "4. Do not modify the column headers",
            "5. Remove these instructions before importing",
            "6. Save the file as .xlsx format"
        ]

        for row, line in enumerate(instructions):
            worksheet.write(row, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_categories.xlsx'
    )


# Import categories
@admin.route(PHARMACY_CATEGORIES_IMPORT, methods=['POST'], endpoint="import_categories")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_categories(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_CATEGORIES)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_CATEGORIES)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + PHARMACY_CATEGORIES)

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Validate columns
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + PHARMACY_CATEGORIES)

        # Process each row
        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                description = row.get('Description', '')

                if not name or pd.isna(name):
                    error_count += 1
                    continue

                # Check if category exists
                existing = MedicineCategory.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        existing.description = description
                        db.session.commit()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Create new category
                    new_category = MedicineCategory(
                        name=name,
                        description=description
                    )
                    db.session.add(new_category)
                    db.session.commit()
                    success_count += 1

            except Exception as e:
                error_count += 1
                continue

        flash(f'Import completed: {success_count} successful, {error_count} failed',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(ADMIN + PHARMACY_CATEGORIES)
