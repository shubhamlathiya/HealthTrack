import io
import os
import traceback
from datetime import datetime

import pandas as pd
from flask import render_template, request
from flask import send_file, flash, redirect
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import ADMIN, DOCTOR_IMPORT_SAMPLE
from controllers.constant.adminPathConstant import DOCTOR_ADD_DOCTOR, DOCTOR_LIST, DOCTOR_EDIT_DOCTOR, \
    DOCTOR_DELETE_DOCTOR, DOCTOR_RESTORE_DOCTOR, DOCTOR_EXPORT, \
    DOCTOR_IMPORT
from middleware.auth_middleware import token_required
from models.doctorModel import Availability, Doctor
from models.userModel import User, UserRole
from utils.config import db
from utils.create_new_patient import create_new_doctor

# --- Configuration ---
UPLOAD_FOLDER = 'static/uploads/profile_pictures'  # Base folder for profile pictures
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # PDF is not typical for profile pictures, removed it


def allowed_file(filename):
    """Checks if the uploaded file's extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Helper Function for Availability Parsing ---
def parse_availability_from_form(form_data, doctor_id):
    """
    Parses availability data from form submission.
    Returns a list of Availability objects.
    """
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    availability_records = []
    for i, day in enumerate(days_of_week, start=1):
        from_time = form_data.get(f'd{i}')
        to_time = form_data.get(f'd{i}X')

        if from_time and to_time and from_time != 'None' and to_time != 'None':
            availability_records.append(
                Availability(
                    day_of_week=i,
                    from_time=from_time,
                    to_time=to_time,
                    doctor_id=doctor_id
                )
            )
    return availability_records


# --- Doctor List Route ---
@admin.route(DOCTOR_LIST, methods=['GET'], endpoint='doctor_list')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def doctor_list(current_user):
    """
    Renders the list of active and archived doctors.
    Includes associated department names for active doctors.
    """
    # Query all doctors along with their user information
    doctors = Doctor.query.join(User).filter(Doctor.is_deleted == False).order_by(Doctor.created_at.desc()).all()
    archived_doctors = Doctor.query.join(User).filter(Doctor.is_deleted == True).order_by(
        Doctor.deleted_at.desc()).all()

    for doctor in doctors:
        doctor.department_names = [
            assignment.department.name
            for assignment in doctor.department_assignments
            if assignment.current_status == 'Active'
        ]

    for doctor in archived_doctors:
        doctor.department_names = [
            assignment.department.name
            for assignment in doctor.department_assignments
            if assignment.current_status == 'Active'
        ]

    return render_template(
        "admin_templates/doctor/doctor_list.html",
        doctors=doctors,
        archived_doctors=archived_doctors,  # Pass archived doctors
        ADMIN=ADMIN,
        DOCTOR_ADD_DOCTOR=DOCTOR_ADD_DOCTOR,
        DOCTOR_EDIT_DOCTOR=DOCTOR_EDIT_DOCTOR,  # For linking to edit page
        DOCTOR_DELETE_DOCTOR=DOCTOR_DELETE_DOCTOR,  # For delete actions
        DOCTOR_RESTORE_DOCTOR=DOCTOR_RESTORE_DOCTOR,  # For restore actions
        DOCTOR_EXPORT=DOCTOR_EXPORT,
        DOCTOR_IMPORT=DOCTOR_IMPORT,
        DOCTOR_IMPORT_SAMPLE=DOCTOR_IMPORT_SAMPLE
    )


# --- Add Doctor Form (GET) ---
@admin.route(DOCTOR_ADD_DOCTOR, methods=['GET'], endpoint='add_doctor_form')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def add_doctor_form(current_user):
    """
    Renders the form for adding a new doctor.
    """
    return render_template("admin_templates/doctor/add-doctors.html",
                           ADMIN=ADMIN,
                           DOCTOR_ADD_DOCTOR=DOCTOR_ADD_DOCTOR)


# --- Register Doctor (POST) ---
@admin.route(DOCTOR_ADD_DOCTOR, methods=['POST'], endpoint='register_doctor')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def register_doctor(current_user):
    """
    Handles the registration of a new doctor, including user creation,
    doctor profile, profile picture upload, and availability.
    """
    try:
        data = request.form

        doctor_data = {
            'email': data.get('a5'),
            'first_name': data.get('a1'),
            'last_name': data.get('a2'),
            'age': int(data.get('a3')),  # Ensure type conversion as expected by helper
            'gender': data.get('selectGenderOptions'),
            'phone': data.get('a6'),
            'qualification': data.get('a8'),
            'designation': data.get('a9'),
            'blood_group': data.get('a10'),
            'address': data.get('a11'),
            'bio': data.get('bio', '')
        }

        new_doctor = create_new_doctor(doctor_data)
        # 3. Handle profile picture upload
        profile_pic_path = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{new_doctor.id}_{filename}"  # Make filename unique
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                profile_pic_path = file_path.replace('\\', '/')  # Store web-friendly path

        new_doctor.profile_picture = profile_pic_path

        # 4. Add availability records
        availability_records = parse_availability_from_form(data, new_doctor.id)
        db.session.add_all(availability_records)

        db.session.commit()  # Final commit

        flash("Doctor registered successfully!", 'success')
        return redirect(ADMIN + DOCTOR_LIST)

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error registering doctor: {str(e)}', 'danger')
        return redirect(ADMIN + DOCTOR_ADD_DOCTOR)


# --- Edit Doctor Form (GET) ---
@admin.route(DOCTOR_EDIT_DOCTOR + '/<int:id>', methods=['GET'], endpoint='edit_doctor_form')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_doctor_form(current_user, id):
    """
    Renders the form for editing an existing doctor's details.
    """
    doctor = Doctor.query.get_or_404(id)

    # Prepare availability data for the template
    doctor_availability_map = {}
    for avail in doctor.availabilities:
        # Convert day_of_week int back to string day name for template lookup
        # Assuming day_of_week is 1 for Sunday, 2 for Monday, etc.
        day_name = {
            1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday',
            5: 'Thursday', 6: 'Friday', 7: 'Saturday'
        }.get(avail.day_of_week)
        if day_name:
            doctor_availability_map[day_name] = {'from': avail.from_time, 'to': avail.to_time}

    return render_template("admin_templates/doctor/edit-doctors.html",
                           doctor=doctor,
                           doctor_availability_map=doctor_availability_map,
                           ADMIN=ADMIN,
                           DOCTOR_EDIT_DOCTOR=DOCTOR_EDIT_DOCTOR)



@admin.route(DOCTOR_EDIT_DOCTOR + '/<int:id>', methods=['POST'], endpoint='edit_doctor')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def edit_doctor(current_user, id):
    """
    Handles the submission of the edited doctor's details.
    Updates doctor profile, user email/password (if provided), and availability.
    """
    try:
        doctor = Doctor.query.get_or_404(id)
        user = User.query.get_or_404(doctor.user_id)
        data = request.form

        # Update User details
        new_email = data.get('a5')
        new_password = data.get('u2')

        if new_email and new_email != user.email:
            if User.query.filter(User.email == new_email, User.id != user.id).first():
                flash(f'Email {new_email} is already in use by another user.', 'warning')
                return redirect(ADMIN + DOCTOR_EDIT_DOCTOR + f'/{id}')
            user.email = new_email

        if new_password:
            # Only update password if a new one is provided and it's different/not empty
            if not check_password_hash(user.password, new_password):  # Avoid rehashing if same password
                user.password = generate_password_hash(new_password)

        # Update Doctor details
        doctor.first_name = data.get('a1')
        doctor.last_name = data.get('a2')
        doctor.age = int(data.get('a3'))
        doctor.gender = data.get('selectGenderOptions')
        doctor.phone = data.get('a6')
        doctor.qualification = data.get('a8')
        doctor.designation = data.get('a9')
        doctor.blood_group = data.get('a10')
        doctor.address = data.get('a11')
        doctor.bio = data.get('bio', '')
        doctor.updated_at = datetime.utcnow()

        # Handle profile picture update
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                # Delete old picture if it exists
                if doctor.profile_picture and os.path.exists(doctor.profile_picture):
                    os.remove(doctor.profile_picture)

                filename = secure_filename(file.filename)
                unique_filename = f"{doctor.id}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                doctor.profile_picture = file_path.replace('\\', '/')
            elif file.filename == '':  # If file input is empty, and user wants to clear existing
                if 'clear_profile_picture' in data and data['clear_profile_picture'] == 'on':
                    if doctor.profile_picture and os.path.exists(doctor.profile_picture):
                        os.remove(doctor.profile_picture)
                    doctor.profile_picture = None
        elif 'clear_profile_picture' in data and data[
            'clear_profile_picture'] == 'on':  # Clear if checkbox checked and no new file uploaded
            if doctor.profile_picture and os.path.exists(doctor.profile_picture):
                os.remove(doctor.profile_picture)
            doctor.profile_picture = None

        # Update availability records
        # First, delete existing availabilities for this doctor
        Availability.query.filter_by(doctor_id=doctor.id).delete()
        db.session.flush()  # Ensure deletion happens before adding new ones

        # Then, add new availability records from the form
        availability_records = parse_availability_from_form(data, doctor.id)
        db.session.add_all(availability_records)

        db.session.commit()
        flash('Doctor updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error updating doctor: {str(e)}', 'danger')
    return redirect(ADMIN + DOCTOR_LIST)


# --- Delete Doctor (Soft Delete) ---
@admin.route(DOCTOR_DELETE_DOCTOR + '/<int:id>', methods=['POST'], endpoint='delete_doctor')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def delete_doctor(current_user, id):
    """
    Performs a soft delete on a doctor and their associated user.
    """
    try:
        doctor = Doctor.query.get_or_404(id)
        user = User.query.get_or_404(doctor.user_id)

        doctor.is_deleted = True
        doctor.deleted_at = datetime.utcnow()
        user.status = False  # Deactivate user account
        user.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Doctor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error deleting doctor: {str(e)}', 'danger')
    return redirect(ADMIN + DOCTOR_LIST)


# --- Restore Doctor ---
@admin.route(DOCTOR_RESTORE_DOCTOR + '/<int:id>', methods=['POST'], endpoint='restore_doctor')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def restore_doctor(current_user, id):
    """
    Restores a soft-deleted doctor and their associated user.
    """
    try:
        doctor = Doctor.query.get_or_404(id)
        user = User.query.get_or_404(doctor.user_id)

        doctor.is_deleted = False
        doctor.deleted_at = None
        user.status = True  # Reactivate user account
        user.deleted_at = None

        db.session.commit()
        flash('Doctor restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        flash(f'Error restoring doctor: {str(e)}', 'danger')
    return redirect(ADMIN + DOCTOR_LIST)


days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


# --- Export Doctors ---
@admin.route(DOCTOR_EXPORT + '/<format>', methods=['GET'], endpoint='export_doctors')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def export_doctors(current_user, format):
    """
    Exports doctor data to CSV, Excel, or PDF format.
    """
    doctors = Doctor.query.join(User).filter(Doctor.is_deleted == False).order_by(Doctor.first_name).all()

    data = []
    for doctor in doctors:
        doctor_data = {
            'First Name': doctor.first_name,
            'Last Name': doctor.last_name,
            'Email': doctor.user.email,  # Access email via the user relationship
            'Age': doctor.age,
            'Gender': doctor.gender,
            'Phone': doctor.phone,
            'Qualification': doctor.qualification,
            'Designation': doctor.designation,
            'Blood Group': doctor.blood_group,
            'Address': doctor.address,
            'Bio': doctor.bio
        }

        # Initialize availability for all days as 'Not working'
        for day_name in days:  # Use the 'days' list defined globally or locally
            doctor_data[f'{day_name} From'] = 'Not working'
            doctor_data[f'{day_name} To'] = 'Not working'

        # Populate actual availability
        for avail in doctor.availabilities:
            # Convert day_of_week to int before using it as an index
            day_index = int(avail.day_of_week) - 1  # Convert to int and then adjust to 0-indexed
            if 0 <= day_index < len(days):  # Ensure index is within bounds
                day_name = days[day_index]
                doctor_data[f'{day_name} From'] = avail.from_time
                doctor_data[f'{day_name} To'] = avail.to_time

        data.append(doctor_data)

    df = pd.DataFrame(data)

    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name='doctors.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Doctors')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='doctors.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                                topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        styles = getSampleStyleSheet()

        elements = []
        title_text = "Doctor Roster Report"
        title = Paragraph(title_text, styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        pdf_data = []
        header_style = styles['h4']  # Slightly smaller header for PDF
        header_style.alignment = 1  # Center align header
        pdf_data.append([Paragraph(col, header_style) for col in df.columns.tolist()])

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 7  # Smaller font size for more data
        normal_style.leading = 8  # Line spacing

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = letter
        AVAILABLE_WIDTH = PAGE_WIDTH - doc.leftMargin - doc.rightMargin

        num_columns = len(df.columns)
        # Dynamic column width calculation - adjust weights as needed
        col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        # Custom adjustments for specific columns (e.g., make Bio/Address wider)
        if 'First Name' in df.columns: col_widths[df.columns.get_loc('First Name')] = AVAILABLE_WIDTH * 0.08
        if 'Last Name' in df.columns: col_widths[df.columns.get_loc('Last Name')] = AVAILABLE_WIDTH * 0.08
        if 'Email' in df.columns: col_widths[df.columns.get_loc('Email')] = AVAILABLE_WIDTH * 0.12
        if 'Phone' in df.columns: col_widths[df.columns.get_loc('Phone')] = AVAILABLE_WIDTH * 0.08
        if 'Qualification' in df.columns: col_widths[df.columns.get_loc('Qualification')] = AVAILABLE_WIDTH * 0.1
        if 'Designation' in df.columns: col_widths[df.columns.get_loc('Designation')] = AVAILABLE_WIDTH * 0.1
        if 'Address' in df.columns: col_widths[df.columns.get_loc('Address')] = AVAILABLE_WIDTH * 0.15
        if 'Bio' in df.columns: col_widths[df.columns.get_loc('Bio')] = AVAILABLE_WIDTH * 0.15
        if 'Availability' in df.columns: col_widths[df.columns.get_loc('Availability')] = AVAILABLE_WIDTH * 0.15
        # Ensure all columns have a width defined, fallback to equal if not specifically set
        total_assigned_width = sum(col_widths)
        if total_assigned_width > AVAILABLE_WIDTH:
            # Scale down if sum exceeds available width
            col_widths = [w * (AVAILABLE_WIDTH / total_assigned_width) for w in col_widths]

        table = Table(pdf_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align text to top
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='doctors.pdf'
        )
    flash('Invalid export format', 'error')
    return redirect(ADMIN + DOCTOR_LIST)


# --- Define the precise allowed times (matching your import logic) ---
# This list is used for instructions and potentially for auto-filling examples
ALLOWED_AVAILABILITY_TIMES = [
    '07:00 AM', '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM',
    '12:00 PM', '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM'
]

# --- Define the structure of the sample Excel file with example data ---
# This dictionary now uses the ALLOWED_AVAILABILITY_TIMES for examples.
SAMPLE_EXCEL_STRUCTURE_DOCTORS = {
    'First Name': ['John', 'Jane'],
    'Last Name': ['Doe', 'Smith'],
    'Email': ['john.doe@example.com', 'jane.smith@example.com'],
    'Password': ['StrongP@ss1', 'SecureP@ss2'],
    'Age': [45, 38],
    'Gender': ['Male', 'Female'],
    'Phone': ['+919876543210', '+918765432109'],
    'Qualification': ['MD', 'MBBS, DCH'],
    'Designation': ['Cardiologist', 'Pediatrician'],
    'Blood Group': ['O+', 'A-'],
    'Address': ['123 Main St, Anytown', '456 Oak Ave, Somewhere'],
    'Bio': ['Experienced heart specialist.', 'Loves working with kids.'],
    'Sunday From': ['Not working', ALLOWED_AVAILABILITY_TIMES[0]],  # Example: Not working
    'Sunday To': ['Not working', ALLOWED_AVAILABILITY_TIMES[4]],
    'Monday From': [ALLOWED_AVAILABILITY_TIMES[0], 'Not working'],  # Example: 07:00 AM
    'Monday To': [ALLOWED_AVAILABILITY_TIMES[-1], 'Not working'],
    'Tuesday From': [ALLOWED_AVAILABILITY_TIMES[1], ALLOWED_AVAILABILITY_TIMES[2]],
    'Tuesday To': [ALLOWED_AVAILABILITY_TIMES[5], ALLOWED_AVAILABILITY_TIMES[6]],
    'Wednesday From': [ALLOWED_AVAILABILITY_TIMES[0], ALLOWED_AVAILABILITY_TIMES[0]],
    'Wednesday To': [ALLOWED_AVAILABILITY_TIMES[7], ALLOWED_AVAILABILITY_TIMES[7]],
    'Thursday From': [ALLOWED_AVAILABILITY_TIMES[2], ALLOWED_AVAILABILITY_TIMES[1]],
    'Thursday To': [ALLOWED_AVAILABILITY_TIMES[8], ALLOWED_AVAILABILITY_TIMES[5]],
    'Friday From': [ALLOWED_AVAILABILITY_TIMES[0], ALLOWED_AVAILABILITY_TIMES[0]],
    'Friday To': [ALLOWED_AVAILABILITY_TIMES[-1], ALLOWED_AVAILABILITY_TIMES[-1]],
    'Saturday From': ['Not working', 'Not working'],  # Example: Not working
    'Saturday To': ['Not working', 'Not working']
}


# --- Download Sample Import File ---
@admin.route(DOCTOR_IMPORT_SAMPLE, methods=['GET'], endpoint='download_doctor_import_sample')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def download_doctor_import_sample(current_user):
    """
    Provides a sample Excel file for importing doctor data,
    with updated instructions and example data matching strict time formats.
    """
    df = pd.DataFrame(SAMPLE_EXCEL_STRUCTURE_DOCTORS)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Doctors Data')
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')

        instructions = [
            "INSTRUCTIONS FOR IMPORTING DOCTORS:",
            "",
            "1. Use the 'Doctors Data' sheet for your data.",
            "2. Required columns must be filled: 'First Name', 'Last Name', 'Email', 'Password', 'Age', 'Gender', 'Phone', 'Qualification', 'Designation', 'Blood Group', 'Address'.",
            "3. Optional columns: 'Bio', and all 'Day From'/'Day To' columns (e.g., 'Monday From', 'Monday To').",
            "4. For availability, **strictly use these time formats** for 'From' and 'To' columns:",
            f"   {', '.join(ALLOWED_AVAILABILITY_TIMES)}",  # Dynamically list allowed times
            "   OR use 'Not working' (case-insensitive) if the doctor is not available.",
            "5. If a doctor is 'Not working' for a day, both 'From' and 'To' for that day must be 'Not working'.",
            "6. 'Email' must be unique for each doctor and will be used as their login username.",
            "7. Passwords provided will be hashed and stored securely.",
            "8. Do not modify the column headers.",
            "9. Remove this 'Instructions' sheet before importing to avoid import errors.",
            "10. Save the file as .xlsx format."
        ]

        # Add a note about the exact time format in instructions
        worksheet.write(3, 0, "4. For availability, **strictly use these time formats** for 'From' and 'To' columns:")
        worksheet.write(4, 0, f"   {', '.join(ALLOWED_AVAILABILITY_TIMES)}")
        worksheet.write(5, 0, "   OR use 'Not working' (case-insensitive) if the doctor is not available.")
        worksheet.write(6, 0,
                        "5. If a doctor is 'Not working' for a day, both 'From' and 'To' for that day must be 'Not working'.")

        # Adjust subsequent instruction indices based on the new lines added
        # We need to write the instructions one by one
        current_row = 0
        for line in instructions:
            worksheet.write(current_row, 0, line)
            current_row += 1

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_doctors.xlsx'
    )


# --- Import Doctors ---
@admin.route(DOCTOR_IMPORT, methods=['POST'], endpoint='import_doctors')
@token_required(allowed_roles=[UserRole.ADMIN.name])
def import_doctors(current_user):
    """
    Handles the bulk import of doctor data from an uploaded Excel file.
    Optimized to use the `create_new_doctor` helper function for new entries
    and enforce strict time format validation for availability.
    """
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(ADMIN + DOCTOR_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(ADMIN + DOCTOR_LIST)

    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Only Excel files (.xlsx, .xls) are allowed', 'error')
        return redirect(ADMIN + DOCTOR_LIST)

    try:
        df = pd.read_excel(file)

        required_columns = [
            'First Name', 'Last Name', 'Email', 'Password', 'Age', 'Gender',
            'Phone', 'Qualification', 'Designation', 'Blood Group', 'Address'
        ]

        # Define allowed time formats as a set for efficient lookup
        # The 'None' value for 'Not working' is handled explicitly in the validation
        allowed_times = {
            '07:00 AM', '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM',
            '12:00 PM', '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM'
        }

        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing required columns: {", ".join(missing)}. Please check your Excel file and sample.', 'danger')
            return redirect(ADMIN + DOCTOR_LIST)

        success_count = 0
        error_count = 0
        overwrite = request.form.get('overwrite') == 'on'

        availability_cols_map = {
            'Sunday': {'from': 'Sunday From', 'to': 'Sunday To'},
            'Monday': {'from': 'Monday From', 'to': 'Monday To'},
            'Tuesday': {'from': 'Tuesday From', 'to': 'Tuesday To'},
            'Wednesday': {'from': 'Wednesday From', 'to': 'Wednesday To'},
            'Thursday': {'from': 'Thursday From', 'to': 'Thursday To'},
            'Friday': {'from': 'Friday From', 'to': 'Friday To'},
            'Saturday': {'from': 'Saturday From', 'to': 'Saturday To'}
        }
        days_of_week_map = {
            'Sunday': 1, 'Monday': 2, 'Tuesday': 3, 'Wednesday': 4,
            'Thursday': 5, 'Friday': 6, 'Saturday': 7
        }

        for index, row in df.iterrows():
            row_num = index + 2
            try:
                doctor_data = {
                    'first_name': str(row.get('First Name', '')).strip(),
                    'last_name': str(row.get('Last Name', '')).strip(),
                    'email': str(row.get('Email', '')).strip().lower(),
                    'password': str(row.get('Password', '')).strip(),
                    'age': int(row.get('Age')) if pd.notna(row.get('Age')) else None,
                    'gender': str(row.get('Gender', '')).strip(),
                    'phone': str(row.get('Phone', '')).strip(),
                    'qualification': str(row.get('Qualification', '')).strip(),
                    'designation': str(row.get('Designation', '')).strip(),
                    'blood_group': str(row.get('Blood Group', '')).strip(),
                    'address': str(row.get('Address', '')).strip(),
                    'bio': str(row.get('Bio', '')).strip() if pd.notna(row.get('Bio')) else ''
                }

                # Ensure essential fields are not None after stripping
                if not all([doctor_data['first_name'], doctor_data['last_name'], doctor_data['email'],
                            doctor_data['password'], doctor_data['age'], doctor_data['gender'],
                            doctor_data['phone'], doctor_data['qualification'], doctor_data['designation'],
                            doctor_data['address']]):
                    flash(
                        f'Row {row_num}: Skipping - Missing required data (e.g., First Name, Email, Password, Age, Gender, Phone, Qualification, Designation, Address).',
                        'warning')
                    error_count += 1
                    continue

                existing_user = User.query.filter_by(email=doctor_data['email']).first()
                target_doctor = None

                if existing_user:
                    if overwrite:
                        if existing_user.role != UserRole.DOCTOR:
                            flash(
                                f'Row {row_num}: Cannot overwrite user "{doctor_data["email"]}" - not a doctor role. Skipping.',
                                'danger')
                            error_count += 1
                            continue

                        if not existing_user.status and existing_user.deleted_at:
                            existing_user.status = True
                            existing_user.deleted_at = None
                            flash(
                                f'Row {row_num}: User account for "{doctor_data["email"]}" was inactive and has been restored.',
                                'info')

                        if doctor_data['password'] and not check_password_hash(existing_user.password,
                                                                               doctor_data['password']):
                            existing_user.password = generate_password_hash(doctor_data['password'])

                        existing_doctor = Doctor.query.filter_by(user_id=existing_user.id).first()
                        if not existing_doctor:
                            flash(
                                f'Row {row_num}: Found user "{doctor_data["email"]}" but no associated doctor profile. Creating one.',
                                'warning')
                            new_doctor_from_helper, _, _ = create_new_doctor(doctor_data)
                            target_doctor = new_doctor_from_helper
                        else:
                            existing_doctor.first_name = doctor_data['first_name']
                            existing_doctor.last_name = doctor_data['last_name']
                            existing_doctor.age = doctor_data['age']
                            existing_doctor.gender = doctor_data['gender']
                            existing_doctor.phone = doctor_data['phone']
                            existing_doctor.qualification = doctor_data['qualification']
                            existing_doctor.designation = doctor_data['designation']
                            existing_doctor.blood_group = doctor_data['blood_group']
                            existing_doctor.address = doctor_data['address']
                            existing_doctor.bio = doctor_data['bio']
                            existing_doctor.updated_at = datetime.utcnow()

                            if existing_doctor.is_deleted:
                                existing_doctor.is_deleted = False
                                existing_doctor.deleted_at = None
                                flash(
                                    f'Row {row_num}: Doctor profile for "{doctor_data["email"]}" was archived and has been restored.',
                                    'info')
                            target_doctor = existing_doctor

                        db.session.flush()
                        success_count += 1

                    else:
                        flash(
                            f'Row {row_num}: Doctor with email "{doctor_data["email"]}" already exists and overwrite is OFF. Skipping.',
                            'warning')
                        error_count += 1
                        continue
                else:
                    new_doctor = create_new_doctor(doctor_data)
                    target_doctor = new_doctor
                    success_count += 1

                # --- Availability Handling for both new and updated doctors ---
                if target_doctor:
                    Availability.query.filter_by(doctor_id=target_doctor.id).delete()
                    db.session.flush()

                    imported_availabilities = []
                    for day_name, cols in availability_cols_map.items():
                        from_time_str = str(row.get(cols['from'], '')).strip()
                        to_time_str = str(row.get(cols['to'], '')).strip()

                        # --- NEW VALIDATION LOGIC ---
                        # Check if times are valid or 'not working' (case-insensitive)
                        is_from_valid = (from_time_str.lower() == 'not working' or from_time_str in allowed_times)
                        is_to_valid = (to_time_str.lower() == 'not working' or to_time_str in allowed_times)

                        if not is_from_valid or not is_to_valid:
                            raise ValueError(
                                f"Invalid time format for {day_name} ({from_time_str} to {to_time_str}). "
                                f"Expected formats: {', '.join(allowed_times)} or 'Not working'."
                            )

                        # Only add if both times are not 'not working'
                        if from_time_str.lower() != 'not working' and to_time_str.lower() != 'not working':
                            # Ensure both from_time and to_time are provided if not 'not working'
                            if not from_time_str or not to_time_str:
                                raise ValueError(
                                    f"Missing 'From' or 'To' time for {day_name}. Both must be provided if not 'Not working'."
                                )
                            imported_availabilities.append(
                                Availability(
                                    day_of_week=days_of_week_map[day_name],
                                    from_time=from_time_str,
                                    to_time=to_time_str,
                                    doctor_id=target_doctor.id
                                )
                            )
                    db.session.add_all(imported_availabilities)
                    db.session.commit()
                else:
                    flash(f'Row {row_num}: Failed to identify or create a doctor object for processing availability.',
                          'danger')
                    error_count += 1
                    db.session.rollback()
                    continue

            except Exception as e:
                db.session.rollback()
                display_name = f"{doctor_data.get('first_name', '')} {doctor_data.get('last_name', '')}" if doctor_data.get(
                    'first_name') else 'Unknown Doctor'
                email_info = doctor_data.get('email', 'N/A')
                flash(f'Row {row_num}: Error processing data for "{display_name}" (Email: {email_info}): {str(e)}',
                      'danger')
                error_count += 1
                traceback.print_exc()

        flash(f'Doctor import completed: {success_count} successful, {error_count} failed.',
              'success' if success_count > 0 else 'warning')

    except Exception as e:
        flash(f'Error processing file: {str(e)}. Ensure it is a valid Excel file and follows the sample structure.',
              'danger')
        traceback.print_exc()

    return redirect(ADMIN + DOCTOR_LIST)
