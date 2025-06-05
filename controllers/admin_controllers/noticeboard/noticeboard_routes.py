import os
from datetime import datetime

from flask import flash, render_template, redirect, request
from werkzeug.utils import secure_filename

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, NOTICEBOARD_ADD_NOTICE, NOTICEBOARD, NOTICEBOARD_EDIT_NOTICE, \
    NOTICEBOARD_DELETE_NOTICE, NOTICEBOARD_RESTORE_NOTICE
from middleware.auth_middleware import token_required
from models import UserRole, Department
from models.noticeboardModel import Notice
from utils.config import db

UPLOAD_FOLDER = 'static/uploads/notices'
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin.route(NOTICEBOARD, methods=['GET'], endpoint="notice_board")
def notice_board():
    # Get active notices
    notices = Notice.query.filter_by(is_deleted=False).order_by(Notice.post_date.desc()).all()
    deleted_notices = Notice.query.filter_by(is_deleted=True).order_by(Notice.post_date.desc()).all()

    # Get all roles and departments for forms
    all_roles = [role for role in UserRole]
    all_departments = Department.query.all()

    return render_template('admin_templates/noticeboard/noticeboard.html',
                           notices=notices,
                           all_roles=all_roles,
                           all_departments=all_departments,
                           deleted_notices = deleted_notices,
                           ADMIN=ADMIN,
                           NOTICEBOARD_ADD_NOTICE=NOTICEBOARD_ADD_NOTICE,
                           NOTICEBOARD_EDIT_NOTICE=NOTICEBOARD_EDIT_NOTICE,
                           NOTICEBOARD_DELETE_NOTICE=NOTICEBOARD_DELETE_NOTICE,
                           NOTICEBOARD_RESTORE_NOTICE=NOTICEBOARD_RESTORE_NOTICE)


@admin.route(NOTICEBOARD_ADD_NOTICE, methods=['POST'], endpoint="notice_board_add")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_notice(current_user):
    try:
        # Get form data
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority')
        expiry_date = request.form.get('expiry_date')
        is_active = request.form.get('is_active') == 'on'
        target_type = request.form.get('target_type')

        # Validate required fields
        if not all([title, content, priority, target_type]):
            flash('Please fill all required fields', 'danger')
            return redirect(ADMIN + NOTICEBOARD)

        # Handle file upload
        attachment = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                attachment = filename

        # Create new notice
        new_notice = Notice(
            title=title,
            content=content,
            posted_by=current_user,  # Changed from current_user to current_user.id
            post_date=datetime.utcnow(),
            expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d') if expiry_date else None,
            priority=priority,
            is_active=is_active,
            attachment=attachment,
            target_type=target_type.rstrip('s')  # Convert 'roles' to 'role' and 'departments' to 'department'
        )

        # Set target type
        if target_type == 'roles':
            roles = request.form.getlist('roles')
            new_notice.roles = roles if roles else None  # Store as JSON array directly
        else:
            departments = request.form.getlist('departments')
            if departments:
                for dept_id in departments:
                    dept = Department.query.get(dept_id)
                    if dept:
                        new_notice.departments.append(dept)
            else:
                flash('Please select at least one department', 'warning')
                return redirect(ADMIN + NOTICEBOARD)

        db.session.add(new_notice)
        db.session.commit()

        flash('Notice added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding notice: {str(e)}', 'danger')

    return redirect(ADMIN + NOTICEBOARD)


@admin.route(NOTICEBOARD_EDIT_NOTICE + '/<int:notice_id>', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_notice(current_user,notice_id):
    notice = Notice.query.get_or_404(notice_id)

    try:
        # Update basic fields
        notice.title = request.form.get('title')
        notice.content = request.form.get('content')
        notice.priority = request.form.get('priority')
        notice.is_active = request.form.get('is_active') == 'on'
        target_type = request.form.get('target_type')
        notice.target_type = target_type.rstrip('s')  # Convert to singular

        # Update expiry date
        expiry_date = request.form.get('expiry_date')
        notice.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d') if expiry_date else None

        # Handle file upload/removal
        if request.form.get('remove_attachment') == '1':
            if notice.attachment:
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, notice.attachment))
                except Exception as e:
                    flash(f"Error removing attachment: {str(e)}","danger")
            notice.attachment = None
        elif 'attachment' in request.files:
            file = request.files['attachment']
            if file and allowed_file(file.filename):
                # Remove old file if exists
                if notice.attachment:
                    try:
                        os.remove(os.path.join(UPLOAD_FOLDER, notice.attachment))
                    except Exception as e:
                        flash(f"Error removing old attachment: {str(e)}" , "danger")

                # Save new file
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                notice.attachment = filename

        # Update target type
        if target_type == 'roles':
            # Clear departments and set roles
            notice.departments = []
            roles = request.form.getlist('roles')
            notice.roles = roles if roles else None  # Store as JSON array
            if not roles:
                flash('Please select at least one role', 'warning')
                return redirect(ADMIN + NOTICEBOARD)
        else:
            # Clear roles and set departments
            notice.roles = None
            departments = request.form.getlist('departments')
            notice.departments = []
            if departments:
                for dept_id in departments:
                    dept = Department.query.get(dept_id)
                    if dept:
                        notice.departments.append(dept)
            else:
                flash('Please select at least one department', 'warning')
                return redirect(ADMIN + NOTICEBOARD)

        notice.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Notice updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating notice: {str(e)}', 'danger')

    return redirect(ADMIN + NOTICEBOARD)


@admin.route(NOTICEBOARD_DELETE_NOTICE + '/<int:notice_id>', methods=['POST'])
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)

    try:
        notice.is_deleted = True
        notice.deleted_at = datetime.utcnow()
        db.session.commit()

        flash('Notice deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting notice: {str(e)}', 'danger')

    return redirect(ADMIN + NOTICEBOARD)


@admin.route(NOTICEBOARD_RESTORE_NOTICE + '/<int:notice_id>', methods=['POST'])
def restore_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)

    try:
        notice.is_deleted = False
        notice.deleted_at = None
        db.session.commit()

        flash('Notice restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring notice: {str(e)}', 'danger')

    return redirect(ADMIN + NOTICEBOARD)
