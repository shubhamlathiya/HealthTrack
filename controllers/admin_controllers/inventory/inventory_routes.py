from flask import render_template, request, redirect, url_for, flash
from datetime import datetime

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INVENTORY_ITEM_STOCK_LIST, ADMIN, INVENTORY_ADD_ITEM, \
    INVENTORY_EDIT_ITEM, INVENTORY_DELETE_ITEM, INVENTORY_RESTORE_ITEM, INVENTORY_ISSUED_ITEM, \
    INVENTORY_ADD_ISSUED_ITEM, INVENTORY_EDIT_ISSUED_ITEM, INVENTORY_DELETE_ISSUED_ITEM, INVENTORY_RESTORE_ISSUED_ITEM, \
    INVENTORY_RETURN_ISSUED_ITEM
from models.InventoryItemModel import Item, IssuedItem
from utils.config import db



# Item Stock List Routes
@admin.route(INVENTORY_ITEM_STOCK_LIST, methods=['GET'], endpoint='inventory_item_stock_list')
def item_stock_list():
    active_items = Item.query.filter_by(is_deleted=False).all()
    deleted_items = Item.query.filter_by(is_deleted=True).all()
    return render_template('admin_templates/inventory/item_stock_list.html', items=active_items,
                           deleted_items=deleted_items)


@admin.route(INVENTORY_ADD_ITEM, methods=['POST'], endpoint='inventory_item_add')
def add_item():
    try:
        item = Item(
            item_name=request.form['item_name'],
            category=request.form['category'],
            quantity=int(request.form['quantity']),
            purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date(),
            price=float(request.form['price']),
            description=request.form.get('description', '')
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEM_STOCK_LIST)


@admin.route(INVENTORY_EDIT_ITEM + '/<int:id>', methods=['POST'], endpoint='inventory_item_edit')
def edit_item(id):
    try:
        item = Item.query.get_or_404(id)
        item.item_name = request.form['item_name']
        item.category = request.form['category']
        item.quantity = int(request.form['quantity'])
        item.purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date()
        item.price = float(request.form['price'])
        item.description = request.form.get('description', '')
        db.session.commit()
        flash('Item updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEM_STOCK_LIST)


@admin.route(INVENTORY_DELETE_ITEM + '/<int:id>', methods=['POST'], endpoint='inventory_item_delete')
def delete_item(id):
    try:
        item = Item.query.get_or_404(id)
        item.is_deleted = True
        item.deleted_at = datetime.now()
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEM_STOCK_LIST)


@admin.route(INVENTORY_RESTORE_ITEM + '/<int:id>', methods=['POST'], endpoint='inventory_item_restore')
def restore_item(id):
    try:
        item = Item.query.get_or_404(id)
        item.is_deleted = False
        item.deleted_at = None
        db.session.commit()
        flash('Item restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ITEM_STOCK_LIST)


# Issued Items Routes
@admin.route(INVENTORY_ISSUED_ITEM, methods=['GET'], endpoint='inventory_item_issued')
def issued_items():
    active_issued_items = IssuedItem.query.filter_by(is_deleted=False).all()
    deleted_issued_items = IssuedItem.query.filter_by(is_deleted=True).all()
    active_items = Item.query.filter_by(is_deleted=False).all()
    return render_template('admin_templates/inventory/issued_items.html', issued_items=active_issued_items,
                           deleted_issued_items=deleted_issued_items,
                           items=active_items)


@admin.route(INVENTORY_ADD_ISSUED_ITEM, methods=['POST'], endpoint="inventory_add_item_issued")
def add_issue_item():
    try:
        item_id = int(request.form['item_id'])
        quantity = int(request.form['quantity'])

        # Check if item exists and has enough quantity
        item = Item.query.get_or_404(item_id)
        if item.quantity < quantity:
            flash('Not enough quantity in stock!', 'danger')
            return redirect(url_for('inventory.issued_items'))

        # Create issued item
        issued_item = IssuedItem(
            item_id=item_id,
            issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date(),
            return_date=datetime.strptime(request.form['return_date'], '%Y-%m-%d').date() if request.form[
                'return_date'] else None,
            issued_to=request.form['issued_to'],
            quantity=quantity,
            status='Issued'
        )

        # Update item quantity
        item.quantity -= quantity

        db.session.add(issued_item)
        db.session.commit()
        flash('Item issued successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error issuing item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)


@admin.route(INVENTORY_EDIT_ISSUED_ITEM + '/<int:id>', methods=['POST'], endpoint="edit_issued_item")
def edit_issued_item(id):
    try:
        issued_item = IssuedItem.query.get_or_404(id)
        original_quantity = issued_item.quantity
        original_status = issued_item.status
        item = issued_item.item  # The inventory item being issued

        # Handle return case
        if 'return' in request.form:
            issued_item.status = 'Returned'
            issued_item.return_date = datetime.now().date()
            # Return quantity to stock only if it wasn't already returned
            if original_status != 'Returned':
                item.quantity += issued_item.quantity
            db.session.commit()
            flash('Item marked as returned!', 'success')
            return redirect(ADMIN + INVENTORY_ISSUED_ITEM)

        # Get form data
        new_quantity = int(request.form['quantity'])
        new_status = request.form['status']
        issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date()
        return_date = datetime.strptime(request.form['return_date'], '%Y-%m-%d').date() if request.form[
            'return_date'] else None
        issued_to = request.form['issued_to']

        # Quantity change logic
        if new_quantity != original_quantity:
            quantity_diff = new_quantity - original_quantity

            # Check if we have enough stock for the increase
            if quantity_diff > 0 and item.quantity < quantity_diff:
                flash('Not enough items in stock to increase the issued quantity!', 'danger')
                return redirect(ADMIN + INVENTORY_ISSUED_ITEM)

            # Update stock based on quantity change
            if original_status != 'Returned':
                item.quantity -= quantity_diff
            else:
                # If item was returned, we need to handle differently
                if new_status == 'Returned':
                    # Just adjust the stock by the difference
                    item.quantity -= quantity_diff
                else:
                    # Changing from Returned to Issued - deduct full new quantity
                    item.quantity -= new_quantity

        # Status change logic
        if original_status != new_status:
            if original_status == 'Returned' and new_status == 'Issued':
                # Changing from returned to issued - deduct from stock
                if item.quantity < new_quantity:
                    flash('Not enough items in stock to re-issue this quantity!', 'danger')
                    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)
                item.quantity -= new_quantity
            elif original_status == 'Issued' and new_status == 'Returned':
                # Changing from issued to returned - add to stock
                item.quantity += new_quantity

        # Update issued item record
        issued_item.issue_date = issue_date
        issued_item.return_date = return_date
        issued_item.issued_to = issued_to
        issued_item.quantity = new_quantity
        issued_item.status = new_status

        db.session.commit()
        flash('Issued item updated successfully!', 'success')

    except ValueError as e:
        db.session.rollback()
        flash('Invalid data format provided!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating issued item: {str(e)}', 'danger')

    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)


@admin.route(INVENTORY_RETURN_ISSUED_ITEM + '/<int:issued_item_id>', methods=['POST'], endpoint='inventory_item_return')
def return_item(issued_item_id):
    issued_item = IssuedItem.query.get_or_404(issued_item_id)
    try:
        # Update issued item status
        issued_item.status = 'Returned'
        issued_item.return_date = datetime.now().date()

        # Return quantity to stock
        item = Item.query.get(issued_item.item_id)
        item.quantity += issued_item.quantity

        db.session.commit()
        flash('Item successfully returned to stock!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error returning item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)


@admin.route(INVENTORY_DELETE_ISSUED_ITEM + '/<int:id>', methods=['POST'], endpoint="delete_issued_item")
def delete_issued_item(id):
    try:
        issued_item = IssuedItem.query.get_or_404(id)
        issued_item.is_deleted = True
        issued_item.deleted_at = datetime.now()

        # If item wasn't returned, return quantity to stock
        if issued_item.status != 'Returned':
            issued_item.item.quantity += issued_item.quantity

        db.session.commit()
        flash('Issued item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting issued item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)


@admin.route(INVENTORY_RESTORE_ISSUED_ITEM + '/<int:id>', methods=['POST'], endpoint="restore")
def restore_issued_item(id):
    try:
        issued_item = IssuedItem.query.get_or_404(id)
        issued_item.is_deleted = False
        issued_item.deleted_at = None

        # If restoring, deduct quantity from stock if not returned
        if issued_item.status != 'Returned':
            issued_item.item.quantity -= issued_item.quantity

        db.session.commit()
        flash('Issued item restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring issued item: {str(e)}', 'danger')
    return redirect(ADMIN + INVENTORY_ISSUED_ITEM)
