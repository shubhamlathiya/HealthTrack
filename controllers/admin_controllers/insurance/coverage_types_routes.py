from datetime import datetime
from sqlite3 import IntegrityError

from flask import render_template, flash, request, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import INSURANCE_CONVERAGE_TYPE, INSURANCE_ADD_CONVERAGE_TYPE, ADMIN, \
    INSURANCE_EDIT_CONVERAGE_TYPE, INSURANCE_DELETE_CONVERAGE_TYPE, INSURANCE_RESTORE_CONVERAGE_TYPE
from middleware.auth_middleware import token_required
from models.insuranceProviderModel import CoverageType
from models.userModel import UserRole
from utils.config import db


# Coverage Type Management
@admin.route(INSURANCE_CONVERAGE_TYPE, methods=['GET'], endpoint='coverage_types')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def list_coverage_types(current_user):
    try:
        coverage_types = CoverageType.query \
            .filter_by(is_deleted=False) \
            .order_by(CoverageType.name) \
            .all()

        deleted_coverage_types = CoverageType.query \
            .filter_by(is_deleted=True) \
            .order_by(CoverageType.deleted_at.desc()) \
            .all()

        return render_template(
            'admin_templates/insurance/coverage_types.html',
            coverage_types=coverage_types,
            deleted_coverage_types=deleted_coverage_types,
            ADMIN=ADMIN,
            INSURANCE_ADD_CONVERAGE_TYPE=INSURANCE_ADD_CONVERAGE_TYPE,
            INSURANCE_EDIT_CONVERAGE_TYPE=INSURANCE_EDIT_CONVERAGE_TYPE,
            INSURANCE_DELETE_CONVERAGE_TYPE=INSURANCE_DELETE_CONVERAGE_TYPE,
            INSURANCE_RESTORE_CONVERAGE_TYPE=INSURANCE_RESTORE_CONVERAGE_TYPE
        )
    except Exception as e:
        flash(f'Error loading coverage types: {str(e)}', 'danger')
        return render_template(
            'admin_templates/insurance/coverage_types.html',
            coverage_types=[],
            deleted_coverage_types=[],
            ADMIN=ADMIN,
            INSURANCE_ADD_CONVERAGE_TYPE=INSURANCE_ADD_CONVERAGE_TYPE,
            INSURANCE_EDIT_CONVERAGE_TYPE=INSURANCE_EDIT_CONVERAGE_TYPE,
            INSURANCE_DELETE_CONVERAGE_TYPE=INSURANCE_DELETE_CONVERAGE_TYPE,
            INSURANCE_RESTORE_CONVERAGE_TYPE=INSURANCE_RESTORE_CONVERAGE_TYPE
        )


@admin.route(INSURANCE_ADD_CONVERAGE_TYPE, methods=['POST'], endpoint="add_coverage_type")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_coverage_type(current_user):
    try:
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Name is required', 'danger')
            return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)

        # Check if coverage type already exists
        if CoverageType.query.filter_by(name=name, is_deleted=False).first():
            flash('Coverage type with this name already exists', 'danger')
            return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)

        coverage = CoverageType(
            name=name,
            description=description
        )

        db.session.add(coverage)
        db.session.commit()
        flash('Coverage type added successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Database integrity error. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding coverage type: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)


@admin.route(INSURANCE_EDIT_CONVERAGE_TYPE + '/<int:coverage_id>', methods=['POST'], endpoint='edit_coverage_type')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_coverage_type(current_user, coverage_id):
    coverage = CoverageType.query.get_or_404(coverage_id)

    try:
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Name is required', 'danger')
            return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)

        # Check if another coverage type has this name
        existing_coverage = CoverageType.query.filter(
            CoverageType.name == name,
            CoverageType.id != coverage_id,
            CoverageType.is_deleted == False
        ).first()

        if existing_coverage:
            flash('Another coverage type with this name already exists', 'danger')
            return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)

        coverage.name = name
        coverage.description = description
        coverage.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Coverage type updated successfully!', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Database integrity error. Please try again.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating coverage type: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)


@admin.route(INSURANCE_DELETE_CONVERAGE_TYPE + '/<int:coverage_id>', methods=['POST'], endpoint='delete_coverage_type')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_coverage_type(current_user, coverage_id):
    coverage = CoverageType.query.get_or_404(coverage_id)

    try:
        # Check if any providers are using this coverage type
        if coverage.providers:
            flash('Cannot delete coverage type as it is assigned to one or more providers', 'danger')
        else:
            # Soft delete the coverage type
            coverage.is_deleted = True
            coverage.deleted_at = datetime.utcnow()
            db.session.commit()
            flash('Coverage type deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting coverage type: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)


@admin.route(INSURANCE_RESTORE_CONVERAGE_TYPE + '/<int:coverage_id>', methods=['POST'],
             endpoint="restore_coverage_type")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_coverage_type(current_user, coverage_id):
    coverage = CoverageType.query.filter_by(id=coverage_id, is_deleted=True).first_or_404()

    try:
        # Restore the coverage type
        coverage.is_deleted = False
        coverage.deleted_at = None
        db.session.commit()
        flash('Coverage type restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring coverage type: {str(e)}', 'danger')

    return redirect(ADMIN + INSURANCE_CONVERAGE_TYPE)
