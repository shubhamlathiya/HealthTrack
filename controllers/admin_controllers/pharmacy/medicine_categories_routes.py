# Categories Routes
from datetime import datetime

from flask import render_template, request, flash, redirect

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import PHARMACY_MEDICINE_CATEGORIES, PHARMACY_MEDICINE_COMPANIES, \
    PHARMACY_MEDICINE_ADD_CATEGORIES, PHARMACY_MEDICINE_ADD_COMPANIES, PHARMACY_MEDICINE_EDIT_CATEGORIES, \
    PHARMACY_MEDICINE_DELETE_CATEGORIES, PHARMACY_MEDICINE_RESTORE_CATEGORIES, PHARMACY_MEDICINE_EDIT_COMPANIES, \
    PHARMACY_MEDICINE_DELETE_COMPANIES, PHARMACY_MEDICINE_RESTORE_COMPANIES, ADMIN
from middleware.auth_middleware import token_required
from models.medicineModel import MedicineCategory, MedicineCompany
from utils.config import db


@admin.route(PHARMACY_MEDICINE_CATEGORIES, methods=['GET'], endpoint='medicine-categories')
@token_required
def medicine_categories(current_user):
    categories = MedicineCategory.query.filter_by(is_deleted=0).order_by(MedicineCategory.name).all()
    archived_categories = MedicineCategory.query.filter_by(is_deleted=1).order_by(
        MedicineCategory.deleted_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_categories.html', categories=categories,
                           archived_categories=archived_categories)


@admin.route(PHARMACY_MEDICINE_ADD_CATEGORIES, methods=['POST'], endpoint='medicine-categories/add')
@token_required
def add_medicine_category(current_user):
    try:
        category = MedicineCategory(
            name=request.form.get('name'),
            description=request.form.get('description')
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_CATEGORIES)


@admin.route(PHARMACY_MEDICINE_EDIT_CATEGORIES + '/<int:id>', methods=['POST'],
             endpoint='medicine-categories/<int:id>/edit')
@token_required
def edit_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        db.session.commit()
        flash('Category updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_CATEGORIES)


@admin.route(PHARMACY_MEDICINE_DELETE_CATEGORIES + '/<int:id>', methods=['POST'])
@token_required
def delete_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_CATEGORIES)


@admin.route(PHARMACY_MEDICINE_RESTORE_CATEGORIES + '/<int:id>', methods=['POST'],
             endpoint='medicine-categories/<int:id>/restore')
@token_required
def restore_medicine_category(current_user, id):
    category = MedicineCategory.query.get_or_404(id)
    try:
        category.is_deleted = False
        category.deleted_at = None
        db.session.commit()
        flash('Category restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_CATEGORIES)


# Companies Routes
@admin.route(PHARMACY_MEDICINE_COMPANIES, methods=['GET'], endpoint='medicine-companies')
@token_required
def medicine_companies(current_user):
    companies = MedicineCompany.query.filter_by(is_deleted=0).order_by(MedicineCompany.name).all()
    archived_companies = MedicineCompany.query.filter_by(is_deleted=1).order_by(MedicineCompany.deleted_at.desc()).all()
    return render_template('admin_templates/pharmacy/medicine_companies.html', companies=companies,
                           archived_companies=archived_companies)


@admin.route(PHARMACY_MEDICINE_ADD_COMPANIES, methods=['POST'], endpoint='medicine-companies/add')
@token_required
def add_medicine_company(current_user):
    try:
        company = MedicineCompany(
            name=request.form.get('name'),
            address=request.form.get('address'),
            contact_number=request.form.get('contact_number'),
            email=request.form.get('email'),
            website=request.form.get('website')
        )
        db.session.add(company)
        db.session.commit()
        flash('Company added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_COMPANIES)


@admin.route(PHARMACY_MEDICINE_EDIT_COMPANIES + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/edit')
@token_required
def edit_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.name = request.form.get('name')
        company.address = request.form.get('address')
        company.contact_number = request.form.get('contact_number')
        company.email = request.form.get('email')
        company.website = request.form.get('website')
        db.session.commit()
        flash('Company updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_COMPANIES)


@admin.route(PHARMACY_MEDICINE_DELETE_COMPANIES + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/delete')
@token_required
def delete_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.is_deleted = True
        company.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Company deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting company: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_COMPANIES)


@admin.route(PHARMACY_MEDICINE_RESTORE_COMPANIES + '/<int:id>', methods=['POST'],
             endpoint='medicine-companies/<int:id>/restore')
@token_required
def restore_medicine_company(current_user, id):
    company = MedicineCompany.query.get_or_404(id)
    try:
        company.is_deleted = False
        company.deleted_at = None

        db.session.commit()
        flash('Category restored successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring category: {str(e)}', 'danger')
    return redirect(ADMIN + PHARMACY_MEDICINE_COMPANIES)
