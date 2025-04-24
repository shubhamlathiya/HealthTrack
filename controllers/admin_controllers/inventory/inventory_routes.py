from flask import render_template, request, redirect, flash
from datetime import datetime
from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INVENTORY_ITEM_STOCK_LIST, ADMIN, INVENTORY_ADD_ITEM, \
    INVENTORY_EDIT_ITEM, INVENTORY_DELETE_ITEM, INVENTORY_RESTORE_ITEM
from models.InventoryItemModel import Item
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
