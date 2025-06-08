# Supplier Routes
import io
from datetime import datetime

import pandas as pd
from flask import render_template, request, flash, redirect, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, PHARMACY_SUPPLIERS_LIST, PHARMACY_SUPPLIERS_ADD, \
    PHARMACY_SUPPLIERS_EDIT, PHARMACY_SUPPLIERS_DELETE, PHARMACY_SUPPLIERS_RESTORE, PHARMACY_SUPPLIERS_IMPORT, \
    PHARMACY_SUPPLIERS_EXPORT, PHARMACY_SUPPLIERS_IMPORT_SAMPLE
from middleware.auth_middleware import token_required
from models.medicineModel import Supplier
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(PHARMACY_SUPPLIERS_LIST, methods=['GET'], endpoint='suppliers')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def suppliers(current_user):
    active_suppliers = Supplier.query.filter_by(is_deleted=0).order_by(Supplier.name).all()
    archived_suppliers = Supplier.query.filter_by(is_deleted=1).order_by(Supplier.deleted_at.desc()).all()
    return render_template('admin_templates/pharmacy/supplier.html',
                           suppliers=active_suppliers,
                           archived_suppliers=archived_suppliers,
                           ADMIN=ADMIN,
                           SUPPLIERS_ADD=PHARMACY_SUPPLIERS_ADD,
                           SUPPLIERS_EDIT=PHARMACY_SUPPLIERS_EDIT,
                           SUPPLIERS_DELETE=PHARMACY_SUPPLIERS_DELETE,
                           SUPPLIERS_RESTORE=PHARMACY_SUPPLIERS_RESTORE,
                           SUPPLIERS_IMPORT=PHARMACY_SUPPLIERS_IMPORT,
                           SUPPLIERS_EXPORT=PHARMACY_SUPPLIERS_EXPORT,
                           SUPPLIERS_SAMPLE_IMPORT=PHARMACY_SUPPLIERS_IMPORT_SAMPLE)


@admin.route(PHARMACY_SUPPLIERS_ADD, methods=['POST'], endpoint='suppliers/add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_supplier(current_user):
    try:
        supplier_name = request.form.get('name')

        existing_supplier = Supplier.query.filter(
            Supplier.name == supplier_name,
            Supplier.is_deleted == False  # Check for active, non-deleted suppliers
        ).first()

        if existing_supplier:
            flash(f'Supplier with name "{supplier_name}" already exists.', 'warning')
            return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)  # Redirect back to the suppliers list or add form

        # If supplier does not exist, proceed to add
        supplier = Supplier(
            name=supplier_name,
            contact_person=request.form.get('contact_person'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            tax_id=request.form.get('tax_id'),
            payment_terms=request.form.get('payment_terms')

        )
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Rollback changes if any error occurs during add
        import traceback
        traceback.print_exc()  # For debugging: print full traceback to console
        flash(f'Error adding supplier: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)


@admin.route(PHARMACY_SUPPLIERS_EDIT + '/<int:id>', methods=['POST'], endpoint='suppliers/<int:id>/edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_supplier(current_user, id):
    supplier = Supplier.query.get_or_404(id)
    try:
        supplier.name = request.form.get('name')
        supplier.contact_person = request.form.get('contact_person')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.address = request.form.get('address')
        supplier.tax_id = request.form.get('tax_id')
        supplier.payment_terms = request.form.get('payment_terms')
        db.session.commit()
        flash('Supplier updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating supplier: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)


@admin.route(PHARMACY_SUPPLIERS_DELETE + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_supplier(current_user, id):
    supplier = Supplier.query.get_or_404(id)
    try:
        supplier.is_deleted = True
        supplier.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Supplier deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)


@admin.route(PHARMACY_SUPPLIERS_RESTORE + '/<int:id>', methods=['POST'], endpoint='suppliers/<int:id>/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_supplier(current_user, id):
    supplier = Supplier.query.get_or_404(id)
    try:
        supplier.is_deleted = False
        supplier.deleted_at = None
        db.session.commit()
        flash('Supplier restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring supplier: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)


# Export suppliers
@admin.route(PHARMACY_SUPPLIERS_EXPORT + '/<format>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_suppliers(current_user, format):
    suppliers = Supplier.query.filter_by(is_deleted=0).all()

    # Prepare data for export
    data = []
    for supplier in suppliers:
        data.append({
            'Name': supplier.name,
            'Contact Person': supplier.contact_person,
            'Phone': supplier.phone,
            'Email': supplier.email,
            'Address': supplier.address,
            'Tax ID': supplier.tax_id,
            'Payment Terms': supplier.payment_terms,
            'Created At': supplier.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated At': supplier.updated_at.strftime('%Y-%m-%d %H:%M')
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
            download_name='suppliers.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Suppliers')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='suppliers.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()

        styles = getSampleStyleSheet()

        # Define a normal style for table content that allows wrapping
        normal_style = styles['Normal']
        normal_style.fontName = "Helvetica"
        normal_style.fontSize = 9
        normal_style.leading = 10  # Line spacing for wrapped text

        # Define a bold style for table headers
        header_style = styles['h3']
        header_style.fontName = "Helvetica-Bold"
        header_style.fontSize = 10

        # Title setup
        title_text = "Suppliers Report"
        title = Paragraph(title_text, styles['Title'])

        # --- Prepare PDF data with Paragraph objects for wrapping ---
        pdf_data = []
        # Add header row, ensuring headers are also Paragraphs for consistency in styling and potential wrapping
        pdf_data.append([Paragraph(col, header_style) for col in df.columns.tolist()])

        # Add data rows, wrapping all cell content in Paragraphs
        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        # --- Calculate Column Widths for Wrapping ---
        # Define standard page margins for the document
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = letter[0] - LEFT_MARGIN - RIGHT_MARGIN  # letter[0] is the width of the letter page

        # Calculate estimated column widths based on longest content and a factor for wrapping
        col_widths = []
        min_col_width_per_column = 0.8 * inch  # Minimum width for any column to be legible
        padding_per_side = 0.1 * inch  # Small internal padding for cells

        for col_idx in range(len(df.columns)):
            # Calculate max width of string in this column for initial estimation
            max_content_width_in_points = 0
            for row in pdf_data:
                # Get the text content from the Paragraph object and measure its raw width
                if isinstance(row[col_idx], Paragraph):
                    text_to_measure = row[col_idx].text
                else:
                    text_to_measure = str(row[col_idx])  # Fallback for non-Paragraphs (though all should be now)

                # Use stringWidth for precise text width calculation
                width = stringWidth(text_to_measure, normal_style.fontName, normal_style.fontSize)
                if width > max_content_width_in_points:
                    max_content_width_in_points = width

            # Add padding to the estimated content width
            estimated_col_width = max_content_width_in_points + (2 * padding_per_side)

            # Ensure it meets a minimum width for very short content or empty cells
            estimated_col_width = max(estimated_col_width, min_col_width_per_column)
            col_widths.append(estimated_col_width)

        # If the sum of estimated column widths exceeds available page width,
        # proportionally scale them down to fit.
        total_estimated_width = sum(col_widths)
        if total_estimated_width > AVAILABLE_WIDTH:
            scaling_factor = AVAILABLE_WIDTH / total_estimated_width
            col_widths = [w * scaling_factor for w in col_widths]

        # --- Build the document ---
        # Use SimpleDocTemplate with standard page size for content flow
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
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),  # Light grey for data rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Finer grid lines
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            # Note: FONTNAME/FONTSIZE for data rows are controlled by Paragraph's normal_style
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='suppliers.pdf'
        )

    flash('Invalid export format', 'error')
    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)


# Sample Excel file structure for import
SAMPLE_SUPPLIER_STRUCTURE = [
    {
        "Name": "ABC Pharmaceuticals",
        "Contact Person": "John Doe",
        "Phone": "1234567890",
        "Email": "john@abc.com",
        "Address": "123 Pharma St, City",
        "Tax ID": "TAX12345",
        "Payment Terms": "Net 30"
    },
    {
        "Name": "XYZ Medical Supplies",
        "Contact Person": "Jane Smith",
        "Phone": "9876543210",
        "Email": "jane@xyz.com",
        "Address": "456 Medical Ave, Town",
        "Tax ID": "TAX67890",
        "Payment Terms": "Net 45"
    }
]


# Download sample import file
@admin.route(PHARMACY_SUPPLIERS_IMPORT_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_supplier_file(current_user):
    df = pd.DataFrame(SAMPLE_SUPPLIER_STRUCTURE)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Suppliers')
        # Add instructions
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING SUPPLIERS:",
            "",
            "1. Use the 'Suppliers' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: 'Contact Person', 'Phone', 'Email', 'Address', 'Tax ID', 'Payment Terms'",
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
        download_name='sample_import_suppliers.xlsx'
    )


# Import suppliers
@admin.route(PHARMACY_SUPPLIERS_IMPORT, methods=['POST'], endpoint="import_suppliers")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_suppliers(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Validate columns
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)

        # Process each row
        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                contact_person = row.get('Contact Person')
                phone = row.get('Phone')
                email = row.get('Email')
                address = row.get('Address')
                tax_id = row.get('Tax ID')
                payment_terms = row.get('Payment Terms')

                if not name or pd.isna(name):
                    error_count += 1
                    continue

                # Check if supplier exists
                existing = Supplier.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        existing.contact_person = contact_person
                        existing.phone = phone
                        existing.email = email
                        existing.address = address
                        existing.tax_id = tax_id
                        existing.payment_terms = payment_terms
                        db.session.commit()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Create new supplier
                    new_supplier = Supplier(
                        name=name,
                        contact_person=contact_person,
                        phone=phone,
                        email=email,
                        address=address,
                        tax_id=tax_id,
                        payment_terms=payment_terms
                    )
                    db.session.add(new_supplier)
                    db.session.commit()
                    success_count += 1

            except Exception as e:
                error_count += 1
                continue

        flash(f'Import completed: {success_count} successful, {error_count} failed',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(ADMIN + PHARMACY_SUPPLIERS_LIST)
