from datetime import datetime
from io import StringIO, BytesIO

import pandas as pd
from flask import render_template, request, redirect, flash, jsonify, send_file
from reportlab.lib import colors
# ReportLab Imports for PDF export
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy import func

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, API_GET_AVAILABLE_STOCK, API_GET_USERS_BY_ROLE, \
    ISSUED_ITEMS_LIST, ISSUED_ITEMS_ADD, ISSUED_ITEMS_RETURN, ISSUED_ITEMS_EDIT, ISSUED_ITEMS_DELETE, \
    ISSUED_ITEMS_RESTORE, ISSUED_ITEMS_EXPORT, ITEM_REQUESTS_REJECT, ITEM_REQUESTS_APPROVE
from middleware.auth_middleware import token_required
from models import UserRole, User
from models.InventoryItemModel import ItemStock, IssuedItem, Item, ItemCategory  # Changed ItemCategory to Category
from utils.config import db


# --- Constants for Issued Item Routes ---
# (Assuming these are defined in adminPathConstant)


# --- Helper to calculate available stock ---
def get_total_stock_quantity(item_id):
    """Calculates the total physical stock quantity for a given item_id from active ItemStock entries."""
    total_physical_stock = db.session.query(func.sum(ItemStock.quantity)).filter(
        ItemStock.item_id == item_id,
        ItemStock.is_deleted == False  # Ensure only active stock is counted
    ).scalar() or 0
    return total_physical_stock


def get_total_issued_quantity(item_id):
    """
    Calculates the total quantity of items currently issued or pending (not returned/rejected/cancelled).
    This represents stock that is 'out of inventory'.
    """
    total_issued_not_returned = db.session.query(func.sum(IssuedItem.quantity)).filter(
        IssuedItem.item_id == item_id,
        IssuedItem.status.in_(['Issued', 'Pending', 'Requested']),  # Include 'Requested' for full reservation
        IssuedItem.return_date == None,  # Only count those not yet returned
        IssuedItem.is_deleted == False  # Ensure only active issued items are counted
    ).scalar() or 0
    return total_issued_not_returned


# --- API: Get Available Stock for Item ---
@admin.route(API_GET_AVAILABLE_STOCK + "/<int:item_id>", methods=['GET'])
def get_available_item_stock(item_id):
    """
    Returns the currently available stock for a given item,
    considering total physical stock minus currently issued/pending/requested items.
    """
    item = Item.query.filter_by(id=item_id, is_deleted=False).first()
    if not item:
        return jsonify({'available_stock': 0, 'error': 'Item not found or is deleted'}), 404

    total_physical_stock = get_total_stock_quantity(item_id)
    total_issued_not_returned = get_total_issued_quantity(item_id)

    available_stock = total_physical_stock - total_issued_not_returned
    return jsonify({'available_stock': available_stock})


@admin.route(API_GET_USERS_BY_ROLE + "/<string:role_value>", methods=['GET'])
# @token_required(allowed_roles=[UserRole.ADMIN.name, UserRole.DEPARTMENT_HEAD.name]) # Example authorization
def get_users_by_role(role_value):
    normalized_role_value = role_value.lower()

    try:
        # Convert the normalized string to a UserRole Enum member
        target_role_enum = UserRole(normalized_role_value)
    except ValueError:
        # If the provided normalized_role_value still does not match any enum value
        return jsonify({'users': [],
                        'message': f"Invalid user role: '{role_value}'. Role must be one of {', '.join([role.value for role in UserRole])} (case-insensitive)."}), 400

    try:
        users = User.query.filter_by(role=target_role_enum.value).all()

        users_data = [{'id': user.id, 'name': user.email} for user in users]

    except Exception as e:
        print(f"Error fetching users for role {role_value}: {e}")  # Log the original value for context
        return jsonify({'users': [], 'message': 'Error fetching users.'}), 500

    return jsonify({'users': users_data})


# --- List All Issued Items ---
@admin.route(ISSUED_ITEMS_LIST, methods=['GET'])
def issued_items_list():
    # Fetch active and archived issued items
    active_issued_items = IssuedItem.query.filter_by(is_deleted=False).all()
    archived_issued_items = IssuedItem.query.filter_by(is_deleted=True).all()

    # Prepare data for dropdowns in modals
    item_categories = ItemCategory.query.filter_by(is_deleted=False).all()  # Use 'Category' model

    # Prepare all active items data for JavaScript filtering in the frontend
    all_active_items_for_js = [
        {'id': item.id, 'name': item.item_name, 'category_id': item.category_id}
        for item in Item.query.filter_by(is_deleted=False).all()
    ]

    return render_template('admin_templates/inventory/issued_items.html',
                           item_categories=item_categories,
                           items=all_active_items_for_js,  # Pass the list of dictionaries for JS
                           active_issued_items=active_issued_items,
                           archived_issued_items=archived_issued_items,
                           datetime=datetime,  # Pass datetime for template formatting
                           user_roles=UserRole,  # Pass UserRole enum for frontend logic (e.g., dropdowns)
                           ADMIN=ADMIN,
                           ISSUED_ITEMS_ADD=ISSUED_ITEMS_ADD,
                           ISSUED_ITEMS_RETURN=ISSUED_ITEMS_RETURN,
                           ISSUED_ITEMS_APPROVE_REQUEST=ITEM_REQUESTS_APPROVE,
                           ISSUED_ITEMS_REJECT_REQUEST=ITEM_REQUESTS_REJECT,
                           ISSUED_ITEMS_EDIT=ISSUED_ITEMS_EDIT,
                           ISSUED_ITEMS_DELETE=ISSUED_ITEMS_DELETE,
                           ISSUED_ITEMS_RESTORE=ISSUED_ITEMS_RESTORE,
                           ISSUED_ITEMS_EXPORT=ISSUED_ITEMS_EXPORT,
                           API_GET_AVAILABLE_STOCK=API_GET_AVAILABLE_STOCK,
                           API_GET_USERS_BY_ROLE=API_GET_USERS_BY_ROLE
                           )


# --- Add Issued Item ---
@admin.route(ISSUED_ITEMS_ADD, methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_issued_item(current_user):
    try:
        print(request.form)
        item_id = request.form.get('item_id', type=int)
        issued_to_name = request.form.get('issued_to_name')
        issued_to_user_id = request.form.get('issued_to_user_id')  # Optional, if linked to User model
        user_type = request.form.get('user_type')
        issue_date_str = request.form.get('issue_date')
        quantity = request.form.get('quantity', type=int)
        note = request.form.get('note')
        status = request.form.get('status',
                                  default='Issued')  # Default to 'Issued' for direct issue, or 'Pending' for request

        # New fields from IssuedItem model
        requested_by = request.form.get('requested_by')
        approved_by = request.form.get('approved_by')  # Might be filled later on approval
        department = request.form.get('department')
        purpose = request.form.get('purpose')

        if not all([item_id, issued_to_name, user_type, issue_date_str, quantity]):
            flash('Missing required fields: Item, Issued To Name, User Type, Issue Date, Quantity.', 'danger')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()

        # Stock check: Ensure enough items are available before issuing
        # This available_stock already accounts for currently issued/pending items
        available_stock = get_total_stock_quantity(item_id) - get_total_issued_quantity(item_id)
        if quantity > available_stock:
            flash(f'Cannot issue {quantity} units. Only {available_stock} units are currently available for this item.',
                  'danger')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        new_issued_item = IssuedItem(
            item_id=item_id,
            issued_to_name=issued_to_name,
            issued_to_user_id=issued_to_user_id,
            user_type=user_type,
            issued_by=current_user,  # Use current_user's email or ID as issued_by
            issue_date=issue_date,
            quantity=quantity,
            status=status,
            note=note,
            requested_by=requested_by,
            approved_by=approved_by,
            department=department,
            purpose=purpose
        )
        db.session.add(new_issued_item)
        db.session.commit()
        flash('Issued item added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding issued item: {str(e)}', 'danger')
        print(f"Error adding issued item: {e}")  # For debugging
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Return Issued Item ---
@admin.route(ISSUED_ITEMS_RETURN + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def return_issued_item(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    if issued_item.is_deleted:
        flash('Cannot return a deleted issued item.', 'danger')
        return redirect(ADMIN + ISSUED_ITEMS_LIST)

    try:
        # Prevent returning an item that's already returned or cancelled/rejected
        if issued_item.status in ['Returned', 'Cancelled', 'Rejected']:
            flash(f'Item "{issued_item.item.item_name}" is already {issued_item.status.lower()}.', 'warning')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issued_item.return_date = datetime.now().date()
        issued_item.status = 'Returned'
        issued_item.returned_by = current_user.email  # Log who returned it

        db.session.commit()
        flash('Issued item marked as returned successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error returning issued item: {str(e)}', 'danger')
        print(f"Error returning issued item: {e}")
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Approve Issued Item Request ---
@admin.route(ITEM_REQUESTS_APPROVE + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def approve_issued_item_request(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    if issued_item.is_deleted:
        flash('Cannot approve a deleted item request.', 'danger')
        return redirect(ADMIN + ISSUED_ITEMS_LIST)

    try:
        # Only approve if status is 'Pending' or 'Requested'
        if issued_item.status not in ['Pending', 'Requested']:
            flash(f'Item request is not in a pending state (current status: {issued_item.status}).', 'warning')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        # Re-check stock before approving
        # We need to calculate available stock *excluding this specific pending item's quantity*
        # because its quantity is already counted in `get_total_issued_quantity` if its status is 'Pending'.
        total_physical_stock = get_total_stock_quantity(issued_item.item_id)
        current_issued_quantity_for_item = get_total_issued_quantity(issued_item.item_id)

        # The actual available stock *if this pending item were not counted as "issued/pending"*
        # is `total_physical_stock - (current_issued_quantity_for_item - issued_item.quantity)`.
        # Then, we check if `issued_item.quantity` (the amount requested by this item) fits into that.
        # A simpler way: After approval, the new total issued for this item will be
        # `(current_issued_quantity_for_item - issued_item.quantity) + issued_item.quantity` (which simplifies to current_issued_quantity_for_item)
        # So, the check is just: `if current_issued_quantity_for_item > total_physical_stock`.
        # However, the quantity in `get_total_issued_quantity` *already includes* the `issued_item.quantity` when its status is 'Pending' or 'Requested'.
        # So we want to know, "is there enough stock to fulfill this request NOW, assuming it was already counted as pending?"
        # The correct calculation is: `total_physical_stock - current_issued_quantity_for_item` is the *remaining* available stock.
        # We then check if the *quantity for THIS pending item* can be approved.
        # This implies: available_stock = total_physical_stock - (total_issued_quantity_excluding_this_pending_item).
        # Which is `total_physical_stock - (get_total_issued_quantity(issued_item.item_id) - issued_item.quantity)`.

        # Let's use a clear calculation for current effective available stock.
        # total_physical_stock - (all_other_issued_and_pending_items_excluding_this_one)
        # The current available stock before this approval is:
        currently_available_stock = total_physical_stock - current_issued_quantity_for_item

        # If the requested quantity exceeds what's currently available, then reject
        if issued_item.quantity > currently_available_stock:
            flash(
                f'Cannot approve request for {issued_item.quantity} units. Only {currently_available_stock} units are currently available for this item.',
                'danger')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issued_item.status = 'Issued'
        issued_item.approved_by = current_user.email  # Log who approved it
        # If issue_date was not set (because it was a request), set it now.
        if not issued_item.issue_date:
            issued_item.issue_date = datetime.now().date()

        db.session.commit()
        flash('Issued item request approved and status set to "Issued"!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving item request: {str(e)}', 'danger')
        print(f"Error approving item request: {e}")
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Reject Issued Item Request ---
@admin.route(ITEM_REQUESTS_REJECT + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def reject_issued_item_request(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    if issued_item.is_deleted:
        flash('Cannot reject a deleted item request.', 'danger')
        return redirect(ADMIN + ISSUED_ITEMS_LIST)

    try:
        if issued_item.status not in ['Pending', 'Requested']:
            flash(f'Item request is not in a pending state (current status: {issued_item.status}).', 'warning')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issued_item.status = 'Rejected'
        # Log who rejected and when
        rejection_note = f"\nRejected by {current_user.email} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        issued_item.note = (issued_item.note or "") + rejection_note
        db.session.commit()
        flash('Issued item request rejected!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting item request: {str(e)}', 'danger')
        print(f"Error rejecting item request: {e}")
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Edit Issued Item ---
@admin.route(ISSUED_ITEMS_EDIT + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_issued_item(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    if issued_item.is_deleted:
        flash('Cannot edit a deleted issued item.', 'danger')
        return redirect(ADMIN + ISSUED_ITEMS_LIST)

    try:
        # Capture old values for stock adjustment and comparison
        old_quantity = issued_item.quantity
        old_item_id = issued_item.item_id
        old_status = issued_item.status

        # Update fields from form data
        new_item_id = request.form.get('item_id', type=int)
        new_quantity = request.form.get('quantity', type=int)
        new_status = request.form.get('status', issued_item.status)  # Keep current if not provided

        if new_quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        # Apply updates to the issued_item object first
        issued_item.item_id = new_item_id
        issued_item.issued_to_name = request.form.get('issued_to_name')
        issued_item.issued_to_user_id = request.form.get('issued_to_user_id')
        issued_item.user_type = request.form.get('user_type')
        # issued_by is typically the original issuer, not changed on edit unless explicitly intended
        # For simplicity, we'll keep it as is, or you can allow editing if needed.
        # issued_item.issued_by = request.form.get('issued_by')
        issued_item.quantity = new_quantity
        issued_item.note = request.form.get('note')
        issued_item.requested_by = request.form.get('requested_by')
        issued_item.approved_by = request.form.get('approved_by')
        issued_item.department = request.form.get('department')
        issued_item.purpose = request.form.get('purpose')
        issued_item.status = new_status  # Update status

        issue_date_str = request.form.get('issue_date')
        if issue_date_str:
            issued_item.issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        else:
            issued_item.issue_date = None

        return_date_str = request.form.get('return_date')
        if return_date_str:
            issued_item.return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        else:
            issued_item.return_date = None  # Allow clearing return date

        # --- Stock Re-check Logic ---
        # Only perform stock check if the item is currently 'Issued', 'Pending', or 'Requested'
        # or if its status is changing *to* one of these statuses.
        stock_affecting_statuses = ['Issued', 'Pending', 'Requested']
        is_currently_stock_affecting = old_status in stock_affecting_statuses and issued_item.return_date is None
        will_be_stock_affecting = new_status in stock_affecting_statuses and issued_item.return_date is None

        if will_be_stock_affecting:
            total_physical_stock = get_total_stock_quantity(issued_item.item_id)
            total_issued_for_target_item = get_total_issued_quantity(issued_item.item_id)

            # Adjust `total_issued_for_target_item` to exclude the current `issued_item`'s old quantity,
            # but only if the item_id hasn't changed.
            # If item_id changed, the current item's old quantity is NOT counted in `total_issued_for_target_item`.

            # This is the quantity that will be "out of stock" after this specific issued_item update.
            # Start with the total issued for the *new* item_id
            potential_new_total_issued = total_issued_for_target_item

            if is_currently_stock_affecting and old_item_id == issued_item.item_id:
                # If item_id didn't change and it was already counted, remove its old quantity
                potential_new_total_issued = total_issued_for_target_item - old_quantity
            elif is_currently_stock_affecting and old_item_id != issued_item.item_id:
                # If item_id changed, and it was previously stock-affecting for the OLD item_id,
                # its old quantity is not in total_issued_for_target_item, so no need to subtract.
                pass  # potential_new_total_issued is already correct
            else:  # If status is changing *to* stock affecting (e.g., from 'Returned' to 'Issued')
                pass  # potential_new_total_issued is already correct, as old_quantity wasn't "issued" before.

            # Now add the new quantity of this item
            potential_new_total_issued += issued_item.quantity

            if potential_new_total_issued > total_physical_stock:
                flash(
                    f'Cannot update. Not enough physical stock for the selected item and quantity ({issued_item.quantity}). '
                    f'Current total issued for this item would be {potential_new_total_issued}, exceeding '
                    f'physical stock of {total_physical_stock}.',
                    'danger')
                db.session.rollback()
                return redirect(ADMIN + ISSUED_ITEMS_LIST)

        # If status is changing from stock-affecting to non-stock-affecting (e.g., 'Issued' to 'Returned')
        # no stock check is needed, as stock is conceptually being "returned".
        # This is implicitly handled because `will_be_stock_affecting` would be False.

        db.session.commit()
        flash('Issued item updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating issued item: {str(e)}', 'danger')
        print(f"Error updating issued item: {e}")  # For debugging
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Soft Delete Issued Item ---
@admin.route(ISSUED_ITEMS_DELETE + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_issued_item(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    try:
        # Prevent soft-deleting if status is 'Issued' and not returned
        # and also for 'Pending' or 'Requested' items that are still active.
        if issued_item.status in ['Issued', 'Pending', 'Requested'] and issued_item.return_date is None:
            flash(
                f'Item "{issued_item.item.item_name}" is currently {issued_item.status.lower()} and not returned/resolved. Please return or resolve it first.',
                'warning')
            return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issued_item.is_deleted = True
        issued_item.deleted_at = datetime.now()
        db.session.commit()
        flash('Issued item archived successfully!', 'success')  # Changed message to 'archived'
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving issued item: {str(e)}', 'danger')
        print(f"Error archiving issued item: {e}")
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Restore Deleted Issued Item ---
@admin.route(ISSUED_ITEMS_RESTORE + "/<int:issued_item_id>", methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_issued_item(current_user, issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    try:
        # Before restoring, if its status is 'Issued'/'Pending'/'Requested' and no return date,
        # ensure there's enough stock to bring it back to active state affecting stock.
        stock_affecting_statuses = ['Issued', 'Pending', 'Requested']
        if issued_item.status in stock_affecting_statuses and issued_item.return_date is None:
            total_physical_stock = get_total_stock_quantity(issued_item.item_id)
            total_issued_excluding_this = get_total_issued_quantity(
                issued_item.item_id)  # This already excludes deleted ones

            available_after_others = total_physical_stock - total_issued_excluding_this

            if issued_item.quantity > available_after_others:
                flash(
                    f'Cannot restore. Not enough physical stock to reactivate {issued_item.quantity} units of this item. '
                    f'Only {available_after_others} units are currently available.',
                    'danger')
                return redirect(ADMIN + ISSUED_ITEMS_LIST)

        issued_item.is_deleted = False
        issued_item.deleted_at = None
        db.session.commit()
        flash('Issued item restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring issued item: {str(e)}', 'danger')
        print(f"Error restoring issued item: {e}")
    return redirect(ADMIN + ISSUED_ITEMS_LIST)


# --- Export Issued Items ---
@admin.route(ISSUED_ITEMS_EXPORT + "/<string:file_format>", methods=['GET'])
def export_issued_items(file_format):
    issued_items = IssuedItem.query.filter_by(is_deleted=False).all()  # Export only active items

    data = []
    for item in issued_items:
        data.append({
            "ID": item.id,
            "Item Name": item.item.item_name if item.item else 'N/A',  # Use item_name
            "Issued To Name": item.issued_to_name,
            "Issued To User ID": item.issued_to_user_id or 'N/A',
            "User Type": item.user_type,
            "Issued By": item.issued_by,
            "Issue Date": item.issue_date.strftime('%Y-%m-%d') if item.issue_date else 'N/A',
            "Return Date": item.return_date.strftime('%Y-%m-%d') if item.return_date else 'N/A',
            "Quantity": item.quantity,
            "Status": item.status,
            "Note": item.note or 'N/A',
            "Requested By": item.requested_by or 'N/A',  # New field
            "Approved By": item.approved_by or 'N/A',  # New field
            "Department": item.department or 'N/A',  # New field
            "Purpose": item.purpose or 'N/A',  # New field
            "Created At": item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else '',
            "Updated At": item.updated_at.strftime('%Y-%m-%d %H:%M:%S') if item.updated_at else ''
        })

    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    download_filename = f'issued_items_export_{current_time}'

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
            df.to_excel(writer, index=False, sheet_name='Issued Items')
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
        normal_style.fontSize = 7  # Slightly smaller font for more columns
        normal_style.leading = 8

        title_text = "Issued Items Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        # Filter out 'ID' for PDF, and potentially 'Issued To User ID' if it's too technical
        # Include new fields in PDF export
        header_cols = [col for col in df.columns.tolist() if col not in ['ID', 'Issued To User ID']]
        pdf_data.append([Paragraph(col, styles['h3']) for col in header_cols])

        for index, row in df.iterrows():
            row_data = []
            for col_name in header_cols:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter
        LEFT_MARGIN = 0.4 * inch  # Smaller margins for more space
        RIGHT_MARGIN = 0.4 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(header_cols)
        # Distribute width evenly, or you can create custom widths if some columns are wider
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        if pdf_data[1:]:  # Check if there are data rows beyond the header
            table = Table(pdf_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),  # Smaller header font too
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('TOPPADDING', (0, 0), (-1, 0), 5),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No issued items data available for this report.", normal_style))

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
        return redirect(ADMIN + ISSUED_ITEMS_LIST)
