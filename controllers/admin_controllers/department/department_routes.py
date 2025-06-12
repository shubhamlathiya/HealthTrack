import io
import traceback
from datetime import datetime

import pandas as pd
from flask import render_template, request, flash, redirect, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import DEPARTMENT_LIST, DEPARTMENT_ADD_DEPARTMENT, ADMIN, \
    DEPARTMENT_EDIT_DEPARTMENT, DEPARTMENT_DELETE_DEPARTMENT, DEPARTMENT_RESTORE_DEPARTMENT, DEPARTMENT_MANAGE_HEADS, \
    DEPARTMENT_EXPORT, DEPARTMENT_IMPORT, DEPARTMENT_IMPORT_SAMPLE
from middleware.auth_middleware import token_required
from models.departmentModel import Department
from models.userModel import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(DEPARTMENT_LIST, methods=['GET'], endpoint='departments-list')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def department_list(current_user):
    """
    Renders the list of active and archived departments.
    Retrieves associated doctors and rooms for display.
    """
    departments = Department.query.filter_by(is_deleted=0).order_by(Department.name.asc()).all()
    archived_departments = Department.query.filter_by(is_deleted=1).order_by(Department.deleted_at.desc()).all()

    # Get associated doctors and rooms (assuming these relationships are defined in your models)
    all_doctors = []
    for department in departments:
        # Assuming 'assignments' is a relationship to a model that links doctors to departments
        # And 'current_status' is an attribute on the assignment indicating active links
        if hasattr(department, 'assignments'):
            for assignment in department.assignments:
                if str(assignment.current_status) == 'Active':
                    all_doctors.append(assignment.doctor)

    # Assuming 'rooms' is a relationship on the Department model
    # This check prevents errors if departments list is empty or rooms relationship is not defined
    all_rooms = [room for dept in departments for room in dept.rooms] if departments and hasattr(departments[0],
                                                                                                 'rooms') else []

    return render_template("admin_templates/department/departments-list.html",
                           departments=departments,
                           archived_departments=archived_departments,
                           doctors=all_doctors,
                           rooms=all_rooms,
                           ADMIN=ADMIN,
                           DEPARTMENT_ADD_DEPARTMENT=DEPARTMENT_ADD_DEPARTMENT,
                           DEPARTMENT_EDIT_DEPARTMENT=DEPARTMENT_EDIT_DEPARTMENT,
                           DEPARTMENT_DELETE_DEPARTMENT=DEPARTMENT_DELETE_DEPARTMENT,
                           DEPARTMENT_RESTORE_DEPARTMENT=DEPARTMENT_RESTORE_DEPARTMENT,
                           DEPARTMENT_MANAGE_HEADS=DEPARTMENT_MANAGE_HEADS,
                           DEPARTMENT_EXPORT=DEPARTMENT_EXPORT,
                           DEPARTMENT_IMPORT=DEPARTMENT_IMPORT,
                           DEPARTMENT_IMPORT_SAMPLE=DEPARTMENT_IMPORT_SAMPLE
                           )


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['GET'], endpoint='add-department-form')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_department_form(current_user):
    """
    Renders the form for adding a new department.
    """
    return render_template("admin_templates/department/add-department.html",
                           ADMIN=ADMIN,
                           DEPARTMENT_ADD_DEPARTMENT=DEPARTMENT_ADD_DEPARTMENT)


@admin.route(DEPARTMENT_ADD_DEPARTMENT, methods=['POST'], endpoint='add-department')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_department(current_user):
    """
    Handles the submission of the add department form.
    Adds a new department to the database after checking for existing names and emails.
    """
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        # Convert status string from form to boolean
        status_str = request.form.get('status')
        status = status_str.lower() == 'active' if status_str else False
        message = request.form.get('message')

        # Input validation
        if not name or not email or not phone:
            flash('Name, Email, and Phone are required fields.', 'danger')
            return redirect(ADMIN + DEPARTMENT_LIST)

        # Check if a department with this name already exists and is not soft-deleted
        existing_department_by_name = Department.query.filter(
            Department.name == name,
            Department.is_deleted == False
        ).first()

        if existing_department_by_name:
            flash(f'Department "{name}" already exists. Please choose a different name.', 'warning')
            return redirect(ADMIN + DEPARTMENT_LIST)

        # Check if a department with this email already exists and is not soft-deleted
        existing_department_by_email = Department.query.filter(
            Department.email == email,
            Department.is_deleted == False
        ).first()

        if existing_department_by_email:
            flash(f'Department with email "{email}" already exists. Email must be unique.', 'warning')
            return redirect(ADMIN + DEPARTMENT_LIST)

        # Create new department
        new_dept = Department(
            name=name,
            email=email,
            phone=phone,
            status=status,  # Use the converted boolean status
            message=message if message else None  # Store None if message is empty
        )

        db.session.add(new_dept)
        db.session.commit()
        flash('Department added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error adding department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_EDIT_DEPARTMENT + '/<int:id>', methods=['POST'], endpoint='edit-department')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_department(current_user, id):
    """
    Handles the submission of the edit department form.
    Updates an existing department's information.
    """
    try:
        department = Department.query.get_or_404(id)

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        # Convert status string from form to boolean
        status_str = request.form.get('status')
        status = status_str.lower() == 'active' if status_str else False
        message = request.form.get('message')

        # Input validation
        if not name or not email or not phone:
            flash('Name, Email, and Phone are required fields.', 'danger')
            return redirect(ADMIN + DEPARTMENT_LIST)

        # Check for unique email (excluding the current department being edited)
        existing_department_by_email = Department.query.filter(
            Department.email == email,
            Department.id != id,
            Department.is_deleted == False
        ).first()

        if existing_department_by_email:
            flash(f'Department with email "{email}" already exists. Email must be unique.', 'warning')
            return redirect(ADMIN + DEPARTMENT_LIST)

        # Update department data
        department.name = name
        department.email = email
        department.phone = phone
        department.status = status  # Use the converted boolean status
        department.message = message if message else None  # Store None if message is empty
        department.updated_at = datetime.utcnow()

        db.session.commit()

        flash('Department updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error updating department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_DELETE_DEPARTMENT + '/<int:id>', methods=['POST'], endpoint='delete-department')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_department(current_user, id):
    """
    Performs a soft delete on a department by setting is_deleted to True
    and recording the deletion timestamp.
    """
    try:
        department = Department.query.get_or_404(id)
        department.is_deleted = True
        department.deleted_at = datetime.utcnow()
        db.session.commit()

        flash('Department deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error deleting department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_RESTORE_DEPARTMENT + '/<int:id>', methods=['POST'], endpoint='restore-department')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_department(current_user, id):
    """
    Restores a soft-deleted department by setting is_deleted to False
    and clearing the deletion timestamp.
    """
    try:
        department = Department.query.get_or_404(id)
        department.is_deleted = False
        department.deleted_at = None
        db.session.commit()

        flash('Department restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error restoring department: {str(e)}', 'danger')
    return redirect(ADMIN + DEPARTMENT_LIST)


@admin.route(DEPARTMENT_EXPORT + '/<format>', methods=['GET'], endpoint='export-departments')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_departments(current_user, format):
    """
    Exports department data to CSV, Excel, or PDF format.
    """
    departments = Department.query.filter_by(is_deleted=0).order_by(Department.name.asc()).all()

    data = []
    for dept in departments:
        data.append({
            'Name': dept.name,
            'Email': dept.email,
            'Phone': dept.phone,
            'Status': 'Active' if dept.status else 'Inactive',  # Convert boolean status to string
            'Message': dept.message if dept.message else '',  # Ensure message is not None for export
            'Created At': dept.created_at.strftime('%Y-%m-%d %H:%M') if dept.created_at else '',
            'Updated At': dept.updated_at.strftime('%Y-%m-%d %H:%M') if dept.updated_at else ''
        })

    df = pd.DataFrame(data)

    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='departments.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Departments')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='departments.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()

        elements = []
        title_text = "Hospital Departments Report"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Prepare PDF data for table
        pdf_data = []
        # Add header row
        header_style = styles['h3']
        header_style.alignment = 1  # Center align header
        pdf_data.append([Paragraph(col, header_style) for col in df.columns.tolist()])

        # Define normal style for table content
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 9
        normal_style.leading = 10

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        # Calculate dynamic column widths for PDF
        PAGE_WIDTH, PAGE_HEIGHT = letter
        AVAILABLE_WIDTH = PAGE_WIDTH - doc.leftMargin - doc.rightMargin

        # Adjust column widths based on the content or number of columns
        num_columns = len(df.columns)
        # Distribute width proportionally, giving more to message/name if applicable
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        # Example: Give more width to 'Name' and 'Message' if they exist
        if 'Name' in df.columns:
            name_idx = df.columns.get_loc('Name')
            col_widths[name_idx] = AVAILABLE_WIDTH * 0.2
        if 'Message' in df.columns:
            message_idx = df.columns.get_loc('Message')
            col_widths[message_idx] = AVAILABLE_WIDTH * 0.25  # Adjust as needed

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
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertically center content
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='departments.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + DEPARTMENT_LIST)


SAMPLE_EXCEL_STRUCTURE_DEPARTMENTS = [
    {
        "Name": "Cardiology",
        "Email": "cardio@hospital.com",
        "Phone": "123-456-7890",
        "Status": "Active",  # Example for boolean status
        "Message": "Specializes in heart diseases."
    },
    {
        "Name": "Pediatrics",
        "Email": "peds@hospital.com",
        "Phone": "987-654-3210",
        "Status": "Inactive",
        "Message": "Focuses on child health."
    }
]


@admin.route(DEPARTMENT_IMPORT_SAMPLE, methods=['GET'], endpoint='download-department-import-sample')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_sample_import_file(current_user):
    """
    Provides a sample Excel file for importing departments.
    """
    df = pd.DataFrame(SAMPLE_EXCEL_STRUCTURE_DEPARTMENTS)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Departments')
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING DEPARTMENTS:",
            "",
            "1. Use the 'Departments' sheet for your data.",
            "2. Required columns: 'Name', 'Email', 'Phone', 'Status'.",
            "3. Optional columns: 'Message'.",
            "4. For 'Status' column, use 'Active' or 'Inactive'.",
            "5. 'Email' must be unique for each department.",
            "6. Do not modify the column headers.",
            "7. Remove this 'Instructions' sheet before importing.",
            "8. Save the file as .xlsx format."
        ]

        for row, line in enumerate(instructions):
            worksheet.write(row, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_departments.xlsx'
    )


@admin.route(DEPARTMENT_IMPORT, methods=['POST'], endpoint="import-departments")
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_departments(current_user):
    """
    Handles the import of department data from an uploaded Excel file.
    """
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + DEPARTMENT_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + DEPARTMENT_LIST)

    if not allowed_file(file.filename):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + DEPARTMENT_LIST)

    try:
        df = pd.read_excel(file)

        # Define required columns based on the Department model's nullable=False fields
        required_columns = ['Name', 'Email', 'Phone', 'Status']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}. Please refer to the sample file.', 'error')
            return redirect(ADMIN + DEPARTMENT_LIST)

        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        for index, row in df.iterrows():
            row_num = index + 2  # For user-friendly row numbering (Excel starts at 1, headers at 1)
            try:
                # Get data and handle potential NaN/empty values from Excel
                name = row.get('Name')
                email = row.get('Email')
                phone = row.get('Phone')
                status_str = row.get('Status')
                message = row.get('Message')

                # Convert pandas NaN to None or empty string, and strip whitespace
                name = str(name).strip() if pd.notna(name) else None
                email = str(email).strip() if pd.notna(email) else None
                phone = str(phone).strip() if pd.notna(phone) else None
                message = str(message).strip() if pd.notna(message) else None

                # Convert status string to boolean
                status = status_str.strip().lower() == 'active' if pd.notna(status_str) else False

                # Basic validation for required fields
                if not name or not email or not phone:
                    flash(f'Row {row_num}: Skipping - Name, Email, or Phone is missing/invalid.', 'warning')
                    error_count += 1
                    continue

                # Check for existing department by email (unique constraint)
                existing_by_email = Department.query.filter_by(email=email).first()

                if existing_by_email:
                    if overwrite:
                        # Check if the existing department is soft-deleted; if so, restore it upon overwrite
                        if existing_by_email.is_deleted:
                            existing_by_email.is_deleted = False
                            existing_by_email.deleted_at = None
                            flash(
                                f'Row {row_num}: Department "{name}" (email: {email}) was archived and has been restored and updated.',
                                'info')

                        # Update existing department
                        existing_by_email.name = name
                        existing_by_email.phone = phone
                        existing_by_email.status = status
                        existing_by_email.message = message
                        existing_by_email.updated_at = datetime.utcnow()
                        db.session.commit()
                        success_count += 1
                    else:
                        flash(
                            f'Row {row_num}: Department with email "{email}" already exists and overwrite is OFF. Skipping.',
                            'warning')
                        error_count += 1
                else:
                    # Check for existing department by name (to warn, not necessarily block if email is unique)
                    existing_by_name = Department.query.filter(
                        Department.name == name,
                        Department.is_deleted == False
                    ).first()
                    if existing_by_name:
                        flash(
                            f'Row {row_num}: Warning: Department with name "{name}" already exists, but a new entry will be created as email is unique. Consider reviewing for duplicates.',
                            'warning')

                    # Create new department
                    new_department = Department(
                        name=name,
                        email=email,
                        phone=phone,
                        status=status,
                        message=message,
                    )
                    db.session.add(new_department)
                    db.session.commit()
                    success_count += 1

            except Exception as e:
                db.session.rollback()  # Rollback the current row's transaction if it failed
                # Use a more robust way to show name even if it's None
                display_name = name if name else 'Unknown Department'
                flash(
                    f'Row {row_num}: Error processing data for "{display_name}" (email: {email if email else "N/A"}): {str(e)}',
                    'danger')
                error_count += 1
                traceback.print_exc()  # Print full traceback for debugging

        flash(f'Department import completed: {success_count} successful, {error_count} failed.',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}. Ensure it is a valid Excel file and follows the sample structure.',
              'error')
        traceback.print_exc()  # Print full traceback for file-level errors

    return redirect(ADMIN + DEPARTMENT_LIST)