import io
import traceback
from datetime import datetime

import pandas as pd
from flask import render_template, request, flash, redirect, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
# Assuming you have constants for ItemSupplier paths. Adjust if names are different.
from controllers.constant.adminPathConstant import ADMIN, ITEM_SUPPLIERS_ADD, \
    ITEM_SUPPLIERS_EDIT, ITEM_SUPPLIERS_DELETE, ITEM_SUPPLIERS_RESTORE, ITEM_SUPPLIERS_EXPORT, \
    ITEM_SUPPLIERS_IMPORT, ITEM_SUPPLIERS_IMPORT_SAMPLE, ITEM_SUPPLIERS_LIST
from middleware.auth_middleware import token_required
from models.InventoryItemModel import ItemSupplier
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(ITEM_SUPPLIERS_LIST, methods=['GET'], endpoint='item-suppliers')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def item_suppliers(current_user):
    suppliers = ItemSupplier.query.filter_by(is_deleted=0).order_by(ItemSupplier.name).all()
    archived_suppliers = ItemSupplier.query.filter_by(is_deleted=1).order_by(
        ItemSupplier.deleted_at.desc()).all()
    return render_template('admin_templates/inventory/item_suppliers.html', suppliers=suppliers,
                           archived_suppliers=archived_suppliers,
                           ADMIN=ADMIN,
                           ITEM_SUPPLIERS_ADD=ITEM_SUPPLIERS_ADD,
                           ITEM_SUPPLIERS_EDIT=ITEM_SUPPLIERS_EDIT,
                           ITEM_SUPPLIERS_DELETE=ITEM_SUPPLIERS_DELETE,
                           ITEM_SUPPLIERS_RESTORE=ITEM_SUPPLIERS_RESTORE,
                           ITEM_SUPPLIERS_EXPORT=ITEM_SUPPLIERS_EXPORT,
                           ITEM_SUPPLIERS_IMPORT=ITEM_SUPPLIERS_IMPORT,
                           ITEM_SUPPLIERS_IMPORT_SAMPLE=ITEM_SUPPLIERS_IMPORT_SAMPLE)


@admin.route(ITEM_SUPPLIERS_ADD, methods=['POST'], endpoint='item-suppliers/add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_item_supplier(current_user):
    try:
        supplier_name = request.form.get('name')
        supplier_phone = request.form.get('phone')
        supplier_email = request.form.get('email')
        supplier_contact_person_name = request.form.get('contact_person_name')
        supplier_address = request.form.get('address')
        supplier_contact_person_phone = request.form.get('contact_person_phone')
        supplier_contact_person_email = request.form.get('contact_person_email')
        supplier_description = request.form.get('description')

        existing_supplier = ItemSupplier.query.filter(
            ItemSupplier.name == supplier_name,
            ItemSupplier.is_deleted == False
        ).first()

        if existing_supplier:
            flash(f'Item supplier "{supplier_name}" already exists.', 'warning')
            return redirect(ADMIN + ITEM_SUPPLIERS_LIST)

        supplier = ItemSupplier(
            name=supplier_name,
            phone=supplier_phone,
            email=supplier_email,
            contact_person_name=supplier_contact_person_name,
            address=supplier_address,
            contact_person_phone=supplier_contact_person_phone,
            contact_person_email=supplier_contact_person_email,
            description=supplier_description
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Item Supplier added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error adding item supplier: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)


@admin.route(ITEM_SUPPLIERS_EDIT + '/<int:id>', methods=['POST'],
             endpoint='item-suppliers/<int:id>/edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_item_supplier(current_user, id):
    supplier = ItemSupplier.query.get_or_404(id)
    try:
        supplier.name = request.form.get('name')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.contact_person_name = request.form.get('contact_person_name')
        supplier.address = request.form.get('address')
        supplier.contact_person_phone = request.form.get('contact_person_phone')
        supplier.contact_person_email = request.form.get('contact_person_email')
        supplier.description = request.form.get('description')
        db.session.commit()
        flash('Item Supplier updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating item supplier: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)


@admin.route(ITEM_SUPPLIERS_DELETE + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_item_supplier(current_user, id):
    supplier = ItemSupplier.query.get_or_404(id)
    try:
        supplier.is_deleted = True
        supplier.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Item Supplier deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item supplier: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)


@admin.route(ITEM_SUPPLIERS_RESTORE + '/<int:id>', methods=['POST'],
             endpoint='item-suppliers/<int:id>/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_item_supplier(current_user, id):
    supplier = ItemSupplier.query.get_or_404(id)
    try:
        supplier.is_deleted = False
        supplier.deleted_at = None
        db.session.commit()
        flash('Item Supplier restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring item supplier: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)


@admin.route(ITEM_SUPPLIERS_EXPORT + '/<format>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_item_suppliers(current_user, format):
    suppliers = ItemSupplier.query.filter_by(is_deleted=False).all()

    data = []
    for supplier in suppliers:
        data.append({
            'Name': supplier.name,
            'Phone': supplier.phone,
            'Email': supplier.email,
            'Contact Person Name': supplier.contact_person_name,
            'Address': supplier.address,
            'Contact Person Phone': supplier.contact_person_phone,
            'Contact Person Email': supplier.contact_person_email,
            'Description': supplier.description,
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
            download_name='item_suppliers.csv'
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
            download_name='item_suppliers.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        title_text = "Item Suppliers Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        pdf_data.append([Paragraph(col, styles['h3']) for col in df.columns.tolist()])

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        # Adjust AVAILABLE_WIDTH to accommodate more columns
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        # A more sophisticated way to distribute column widths might be needed for many columns
        num_columns = len(df.columns)
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns # Distribute evenly

        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        table = Table(pdf_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
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
            download_name='item_suppliers.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)


SAMPLE_ITEM_SUPPLIER_EXCEL_STRUCTURE = [
    {
        "Name": "Global Medical Supplies",
        "Phone": "123-456-7890",
        "Email": "info@globalmed.com",
        "Contact Person Name": "John Doe",
        "Address": "123 Health St, Medical City",
        "Contact Person Phone": "987-654-3210",
        "Contact Person Email": "john.doe@globalmed.com",
        "Description": "Supplier of various medical equipment and consumables"
    },
    {
        "Name": "Office Mart Inc.",
        "Phone": "900-800-7000",
        "Email": "sales@officemart.com",
        "Contact Person Name": "Jane Smith",
        "Address": "456 Office Rd, Business Park",
        "Contact Person Phone": "654-321-0987",
        "Contact Person Email": "jane.smith@officemart.com",
        "Description": "Supplier of office stationery and furniture"
    }
]


@admin.route(ITEM_SUPPLIERS_IMPORT_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_item_supplier_sample_import_file(current_user):
    df = pd.DataFrame(SAMPLE_ITEM_SUPPLIER_EXCEL_STRUCTURE)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Item Suppliers')
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING ITEM SUPPLIERS:",
            "",
            "1. Use the 'Item Suppliers' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: 'Phone', 'Email', 'Contact Person Name', 'Address', 'Contact Person Phone', 'Contact Person Email', 'Description'",
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
        download_name='sample_import_item_suppliers.xlsx'
    )


@admin.route(ITEM_SUPPLIERS_IMPORT, methods=['POST'], endpoint="import_item_suppliers")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_item_suppliers(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + ITEM_SUPPLIERS_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + ITEM_SUPPLIERS_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + ITEM_SUPPLIERS_LIST)

    try:
        df = pd.read_excel(file)
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + ITEM_SUPPLIERS_LIST)

        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                phone = row.get('Phone', None)
                email = row.get('Email', None)
                contact_person_name = row.get('Contact Person Name', None)
                address = row.get('Address', None)
                contact_person_phone = row.get('Contact Person Phone', None)
                contact_person_email = row.get('Contact Person Email', None)
                description = row.get('Description', None)

                if not name or pd.isna(name):
                    error_count += 1
                    continue

                existing = ItemSupplier.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        existing.phone = phone
                        existing.email = email
                        existing.contact_person_name = contact_person_name
                        existing.address = address
                        existing.contact_person_phone = contact_person_phone
                        existing.contact_person_email = contact_person_email
                        existing.description = description
                        db.session.commit()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    new_supplier = ItemSupplier(
                        name=name,
                        phone=phone,
                        email=email,
                        contact_person_name=contact_person_name,
                        address=address,
                        contact_person_phone=contact_person_phone,
                        contact_person_email=contact_person_email,
                        description=description
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

    return redirect(ADMIN + ITEM_SUPPLIERS_LIST)