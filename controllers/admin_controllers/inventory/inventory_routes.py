import os
from datetime import datetime
from io import StringIO, BytesIO

import pandas as pd
from flask import render_template, request, redirect, flash, jsonify, send_file, url_for
from reportlab.lib import colors
# ReportLab Imports for PDF export
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from werkzeug.utils import secure_filename

from controllers.admin_controllers import admin, allowed_file
from controllers.constant.adminPathConstant import ADMIN, ITEMS_GET_BY_CATEGORY, ITEM_STOCKS, ITEM_STOCKS_ADD, \
    ITEM_STOCKS_EDIT, ITEM_STOCKS_DELETE, ITEM_STOCKS_RESTORE, ITEM_STOCKS_EXPORT, ITEM_STOCKS_IMPORT, \
    ITEM_STOCKS_IMPORT_SAMPLE
from models.InventoryItemModel import Item, ItemCategory, ItemSupplier, ItemStore, ItemStock
from utils.config import db


# Define upload folder
UPLOAD_FOLDER = 'static/uploads' # This should likely be consistent with your 'document_path' logic
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- API Endpoint to get items by category ---
@admin.route(ITEMS_GET_BY_CATEGORY + "/<int:category_id>", methods=['GET'])
def get_items_by_category(category_id):
    """
    Returns a JSON list of items belonging to a specific category.
    Used for dynamic dropdowns in the frontend.
    """
    items = Item.query.filter_by(category_id=category_id, is_deleted=False).all()
    items_data = [{'id': item.id, 'name': item.item_name} for item in items]
    return jsonify(items_data)


# --- View all Item Stock ---
@admin.route(ITEM_STOCKS, methods=['GET'], endpoint='inventory_item_stock_list')
def item_stock_list():
    """
    Renders the item stock management page, displaying active and archived stock.
    """
    item_categories = ItemCategory.query.filter_by(is_deleted=False).order_by(ItemCategory.name).all()
    # Prepare all active items for JavaScript filtering in the frontend
    all_items_data = [
        {'id': item.id, 'name': item.item_name, 'category_id': item.category_id}
        for item in Item.query.filter_by(is_deleted=False).order_by(Item.item_name).all()
    ]
    suppliers = ItemSupplier.query.filter_by(is_deleted=False).order_by(ItemSupplier.name).all()
    stores = ItemStore.query.filter_by(is_deleted=False).order_by(ItemStore.name).all()

    # Eager load relationships to avoid N+1 queries in template for item, supplier, store names
    item_stocks = ItemStock.query.filter_by(is_deleted=False)\
        .options(db.joinedload(ItemStock.item).joinedload(Item.category))\
        .options(db.joinedload(ItemStock.supplier))\
        .options(db.joinedload(ItemStock.store))\
        .all()
    archived_item_stocks = ItemStock.query.filter_by(is_deleted=True)\
        .options(db.joinedload(ItemStock.item).joinedload(Item.category))\
        .options(db.joinedload(ItemStock.supplier))\
        .options(db.joinedload(ItemStock.store))\
        .all()

    today_date = datetime.now().strftime('%Y-%m-%d')

    return render_template('admin_templates/inventory/item_stock.html',
                           item_categories=item_categories,
                           items=all_items_data,
                           suppliers=suppliers,
                           stores=stores,
                           item_stocks=item_stocks,
                           archived_item_stocks=archived_item_stocks,
                           today_date=today_date,
                           ADMIN=ADMIN,
                           ITEM_STOCKS_ADD=ITEM_STOCKS_ADD,
                           ITEM_STOCKS_EDIT=ITEM_STOCKS_EDIT,
                           ITEM_STOCKS_DELETE=ITEM_STOCKS_DELETE,
                           ITEM_STOCKS_RESTORE=ITEM_STOCKS_RESTORE,
                           ITEM_STOCKS_EXPORT=ITEM_STOCKS_EXPORT,
                           ITEM_STOCKS_IMPORT=ITEM_STOCKS_IMPORT,
                           ITEM_STOCKS_IMPORT_SAMPLE=ITEM_STOCKS_IMPORT_SAMPLE,
                           ITEMS_GET_BY_CATEGORY=ITEMS_GET_BY_CATEGORY)


# --- Add New Stock Entry ---
@admin.route(ITEM_STOCKS_ADD, methods=['POST'])
def add_item_stock():
    """
    Handles the addition of a new item stock entry.
    """
    try:
        item_id = request.form.get('item_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)
        store_id = request.form.get('store_id', type=int)
        quantity = request.form.get('quantity', type=int)
        purchase_price = request.form.get('purchase_price', type=float)
        purchase_date_str = request.form.get('purchase_date') # Use purchase_date as per model
        description = request.form.get('description')
        selling_price = request.form.get('selling_price', type=float)
        batch_number = request.form.get('batch_number')
        manufacture_date_str = request.form.get('manufacture_date')
        expiry_date_str = request.form.get('expiry_date')

        # Basic validation for required fields
        if not all([item_id, supplier_id, quantity is not None, purchase_price is not None, purchase_date_str]):
            flash('Missing required fields: Item, Supplier, Quantity, Purchase Price, Purchase Date.', 'danger')
            return redirect(url_for(f'{ADMIN}.inventory_item_stock_list')) # Use url_for for cleaner redirects

        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()

        manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d').date() if manufacture_date_str else None
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None

        attached_document_path = None
        if 'attached_document' in request.files:
            file = request.files['attached_document']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                attached_document_path = os.path.join(UPLOAD_FOLDER, unique_filename) # Store relative path

        new_stock = ItemStock(
            item_id=item_id,
            supplier_id=supplier_id,
            store_id=store_id if store_id else None,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            selling_price=selling_price,
            batch_number=batch_number,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            description=description,
            document_path=attached_document_path
        )
        db.session.add(new_stock)
        db.session.commit()
        flash('Stock entry added successfully!', 'success')
    except ValueError as ve:
        db.session.rollback()
        flash(f'Error converting data: {str(ve)}. Please check your input for dates and numbers.', 'danger')
        print(f"ValueError adding stock: {ve}")
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding stock entry: {str(e)}', 'danger')
        print(f"Exception adding stock: {e}")
    return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))


# --- Edit Stock Entry ---
@admin.route(f'{ITEM_STOCKS_EDIT}/<int:stock_id>', methods=['POST'])
def edit_item_stock(stock_id):
    """
    Handles the editing of an existing item stock entry.
    """
    stock = ItemStock.query.get_or_404(stock_id)
    try:
        stock.item_id = request.form.get('item_id', type=int)
        stock.supplier_id = request.form.get('supplier_id', type=int)
        stock.store_id = request.form.get('store_id', type=int) if request.form.get('store_id') else None
        stock.quantity = request.form.get('quantity', type=int)
        stock.purchase_price = request.form.get('purchase_price', type=float) # Corrected to purchase_price
        stock.selling_price = request.form.get('selling_price', type=float) # Corrected to selling_price
        stock.batch_number = request.form.get('batch_number')
        stock.description = request.form.get('description')

        purchase_date_str = request.form.get('purchase_date')
        stock.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None

        manufacture_date_str = request.form.get('manufacture_date')
        stock.manufacture_date = datetime.strptime(manufacture_date_str, '%Y-%m-%d').date() if manufacture_date_str else None

        expiry_date_str = request.form.get('expiry_date')
        stock.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None

        # Handle document deletion
        if 'delete_document' in request.form and stock.document_path:
            full_path = os.path.join(UPLOAD_FOLDER, os.path.basename(stock.document_path))
            if os.path.exists(full_path):
                os.remove(full_path)
            stock.document_path = None
            flash('Existing document removed.', 'info')

        # Handle new document upload
        if 'attached_document' in request.files:
            file = request.files['attached_document']
            if file and allowed_file(file.filename):
                # Before saving new, remove old one if it exists and wasn't explicitly deleted above
                if stock.document_path: # Check if there's an existing path
                    full_path_old = os.path.join(UPLOAD_FOLDER, os.path.basename(stock.document_path))
                    if os.path.exists(full_path_old):
                        os.remove(full_path_old)
                        flash('Old document replaced.', 'info')

                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                stock.document_path = os.path.join(UPLOAD_FOLDER, unique_filename) # Store relative path
                flash('New document uploaded.', 'info')

        db.session.commit()
        flash('Stock entry updated successfully!', 'success')
    except ValueError as ve:
        db.session.rollback()
        flash(f'Error converting data: {str(ve)}. Please check your input for dates and numbers.', 'danger')
        print(f"ValueError updating stock {stock_id}: {ve}")
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating stock entry: {str(e)}', 'danger')
        print(f"Exception updating stock {stock_id}: {e}")
    return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))


# --- Soft Delete Stock Entry ---
@admin.route(f'{ITEM_STOCKS_DELETE}/<int:stock_id>', methods=['POST'])
def delete_item_stock(stock_id):
    """
    Soft deletes an item stock entry by setting its is_deleted flag to True.
    """
    stock = ItemStock.query.get_or_404(stock_id)
    try:
        stock.is_deleted = True
        stock.deleted_at = datetime.now()
        db.session.commit()
        flash('Stock entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting stock entry: {str(e)}', 'danger')
        print(f"Exception deleting stock {stock_id}: {e}")
    return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))


# --- Restore Deleted Stock Entry ---
@admin.route(f'{ITEM_STOCKS_RESTORE}/<int:stock_id>', methods=['POST'])
def restore_item_stock(stock_id):
    """
    Restores a soft-deleted item stock entry by setting its is_deleted flag to False.
    """
    stock = ItemStock.query.get_or_404(stock_id)
    try:
        stock.is_deleted = False
        stock.deleted_at = None
        db.session.commit()
        flash('Stock entry restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring stock entry: {str(e)}', 'danger')
        print(f"Exception restoring stock {stock_id}: {e}")
    return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))


# --- Export Item Stocks ---
@admin.route(f'{ITEM_STOCKS_EXPORT}/<string:file_format>', methods=['GET'])
def export_item_stocks(file_format):
    """
    Exports active item stock data to CSV, Excel, or PDF format.
    """
    item_stocks = ItemStock.query.filter_by(is_deleted=False).all()

    data = []
    for stock in item_stocks:
        data.append({
            "ID": stock.id,
            "Item Name": stock.item.item_name if stock.item else 'N/A',
            "Category": stock.item.category.name if stock.item and stock.item.category else 'N/A',
            "Store": stock.store.name if stock.store else 'N/A',
            "Supplier": stock.supplier.name if stock.supplier else 'N/A',
            "Quantity": stock.quantity,
            "Purchase Price": stock.purchase_price, # Aligned with model
            "Selling Price": stock.selling_price if stock.selling_price is not None else 'N/A',
            "Purchase Date": stock.purchase_date.strftime('%Y-%m-%d') if stock.purchase_date else 'N/A',
            "Batch Number": stock.batch_number if stock.batch_number else 'N/A',
            "Manufacture Date": stock.manufacture_date.strftime('%Y-%m-%d') if stock.manufacture_date else 'N/A',
            "Expiry Date": stock.expiry_date.strftime('%Y-%m-%d') if stock.expiry_date else 'N/A',
            "Description": stock.description if stock.description else 'N/A',
            "Last Updated": stock.updated_at.strftime('%Y-%m-%d %H:%M:%S') if stock.updated_at else ''
        })

    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    download_filename = f'item_stocks_export_{current_time}'

    if file_format == 'csv':
        output = StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode('utf-8')),
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=f'{download_filename}.csv')

    elif file_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Item Stocks')
        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True,
                         download_name=f'{download_filename}.xlsx')

    elif file_format == 'pdf':
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        title_text = "Item Stock Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        # Add headers to pdf_data, filtering out 'ID' column as it's typically for internal use
        header_cols = [col for col in df.columns.tolist() if col != 'ID']
        pdf_data.append([Paragraph(col, styles['h3']) for col in header_cols])

        # Add data rows, converting cell content to Paragraph objects
        for index, row in df.iterrows():
            row_data = []
            for col_name in header_cols:
                cell_content = str(row[col_name]) if pd.notna(row[col_name]) else 'N/A' # Handle NaN gracefully
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(header_cols)
        # Dynamically calculate column widths, consider using a more sophisticated approach for varied content
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Only add table if there is data (i.e., more than just the header row)
        if len(pdf_data) > 1:
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
        else:
            elements.append(Paragraph("No item stock data available for this report.", normal_style))

        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'{download_filename}.pdf'
        )

    else:
        flash('Invalid export format.', 'danger')
        return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))


# --- Import Item Stocks Sample File ---
@admin.route(ITEM_STOCKS_IMPORT_SAMPLE, methods=['GET'])
def import_item_stocks_sample():
    """
    Provides a sample Excel file for item stock import.
    """
    sample_data = [{
        "item_name": "Syringe (10ml)",
        "supplier_name": "MediCorp",
        "store_name": "Main Pharmacy",
        "quantity": 100,
        "purchase_price": 5.25,
        "selling_price": 7.50,
        "purchase_date": datetime.now().strftime('%Y-%m-%d'), # Consistent with model
        "batch_number": "BATCH123",
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-12-31",
        "description": "10ml Syringe, Box of 100"
    }, {
        "item_name": "Cotton Roll (500g)",
        "supplier_name": "Health Essentials",
        "store_name": "Storage Room A",
        "quantity": 50,
        "purchase_price": 12.00,
        "selling_price": 18.00,
        "purchase_date": datetime.now().strftime('%Y-%m-%d'), # Consistent with model
        "batch_number": "COTTON456",
        "manufacture_date": "2023-06-15",
        "expiry_date": "2025-06-15",
        "description": "Medical grade cotton roll"
    }]

    df = pd.DataFrame(sample_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Item Stock Sample')
    output.seek(0)

    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name='item_stock_import_sample.xlsx')


# --- Import Item Stocks ---
@admin.route(ITEM_STOCKS_IMPORT, methods=['POST'])
def import_item_stocks():
    """
    Handles the import of item stock data from an Excel file.
    """
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))

    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        flash('Invalid file type. Please upload an Excel file (.xlsx or .xls).', 'danger')
        return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))

    overwrite_data = 'overwrite' in request.form # Check if overwrite checkbox is ticked

    try:
        df = pd.read_excel(file.stream)
        df.columns = df.columns.str.lower().str.strip() # Normalize column names

        expected_headers = [
            "item_name", "supplier_name", "quantity", "purchase_price", "purchase_date", # Consistent with model
            "selling_price", "batch_number", "manufacture_date", "expiry_date",
            "description", "store_name" # store_name is optional but expected in sample
        ]

        # Check if all required headers are present (excluding optional store_name for initial check)
        required_headers_present = all(header in df.columns for header in expected_headers if header not in ["store_name", "selling_price", "batch_number", "manufacture_date", "expiry_date", "description"])
        if not required_headers_present:
            flash(
                f'Excel file must contain all required headers: {", ".join([h for h in expected_headers if h not in ["store_name", "selling_price", "batch_number", "manufacture_date", "expiry_date", "description"]])}. Optional: {", ".join([h for h in expected_headers if h in ["store_name", "selling_price", "batch_number", "manufacture_date", "expiry_date", "description"]])}.',
                'danger')
            return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for index, row in df.iterrows():
            # Use .get() with default empty string for robustness against missing columns
            item_name = str(row.get('item_name', '')).strip()
            supplier_name = str(row.get('supplier_name', '')).strip()
            store_name = str(row.get('store_name', '')).strip()
            quantity_str = str(row.get('quantity', '')).strip()
            purchase_price_str = str(row.get('purchase_price', '')).strip()
            purchase_date_str = str(row.get('purchase_date', '')).strip() # Consistent with model
            selling_price_str = str(row.get('selling_price', '')).strip()
            batch_number = str(row.get('batch_number', '')).strip()
            manufacture_date_str = str(row.get('manufacture_date', '')).strip()
            expiry_date_str = str(row.get('expiry_date', '')).strip()
            description = str(row.get('description', '')).strip()

            if not all([item_name, supplier_name, quantity_str, purchase_price_str, purchase_date_str]):
                errors.append(
                    f"Row {index + 2} skipped: Missing required data (Item Name, Supplier Name, Quantity, Purchase Price, Purchase Date).")
                skipped_count += 1
                continue

            try:
                # Convert to float first, then int for quantity to handle Excel's potential scientific notation or decimals
                quantity = int(float(quantity_str))
                purchase_price = float(purchase_price_str)
                selling_price = float(selling_price_str) if selling_price_str else None

                # Robust date parsing
                purchase_date_obj = None
                if purchase_date_str:
                    try:
                        purchase_date_obj = pd.to_datetime(purchase_date_str).date()
                    except ValueError:
                        # Fallback for non-standard date formats
                        try:
                            purchase_date_obj = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Row {index + 2} skipped: Invalid Purchase Date format for '{item_name}'. Expected YYYY-MM-DD.")
                            skipped_count += 1
                            continue

                manufacture_date_obj = None
                if manufacture_date_str:
                    try:
                        manufacture_date_obj = pd.to_datetime(manufacture_date_str).date()
                    except ValueError:
                        pass # Allow None if format is bad

                expiry_date_obj = None
                if expiry_date_str:
                    try:
                        expiry_date_obj = pd.to_datetime(expiry_date_str).date()
                    except ValueError:
                        pass # Allow None if format is bad


            except ValueError as ve:
                errors.append(f"Row {index + 2} skipped: Data type conversion error for '{item_name}' - {str(ve)}.")
                skipped_count += 1
                continue
            except Exception as e:
                errors.append(f"Row {index + 2} skipped: General parsing error for '{item_name}' - {str(e)}.")
                skipped_count += 1
                continue

            item = Item.query.filter(db.func.lower(Item.item_name) == item_name.lower(),
                                     Item.is_deleted == False).first()
            if not item:
                errors.append(f"Row {index + 2} skipped: Item '{item_name}' not found. Please create it first.")
                skipped_count += 1
                continue

            supplier = ItemSupplier.query.filter(db.func.lower(ItemSupplier.name) == supplier_name.lower(),
                                                 ItemSupplier.is_deleted == False).first()
            if not supplier:
                errors.append(f"Row {index + 2} skipped: Supplier '{supplier_name}' not found. Please create it first.")
                skipped_count += 1
                continue

            store = None
            if store_name:
                store = ItemStore.query.filter(db.func.lower(ItemStore.name) == store_name.lower(),
                                               ItemStore.is_deleted == False).first()
                if not store:
                    errors.append(
                        f"Row {index + 2} skipped: Store '{store_name}' not found. Please create it first or leave blank if optional.")
                    skipped_count += 1
                    continue

            # Check for existing stock entry with same Item, Supplier, Store, and Batch Number (if provided)
            existing_stock_query = ItemStock.query.filter_by(
                item_id=item.id,
                supplier_id=supplier.id,
                is_deleted=False
            )
            if store:
                existing_stock_query = existing_stock_query.filter_by(store_id=store.id)
            # Only filter by batch_number if it's provided and not empty
            if batch_number:
                existing_stock_query = existing_stock_query.filter_by(batch_number=batch_number)
            else:
                # If batch_number is not provided, treat entries with no batch number as a distinct set.
                existing_stock_query = existing_stock_query.filter(ItemStock.batch_number.is_(None))


            existing_stock = existing_stock_query.first()

            if existing_stock:
                if overwrite_data:
                    existing_stock.quantity = quantity
                    existing_stock.purchase_price = purchase_price
                    existing_stock.selling_price = selling_price
                    existing_stock.purchase_date = purchase_date_obj
                    existing_stock.batch_number = batch_number if batch_number else None
                    existing_stock.manufacture_date = manufacture_date_obj
                    existing_stock.expiry_date = expiry_date_obj
                    existing_stock.description = description
                    # Note: Attached document is not handled in import for updates to avoid complexity
                    updated_count += 1
                else:
                    errors.append(
                        f"Row {index + 2} skipped: Stock entry for item '{item_name}' with batch '{batch_number if batch_number else 'N/A'}' already exists and overwrite was not selected.")
                    skipped_count += 1
            else:
                new_stock = ItemStock(
                    item_id=item.id,
                    supplier_id=supplier.id,
                    store_id=store.id if store else None,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    selling_price=selling_price,
                    purchase_date=purchase_date_obj,
                    batch_number=batch_number if batch_number else None,
                    manufacture_date=manufacture_date_obj,
                    expiry_date=expiry_date_obj,
                    description=description
                    # document_path is not handled during import via spreadsheet for simplicity
                )
                db.session.add(new_stock)
                imported_count += 1

        db.session.commit()

        if errors:
            flash_message = (
                f'Import completed with {imported_count} new entries, {updated_count} updated entries, '
                f'and {skipped_count} skipped rows. Check below for details.'
            )
            flash(flash_message, 'warning')
            for error_msg in errors:
                flash(error_msg, 'warning') # Flash each specific error as a separate message
        else:
            flash(f'Import successful! {imported_count} new entries added, {updated_count} entries updated.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred during import: {str(e)}. Please check your file format and data.',
              'danger')
        print(f"Import Error: {e}")

    return redirect(url_for(f'{ADMIN}.inventory_item_stock_list'))