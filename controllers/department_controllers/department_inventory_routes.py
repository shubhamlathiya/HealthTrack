from datetime import datetime

from flask import request, flash, redirect, render_template, session

from controllers.constant.departmentPathConstant import DEPARTMENT, INVENTORY_DEPARTMENT_REQUESTS, \
    INVENTORY_REQUEST_RETURN, INVENTORY_CANCEL_REQUEST
from controllers.department_controllers import department
from middleware.auth_middleware import token_required
from models import Department
from models.InventoryItemModel import Item, IssuedItem
from utils.config import db


@department.route(INVENTORY_DEPARTMENT_REQUESTS, methods=['GET', 'POST'], endpoint='department_requests')
@token_required
def department_requests(current_user):
    # Get current department (assuming it's stored in session or current_user)
    department_id = session.get('department_id')
    print(department_id)
    current_department = Department.query.filter_by(id=department_id).first()

    if request.method == 'POST':
        try:
            item_id = int(request.form['item_id'])
            quantity = int(request.form['quantity'])
            purpose = request.form['purpose']
            need_by_date = request.form.get('need_by_date')

            item = Item.query.get_or_404(item_id)

            # Validate available quantity
            if item.quantity < quantity:
                flash(f'Not enough quantity available. Only {item.quantity} {item.item_name} in stock.', 'danger')
                return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)

            # Create a request
            request_item = IssuedItem(
                item_id=item_id,
                issue_date=datetime.now().date(),
                return_date=datetime.strptime(need_by_date, '%Y-%m-%d').date() if need_by_date else None,
                issued_to=current_department.id,  # Issued to department
                quantity=quantity,
                status='Requested',
                requested_by=current_user,
                department=current_department.id,
                purpose=purpose
            )

            db.session.add(request_item)
            db.session.commit()
            flash('Item request submitted for approval!', 'success')
        except ValueError as e:
            db.session.rollback()
            flash('Invalid data format provided!', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting request: {str(e)}', 'danger')
        return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)

    # GET request - prepare all data for the template
    available_items = Item.query.filter_by(is_deleted=False).all()

    all_requests = IssuedItem.query.filter(
        IssuedItem.department == current_department.id,
        IssuedItem.is_deleted == False
    ).order_by(IssuedItem.updated_at.desc()).all()

    return render_template('department_templates/inventory/department_requests.html',
                           all_requests=all_requests,
                           available_items=available_items,
                           DEPARTMENT=DEPARTMENT,
                           INVENTORY_DEPARTMENT_REQUESTS=INVENTORY_DEPARTMENT_REQUESTS)


@department.route(INVENTORY_REQUEST_RETURN + '/<int:item_id>', methods=['POST'], endpoint='request_item_return')
@token_required
def request_item_return(current_user, item_id):
    try:
        issued_item = IssuedItem.query.get_or_404(item_id)
        return_notes = request.form.get('return_notes', '')

        # Verify the item belongs to the current department
        if issued_item.department != str(session.get('department_id')):
            flash('You are not authorized to return this item', 'danger')
            return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)

        # Update the item status (or create a return request depending on your workflow)
        issued_item.status = 'Returned'
        issued_item.return_date = datetime.now().date()
        issued_item.updated_at = datetime.now()

        item = Item.query.get(issued_item.item_id)
        item.quantity += issued_item.quantity

        db.session.commit()
        flash('Return request submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting return request: {str(e)}', 'danger')

    return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)


@department.route(INVENTORY_CANCEL_REQUEST + '/<int:request_id>', methods=['POST'], endpoint='cancel_request')
@token_required
def cancel_request(current_user, request_id):
    try:
        request_item = IssuedItem.query.get_or_404(request_id)
        cancel_reason = request.form.get('cancel_reason', '')

        # Verify the request belongs to the current department
        if request_item.department != str(session.get('department_id')):
            flash('You are not authorized to cancel this request', 'danger')
            return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)

        # Only allow cancellation of pending requests
        if request_item.status != 'Requested':
            flash('Only pending requests can be cancelled', 'warning')
            return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)

        # Mark as cancelled
        request_item.status = 'Cancelled'
        request_item.updated_at = datetime.now()

        db.session.commit()
        flash('Request cancelled successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling request: {str(e)}', 'danger')

    return redirect(DEPARTMENT + INVENTORY_DEPARTMENT_REQUESTS)
