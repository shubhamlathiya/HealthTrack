# Operation Category Routes
import traceback

from flask import request, flash, redirect, render_template

from controllers.constant.setupPathConstant import OPERATION_CATEGORIES_ADD, OPERATIONS_ADD, \
    OPERATION_CATEGORIES_DELETE, OPERATION_CATEGORIES_EDIT, OPERATION_CATEGORIES_LIST, OPERATIONS_LIST, SETUP, \
    OPERATIONS_EDIT, OPERATIONS_DELETE
from controllers.setup_controllers import setup
from middleware.auth_middleware import token_required
from models import UserRole
from models.setupModel import Operation, OperationCategory
from utils.config import db


@setup.route('/operations', methods=['GET'], endpoint='setup')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def list_operation(current_user):
    operations = Operation.query.all()
    operation_categories = OperationCategory.query.all()
    return render_template('setup_templates/operationtheatre.html',
                           operation_categories=operation_categories,
                           operations=operations,
                           SETUP = SETUP,
                           OPERATION_CATEGORIES_ADD=OPERATION_CATEGORIES_ADD,
                           OPERATIONS_ADD=OPERATIONS_ADD
                           )


@setup.route(OPERATION_CATEGORIES_ADD, methods=['POST'], endpoint='add_operation_category')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_operation_category(current_user):
    try:

        category_name = request.form.get('name')

        existing_category = OperationCategory.query.filter(
            OperationCategory.name == category_name
        ).first()

        if existing_category:
            flash(f'Operation category "{category_name}" already exists.', 'warning')
            return redirect(SETUP + OPERATIONS_LIST)

        category = OperationCategory(
            name=category_name
        )
        db.session.add(category)
        db.session.commit()
        flash('Operation Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error adding operation category: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)


@setup.route(OPERATION_CATEGORIES_EDIT + '/<int:id>', methods=['POST'],
             endpoint='edit_operation_category')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_operation_category(current_user, id):
    category = OperationCategory.query.get_or_404(id)
    try:
        category.name = request.form.get('name')
        db.session.commit()
        flash('Operation Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating operation category: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)


@setup.route(OPERATION_CATEGORIES_DELETE + '/<int:id>', methods=['POST'],
             endpoint="delete_operation_category")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_operation_category(current_user, id):
    category = OperationCategory.query.get_or_404(id)
    try:
        # Check if category has any operations before deleting
        if category.operations:
            flash('Cannot delete category with associated operations. Please reassign or delete operations first.',
                  'warning')
            return redirect(SETUP + OPERATIONS_LIST)

        db.session.delete(category)
        db.session.commit()
        flash('Operation Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting operation category: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)


# Operation Routes
@setup.route(OPERATIONS_ADD, methods=['POST'], endpoint='add_operation')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_operation(current_user):
    try:
        operation_name = request.form.get('name')
        description = request.form.get('description')
        category_id = request.form.get('category_id')

        existing_operation = Operation.query.filter(
            Operation.name == operation_name
        ).first()

        if existing_operation:
            flash(f'Operation "{operation_name}" already exists.', 'warning')
            return redirect(SETUP + OPERATIONS_LIST)

        operation = Operation(
            name=operation_name,
            description=description,
            category_id=category_id if category_id else None
        )
        db.session.add(operation)
        db.session.commit()
        flash('Operation added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error adding operation: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)


@setup.route(OPERATIONS_EDIT + '/<int:id>', methods=['POST'],
             endpoint='edit_operation')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_operation(current_user, id):
    operation = Operation.query.get_or_404(id)
    try:
        operation.name = request.form.get('name')
        operation.description = request.form.get('description')
        operation.category_id = request.form.get('category_id')
        db.session.commit()
        flash('Operation updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating operation: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)


@setup.route(OPERATIONS_DELETE + '/<int:id>', methods=['POST'],
             endpoint="delete_operation")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_operation(current_user, id):
    operation = Operation.query.get_or_404(id)
    try:
        db.session.delete(operation)
        db.session.commit()
        flash('Operation deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting operation: {str(e)}', 'danger')
    return redirect(SETUP + OPERATIONS_LIST)
