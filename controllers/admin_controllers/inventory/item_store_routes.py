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
# Assuming you have constants for ItemStore paths. Adjust if names are different.
from controllers.constant.adminPathConstant import ADMIN, ITEM_STORES_ADD, \
    ITEM_STORES_EDIT, ITEM_STORES_DELETE, ITEM_STORES_RESTORE, ITEM_STORES_EXPORT, \
    ITEM_STORES_IMPORT, ITEM_STORES_IMPORT_SAMPLE, ITEM_STORES_LIST
from middleware.auth_middleware import token_required
from models.InventoryItemModel import ItemStore
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(ITEM_STORES_LIST, methods=['GET'], endpoint='item-stores')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def item_stores(current_user):
    stores = ItemStore.query.filter_by(is_deleted=0).order_by(ItemStore.name).all()
    archived_stores = ItemStore.query.filter_by(is_deleted=1).order_by(
        ItemStore.deleted_at.desc()).all()
    return render_template('admin_templates/inventory/item_stores.html', stores=stores,
                           archived_stores=archived_stores,
                           ADMIN=ADMIN,
                           ITEM_STORES_ADD=ITEM_STORES_ADD,
                           ITEM_STORES_EDIT=ITEM_STORES_EDIT,
                           ITEM_STORES_DELETE=ITEM_STORES_DELETE,
                           ITEM_STORES_RESTORE=ITEM_STORES_RESTORE,
                           ITEM_STORES_EXPORT=ITEM_STORES_EXPORT,
                           ITEM_STORES_IMPORT=ITEM_STORES_IMPORT,
                           ITEM_STORES_IMPORT_SAMPLE=ITEM_STORES_IMPORT_SAMPLE)


@admin.route(ITEM_STORES_ADD, methods=['POST'], endpoint='item-stores/add')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_item_store(current_user):
    try:
        store_name = request.form.get('name')
        store_stock_code = request.form.get('stock_code')
        store_description = request.form.get('description')

        existing_store = ItemStore.query.filter(
            ItemStore.name == store_name,
            ItemStore.is_deleted == False
        ).first()

        if existing_store:
            flash(f'Item store "{store_name}" already exists.', 'warning')
            return redirect(ADMIN + ITEM_STORES_LIST)

        store = ItemStore(
            name=store_name,
            stock_code=store_stock_code,
            description=store_description
        )
        db.session.add(store)
        db.session.commit()
        flash('Item Store added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error adding item store: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_STORES_LIST)


@admin.route(ITEM_STORES_EDIT + '/<int:id>', methods=['POST'],
             endpoint='item-stores/<int:id>/edit')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_item_store(current_user, id):
    store = ItemStore.query.get_or_404(id)
    try:
        store.name = request.form.get('name')
        store.stock_code = request.form.get('stock_code')
        store.description = request.form.get('description')
        db.session.commit()
        flash('Item Store updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating item store: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_STORES_LIST)


@admin.route(ITEM_STORES_DELETE + '/<int:id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_item_store(current_user, id):
    store = ItemStore.query.get_or_404(id)
    try:
        store.is_deleted = True
        store.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Item Store deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item store: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_STORES_LIST)


@admin.route(ITEM_STORES_RESTORE + '/<int:id>', methods=['POST'],
             endpoint='item-stores/<int:id>/restore')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_item_store(current_user, id):
    store = ItemStore.query.get_or_404(id)
    try:
        store.is_deleted = False
        store.deleted_at = None
        db.session.commit()
        flash('Item Store restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring item store: {str(e)}', 'danger')
    return redirect(ADMIN + ITEM_STORES_LIST)


@admin.route(ITEM_STORES_EXPORT + '/<format>')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_item_stores(current_user, format):
    stores = ItemStore.query.filter_by(is_deleted=False).all()

    data = []
    for store in stores:
        data.append({
            'Name': store.name,
            'Item Stock Code': store.stock_code,
            'Description': store.description,
            'Created At': store.created_at.strftime('%Y-%m-%d %H:%M'),
            'Updated At': store.updated_at.strftime('%Y-%m-%d %H:%M')
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
            download_name='item_stores.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Stores')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='item_stores.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        title_text = "Item Stores Report"
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
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns  # Distribute evenly

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
            download_name='item_stores.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + ITEM_STORES_LIST)


SAMPLE_ITEM_STORE_EXCEL_STRUCTURE = [
    {
        "Name": "Main Warehouse",
        "Item Stock Code": "MW001",
        "Description": "Primary storage for all inventory"
    },
    {
        "Name": "Pharmacy Storage",
        "Item Stock Code": "PS002",
        "Description": "Dedicated storage for medical items"
    }
]


@admin.route(ITEM_STORES_IMPORT_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_item_store_sample_import_file(current_user):
    df = pd.DataFrame(SAMPLE_ITEM_STORE_EXCEL_STRUCTURE)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Item Stores')
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING ITEM STORES:",
            "",
            "1. Use the 'Item Stores' sheet for your data",
            "2. Required columns: 'Name'",
            "3. Optional columns: 'Item Stock Code', 'Description'",
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
        download_name='sample_import_item_stores.xlsx'
    )


@admin.route(ITEM_STORES_IMPORT, methods=['POST'], endpoint="import_item_stores")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_item_stores(current_user):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + ITEM_STORES_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + ITEM_STORES_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + ITEM_STORES_LIST)

    try:
        df = pd.read_excel(file)
        required_columns = ['Name']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}', 'error')
            return redirect(ADMIN + ITEM_STORES_LIST)

        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for _, row in df.iterrows():
            try:
                name = row['Name']
                stock_code = row.get('Item Stock Code', '')
                description = row.get('Description', '')

                if not name or pd.isna(name):
                    error_count += 1
                    continue

                existing = ItemStore.query.filter_by(name=name).first()

                if existing:
                    if overwrite:
                        existing.stock_code = stock_code
                        existing.description = description
                        db.session.commit()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    new_store = ItemStore(
                        name=name,
                        stock_code=stock_code,
                        description=description
                    )
                    db.session.add(new_store)
                    db.session.commit()
                    success_count += 1

            except Exception as e:
                error_count += 1
                continue

        flash(f'Import completed: {success_count} successful, {error_count} failed',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(ADMIN + ITEM_STORES_LIST)
