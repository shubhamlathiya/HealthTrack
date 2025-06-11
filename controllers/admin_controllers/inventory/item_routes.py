# --- Imports ---
import traceback
from datetime import datetime
from io import StringIO, BytesIO

import pandas as pd
from flask import render_template, request, redirect, flash, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, INVENTORY_ITEMS_ADD, INVENTORY_ITEMS_EDIT, \
    INVENTORY_ITEMS_DELETE, INVENTORY_ITEMS_RESTORE, INVENTORY_ITEMS_EXPORT, INVENTORY_ITEMS_IMPORT, \
    INVENTORY_ITEMS_IMPORT_SAMPLE, INVENTORY_ITEMS_LIST
from models.InventoryItemModel import Item, ItemCategory
from utils.config import db



@admin.route(INVENTORY_ITEMS_LIST, methods=['GET'])
def inventory_items():
    """
    Displays the list of active and deleted inventory items.
    """
    active_items = Item.query.filter_by(is_deleted=False).all()
    deleted_items = Item.query.filter_by(is_deleted=True).all()
    item_categories = ItemCategory.query.filter_by(is_deleted=False).all()

    return render_template('admin_templates/inventory/item_items.html',
                           active_items=active_items,
                           deleted_items=deleted_items,
                           item_categories=item_categories,
                           ADMIN=ADMIN,
                           INVENTORY_ITEMS_ADD=INVENTORY_ITEMS_ADD,
                           INVENTORY_ITEMS_EDIT=INVENTORY_ITEMS_EDIT,
                           INVENTORY_ITEMS_DELETE=INVENTORY_ITEMS_DELETE,
                           INVENTORY_ITEMS_RESTORE=INVENTORY_ITEMS_RESTORE,
                           INVENTORY_ITEMS_EXPORT=INVENTORY_ITEMS_EXPORT,
                           INVENTORY_ITEMS_IMPORT=INVENTORY_ITEMS_IMPORT,
                           INVENTORY_ITEMS_IMPORT_SAMPLE=INVENTORY_ITEMS_IMPORT_SAMPLE)


@admin.route(INVENTORY_ITEMS_ADD, methods=['POST'])
def add_inventory_item():
    """
    Handles adding a new inventory item.
    """
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        min_quantity = request.form.get('min_quantity', type=int)
        is_restricted = 'is_restricted' in request.form  # Checkbox value

        if not all([item_name, category_id, min_quantity is not None]):
            flash('Item Name, Category, and Minimum Quantity are required.', 'danger')
            return redirect(ADMIN + INVENTORY_ITEMS_LIST)

        # Check for duplicate item name
        existing_item = Item.query.filter_by(item_name=item_name, is_deleted=False).first()
        if existing_item:
            flash(f'Item with name "{item_name}" already exists.', 'warning')
            return redirect(ADMIN + INVENTORY_ITEMS_LIST)

        try:
            new_item = Item(
                item_name=item_name,
                category_id=category_id,
                description=description,
                min_quantity=min_quantity,
                is_restricted=is_restricted
            )
            db.session.add(new_item)
            db.session.commit()
            flash(f'Item "{item_name}" added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'danger')

    return redirect(ADMIN + INVENTORY_ITEMS_LIST)


@admin.route(f'{INVENTORY_ITEMS_EDIT}/<int:item_id>', methods=['POST'])
def edit_inventory_item(item_id):
    """
    Handles editing an existing inventory item.
    """
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        item_name = request.form.get('item_name')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        min_quantity = request.form.get('min_quantity', type=int)
        is_restricted = 'is_restricted' in request.form

        if not all([item_name, category_id, min_quantity is not None]):
            flash('Item Name, Category, and Minimum Quantity are required.', 'danger')
            return redirect(ADMIN + INVENTORY_ITEMS_LIST)

        # Check for duplicate item name (excluding current item)
        existing_item = Item.query.filter(
            Item.item_name == item_name,
            Item.id != item_id,
            Item.is_deleted == False
        ).first()
        if existing_item:
            flash(f'Another item with name "{item_name}" already exists.', 'warning')
            return redirect(ADMIN + INVENTORY_ITEMS_LIST)

        try:
            item.item_name = item_name
            item.category_id = category_id
            item.description = description
            item.min_quantity = min_quantity
            item.is_restricted = is_restricted
            # updated_at is automatically handled by server_default onupdate=db.func.now()

            db.session.commit()
            flash(f'Item "{item.item_name}" updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating item: {str(e)}', 'danger')

    return redirect(ADMIN + INVENTORY_ITEMS_LIST)


@admin.route(f'{INVENTORY_ITEMS_DELETE}/<int:item_id>', methods=['POST'])
def delete_inventory_item(item_id):
    """
    Soft deletes an inventory item.
    """
    item = Item.query.get_or_404(item_id)
    try:
        item.is_deleted = True
        item.deleted_at = datetime.now()
        db.session.commit()
        flash(f'Item "{item.item_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEMS_LIST)


@admin.route(f'{INVENTORY_ITEMS_RESTORE}/<int:item_id>', methods=['POST'])
def restore_inventory_item(item_id):
    """
    Restores a soft-deleted inventory item.
    """
    item = Item.query.get_or_404(item_id)
    try:
        item.is_deleted = False
        item.deleted_at = None
        db.session.commit()
        flash(f'Item "{item.item_name}" restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEMS_LIST)


# --- Modified Export Route ---
@admin.route(f'{INVENTORY_ITEMS_EXPORT}/<string:file_format>', methods=['GET'])
def export_inventory_items(file_format):
    """
    Exports all active inventory items to a specified file format (CSV, Excel, PDF).
    """
    items = Item.query.filter_by(is_deleted=False).all()

    # Prepare data for export
    data = []
    for item in items:
        data.append({
            "ID": item.id,
            "Item Name": item.item_name,
            "Category": item.category.name if item.category else 'N/A',
            "Description": item.description,
            "Min Quantity": item.min_quantity,
            "Is Restricted": 'Yes' if item.is_restricted else 'No',
            "Created At": item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            "Updated At": item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        })

    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    if file_format == 'csv':
        output = StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode('utf-8')),
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=f'inventory_items_export_{current_time}.csv')

    elif file_format == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Inventory Items')
        output.seek(0)
        return send_file(output,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True,
                         download_name=f'inventory_items_export_{current_time}.xlsx')

    elif file_format == 'pdf':
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        title_text = "Item Stores Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        # Add headers to pdf_data, converting column names to Paragraph objects
        pdf_data.append([Paragraph(col, styles['h3']) for col in df.columns.tolist()])

        # Add data rows, converting cell content to Paragraph objects
        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                # Ensure content is string before passing to Paragraph
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter
        LEFT_MARGIN = 0.75 * inch
        RIGHT_MARGIN = 0.75 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)
        # Dynamically calculate column widths based on available width
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

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
            download_name=f'inventory_items_export_{current_time}.pdf'  # Dynamic filename
        )

    else:
        flash('Invalid export format.', 'danger')
        return redirect(ADMIN + INVENTORY_ITEMS_LIST)


# --- Modified Sample Import Route (now generates Excel) ---
@admin.route(INVENTORY_ITEMS_IMPORT_SAMPLE, methods=['GET'])
def download_item_import_sample():
    """
    Provides a sample Excel file for inventory item import, matching the expected format.
    """
    # Sample headers for import
    sample_data = [{
        "item_name": "Syringe (10ml)",
        "category_name": "Syringe Packs",
        "description": "10ml Syringe, Box of 100",
        "min_quantity": 10,
        "is_restricted": "No"
    }, {
        "item_name": "Cotton Roll (500g)",
        "category_name": "Cotton Packs",
        "description": "Medical grade cotton roll",
        "min_quantity": 5,
        "is_restricted": "No"
    }]

    df = pd.DataFrame(sample_data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sample Items')
    output.seek(0)

    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name='inventory_items_import_sample.xlsx')


# --- Modified Import Route (now handles Excel and Overwrite) ---
@admin.route(INVENTORY_ITEMS_IMPORT, methods=['POST'])
def import_inventory_items():
    """
    Handles importing inventory items from an Excel file.
    """
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(ADMIN + INVENTORY_ITEMS_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(ADMIN + INVENTORY_ITEMS_LIST)

    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        flash('Invalid file type. Please upload an Excel file (.xlsx or .xls).', 'danger')
        return redirect(ADMIN + INVENTORY_ITEMS_LIST)

    overwrite_data = 'overwrite' in request.form  # Check if overwrite checkbox is ticked

    try:
        # Read Excel file using pandas
        df = pd.read_excel(file.stream)

        # Convert column names to lowercase and strip spaces for robust matching
        df.columns = df.columns.str.lower().str.strip()

        # Expected headers from the sample file (lowercase for matching)
        expected_headers = ["item_name", "category_name", "description", "min_quantity", "is_restricted"]
        if not all(header in df.columns for header in expected_headers):
            flash(f'Excel file must contain all required headers: {", ".join(expected_headers)}', 'danger')
            return redirect(ADMIN + INVENTORY_ITEMS_LIST)

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        # Iterate over DataFrame rows
        for index, row in df.iterrows():
            item_name = str(row.get('item_name', '')).strip()
            category_name = str(row.get('category_name', '')).strip()
            description = str(row.get('description', '')).strip()
            min_quantity_str = str(row.get('min_quantity', '')).strip()
            is_restricted_str = str(row.get('is_restricted', '')).strip().lower()

            if not item_name or not category_name or not min_quantity_str:
                errors.append(
                    f"Row {index + 2} skipped due to missing required data: Item Name '{item_name}', Category Name '{category_name}', Min Quantity '{min_quantity_str}'.")
                skipped_count += 1
                continue

            try:
                min_quantity = int(min_quantity_str)
            except ValueError:
                errors.append(
                    f"Row {index + 2} for item '{item_name}' skipped: Invalid Min Quantity '{min_quantity_str}'. Must be an integer.")
                skipped_count += 1
                continue

            is_restricted = is_restricted_str in ['yes', 'true', '1']

            category = ItemCategory.query.filter_by(name=category_name).first()
            if not category:
                errors.append(
                    f"Row {index + 2} for item '{item_name}' skipped: Category '{category_name}' not found. Please create it first.")
                skipped_count += 1
                continue

            # Check if item already exists (by name, case-insensitive, not deleted)
            item = Item.query.filter(
                db.func.lower(Item.item_name) == item_name.lower(),
                Item.is_deleted == False
            ).first()

            if item:
                if overwrite_data:
                    # Update existing item
                    item.category_id = category.id
                    item.description = description if description else None  # Allow None for empty descriptions
                    item.min_quantity = min_quantity
                    item.is_restricted = is_restricted
                    updated_count += 1
                else:
                    errors.append(
                        f"Row {index + 2} for item '{item_name}' skipped: Item already exists and overwrite was not selected.")
                    skipped_count += 1
            else:
                # Create new item
                new_item = Item(
                    item_name=item_name,
                    category_id=category.id,
                    description=description if description else None,
                    min_quantity=min_quantity,
                    is_restricted=is_restricted
                )
                db.session.add(new_item)
                imported_count += 1

        db.session.commit()

        if errors:
            flash(
                f'Import completed with {imported_count} new items, {updated_count} updated items, and {skipped_count} skipped rows. Some errors occurred: {"; ".join(errors)}',
                'warning')
        else:
            flash(f'Import successful! {imported_count} new items added, {updated_count} items updated.', 'success')

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'An unexpected error occurred during import: {str(e)}. Please check your file format and data.',
              'danger')
        print(f"Import Error: {e}")  # Log the error for debugging

    return redirect(ADMIN + INVENTORY_ITEMS_LIST)
