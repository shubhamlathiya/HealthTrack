# Categories Routes
import io
import traceback
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
from controllers.constant.adminPathConstant import ADMIN, PHARMACY_COMPANIES_ADD, PHARMACY_COMPANIES_EDIT, \
    PHARMACY_COMPANIES_DELETE, PHARMACY_COMPANIES_RESTORE, PHARMACY_COMPANIES_IMPORT_SAMPLE, PHARMACY_COMPANIES_EXPORT, \
    PHARMACY_COMPANIES_IMPORT, PHARMACY_COMPANIES_LIST
from middleware.auth_middleware import token_required
from models.medicineModel import MedicineCompany
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


# Companies Routes
@admin.route(PHARMACY_COMPANIES_LIST, methods=['GET'], endpoint='medicine-companies')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def medicine_companies(current_user):
    companies = MedicineCompany.query.filter_by(is_deleted=0).order_by(MedicineCompany.name).all()
    archived_companies = MedicineCompany.query.filter_by(is_deleted=1).order_by(MedicineCompany.deleted_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_companies.html', companies=companies,
                           archived_companies=archived_companies,
                           ADMIN=ADMIN,
                           PHARMACY_COMPANIES_ADD=PHARMACY_COMPANIES_ADD,
                           PHARMACY_COMPANIES_EDIT=PHARMACY_COMPANIES_EDIT,
                           PHARMACY_COMPANIES_DELETE=PHARMACY_COMPANIES_DELETE,
                           PHARMACY_COMPANIES_RESTORE=PHARMACY_COMPANIES_RESTORE,
                           PHARMACY_COMPANIES_IMPORT_SAMPLE=PHARMACY_COMPANIES_IMPORT_SAMPLE,
                           PHARMACY_COMPANIES_EXPORT=PHARMACY_COMPANIES_EXPORT,
                           PHARMACY_COMPANIES_IMPORT=PHARMACY_COMPANIES_IMPORT
                           )


@admin.route(PHARMACY_COMPANIES_ADD, methods=['POST'], endpoint='medicine-companies/add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_medicine_company(current_user):
    try:
        company_name = request.form.get('name')

        existing_company = MedicineCompany.query.filter(
            MedicineCompany.name == company_name,
            MedicineCompany.is_deleted == False  # Only check against active companies
        ).first()

        if existing_company:
            flash(f'Medicine company "{company_name}" already exists.', 'warning')
            # Redirect back to the companies list or the add form
            return redirect(ADMIN + PHARMACY_COMPANIES_LIST)

        # If the company does not exist, proceed to add
        company = MedicineCompany(
            name=company_name,
            address=request.form.get('address'),
            contact_number=request.form.get('contact_number'),
            email=request.form.get('email'),
            website=request.form.get('website')
        )
        db.session.add(company)
        db.session.commit()
        flash('Company added successfully!', 'success')
    except Exception as e:
        db.session.rollback()  # Rollback changes if any error occurs

        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'Error adding company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)


@admin.route(PHARMACY_COMPANIES_EDIT + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.name = request.form.get('name')
        company.address = request.form.get('address')
        company.contact_number = request.form.get('contact_number')
        company.email = request.form.get('email')
        company.website = request.form.get('website')
        db.session.commit()
        flash('Company updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)


@admin.route(PHARMACY_COMPANIES_DELETE + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/delete')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.is_deleted = True
        company.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Company deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)


@admin.route(PHARMACY_COMPANIES_RESTORE + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.is_deleted = False
        company.deleted_at = None

        db.session.commit()
        flash('Category restored successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)


@admin.route(PHARMACY_COMPANIES_EXPORT + '/<format>', methods=['GET'], endpoint="export_companies")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_companies(current_user, format):
    companies = MedicineCompany.query.filter_by(deleted_at=None).all()

    # Prepare data for export
    data = []
    for company in companies:
        data.append({
            'Name': company.name,
            'Contact Number': company.contact_number or '',
            'Email': company.email or '',
            'Website': company.website or '',
            'Address': company.address or '',
            'Medicines Count': len(company.medicines),
            'Created At': company.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated At': company.updated_at.strftime('%Y-%m-%d %H:%M')
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
            download_name='medicine_companies.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='medicine_companies')
            # No need for writer.save()
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='medicine_companies.xlsx'
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
        title_text = "Medicine Companies Report"
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

        # Define standard page margins for the document
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = letter[0] - LEFT_MARGIN - RIGHT_MARGIN  # letter[0] is the width of the letter page

        # Calculate estimated column widths based on longest content and a factor for wrapping
        col_widths = []
        min_col_width_per_column = 1.0 * inch  # Minimum width for any column to be legible
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
        # we need to proportionally scale them down.
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
            download_name='medicine_companies.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)


# Download sample import file
@admin.route(PHARMACY_COMPANIES_IMPORT_SAMPLE, methods=['GET'], endpoint="download_sample_import_companies")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_import_companies(current_user):
    sample_data = [
        {
            "Name": "ABC Pharmaceuticals",
            "Contact Number": "+1234567890",
            "Email": "contact@abcpharma.com",
            "Website": "https://abcpharma.com",
            "Address": "123 Pharma Street, Medical City"
        },
        {
            "Name": "XYZ Meds",
            "Contact Number": "+9876543210",
            "Email": "info@xyzmeds.com",
            "Website": "https://xyzmeds.com",
            "Address": "456 Health Avenue, Medicine Town"
        }
    ]

    df = pd.DataFrame(sample_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Companies')
        # Add instructions
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING COMPANIES:",
            "",
            "1. Use the 'Companies' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: 'Contact Number', 'Email', 'Website', 'Address'",
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
        download_name='sample_import_companies.xlsx'
    )


# Import companies
@admin.route(PHARMACY_COMPANIES_IMPORT, methods=['POST'], endpoint="import_companies")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_companies(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_COMPANIES_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + PHARMACY_COMPANIES_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + PHARMACY_COMPANIES_LIST)

    try:
        # Read the Excel file
        df = pd.read_excel(file)

        # Validate columns
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + PHARMACY_COMPANIES_LIST)

        # Process each row
        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                contact = row.get('Contact Number', '')
                email = row.get('Email', '')
                website = row.get('Website', '')
                address = row.get('Address', '')

                if not name or pd.isna(name):
                    error_count += 1
                    continue

                # Check if company exists
                existing = MedicineCompany.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        existing.contact_number = contact if not pd.isna(contact) else None
                        existing.email = email if not pd.isna(email) else None
                        existing.website = website if not pd.isna(website) else None
                        existing.address = address if not pd.isna(address) else None
                        db.session.commit()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Create new company
                    new_company = MedicineCompany(
                        name=name,
                        contact_number=contact if not pd.isna(contact) else None,
                        email=email if not pd.isna(email) else None,
                        website=website if not pd.isna(website) else None,
                        address=address if not pd.isna(address) else None
                    )
                    db.session.add(new_company)
                    db.session.commit()
                    success_count += 1

            except Exception as e:
                error_count += 1
                continue

        flash(f'Import completed: {success_count} successful, {error_count} failed',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(ADMIN + PHARMACY_COMPANIES_LIST)
