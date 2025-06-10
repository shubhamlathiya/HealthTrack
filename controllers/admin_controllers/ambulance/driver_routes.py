import io
import traceback  # Import traceback for detailed error logging
from datetime import datetime

import pandas as pd
from flask import redirect, request, render_template, flash, jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_DRIVER_LIST, \
    AMBULANCE_ADD_DRIVER, ADMIN, AMBULANCE_EDIT_DRIVER, AMBULANCE_DELETE_DRIVER, AMBULANCE_RESTORE_DRIVER, \
    AMBULANCE_TOGGLE_STATUS_DRIVER, AMBULANCE_EXPORT_DRIVERS, AMBULANCE_IMPORT_DRIVERS, AMBULANCE_IMPORT_DRIVERS_SAMPLE
from middleware.auth_middleware import token_required  # Import the token_required middleware
# Assuming your models are correctly imported here
from models.ambulanceModel import Driver, Ambulance
from models.userModel import UserRole  # Import UserRole
from utils.config import db
from utils.util_fincation import allowed_file


# --- Driver List Route ---
@admin.route(AMBULANCE_DRIVER_LIST, methods=['GET'], endpoint='driver-list')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def driver_list(current_user):  # Added current_user parameter
    drivers = Driver.query.filter_by(is_deleted=0).order_by(Driver.name).all()
    deleted_drivers = Driver.query.filter_by(is_deleted=1).order_by(Driver.name).all()

    return render_template("admin_templates/ambulance/driver-list.html",
                           drivers=drivers,
                           deleted_drivers=deleted_drivers,
                           datetime=datetime,
                           ADMIN=ADMIN,
                           AMBULANCE_ADD_DRIVER=AMBULANCE_ADD_DRIVER,
                           AMBULANCE_EDIT_DRIVER=AMBULANCE_EDIT_DRIVER,
                           AMBULANCE_DELETE_DRIVER=AMBULANCE_DELETE_DRIVER,
                           AMBULANCE_RESTORE_DRIVER=AMBULANCE_RESTORE_DRIVER,
                           AMBULANCE_TOGGLE_STATUS_DRIVER=AMBULANCE_TOGGLE_STATUS_DRIVER,
                           AMBULANCE_EXPORT_DRIVERS=AMBULANCE_EXPORT_DRIVERS,
                           AMBULANCE_IMPORT_DRIVERS=AMBULANCE_IMPORT_DRIVERS,
                           AMBULANCE_IMPORT_DRIVERS_SAMPLE=AMBULANCE_IMPORT_DRIVERS_SAMPLE)


# --- Add Driver Route ---
@admin.route(AMBULANCE_ADD_DRIVER, methods=['POST'], endpoint='add-driver')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def add_driver(current_user):  # Added current_user parameter
    required_fields = {
        'name': 'Full Name',
        'license_number': 'License Number',
        'contact': 'Contact Number',
        'address': 'Address'
    }

    # Validate required fields
    missing_fields = [field_name for field, field_name in required_fields.items() if not request.form.get(field)]
    if missing_fields:
        flash(f'Missing required fields: {", ".join(missing_fields)}', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    try:
        # Check for duplicate license number (case-insensitive, for non-deleted drivers)
        license_number = request.form.get('license_number').strip().upper()
        if Driver.query.filter(Driver.license_number.ilike(license_number), Driver.is_deleted == False).first():
            flash('Driver with this license number already exists.', 'danger')
            return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

        # Parse dates safely
        date_of_birth_str = request.form.get('date_of_birth')
        date_of_birth = datetime.strptime(date_of_birth_str,
                                          '%Y-%m-%d').date() if date_of_birth_str else None  # Changed to .date() for consistency with model

        license_expiry_str = request.form.get('license_expiry')
        license_expiry = datetime.strptime(license_expiry_str,
                                           '%Y-%m-%d').date() if license_expiry_str else None  # Changed to .date() for consistency with model

        # Create new driver instance
        new_driver = Driver(
            name=request.form.get('name').strip(),
            license_number=license_number,
            contact=request.form.get('contact').strip(),
            address=request.form.get('address').strip(),
            date_of_birth=date_of_birth,
            gender=request.form.get('gender'),
            license_expiry=license_expiry,
            emergency_contact=request.form.get('emergency_contact', '').strip(),
            blood_group=request.form.get('blood_group', '').upper(),
            is_active=True  # New drivers are active by default
        )

        db.session.add(new_driver)
        db.session.commit()
        flash('Driver added successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid date format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'An unexpected error occurred while adding driver: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- Edit Driver Route ---
@admin.route(AMBULANCE_EDIT_DRIVER + '/<int:id>', methods=['POST'], endpoint='edit-driver')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def edit_driver(current_user, id):  # Added current_user parameter
    driver = Driver.query.get_or_404(id)  # Get driver by ID, or return 404 if not found

    try:
        # Check for duplicate license number (excluding the current driver and non-deleted ones)
        license_number = request.form.get('license_number').strip().upper()
        existing = Driver.query.filter(
            Driver.license_number.ilike(license_number),
            Driver.id != id,
            Driver.is_deleted == False
        ).first()

        if existing:
            flash('Another driver with this license number already exists.', 'danger')
            return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

        # Update driver details
        driver.name = request.form.get('name').strip()
        driver.license_number = license_number
        driver.contact = request.form.get('contact').strip()
        driver.address = request.form.get('address').strip()

        # Parse dates safely, allowing them to be set to None if input is empty
        driver.date_of_birth = datetime.strptime(request.form.get('date_of_birth'),
                                                 '%Y-%m-%d').date() if request.form.get(  # Changed to .date()
            'date_of_birth') else None
        driver.gender = request.form.get('gender')
        driver.license_expiry = datetime.strptime(request.form.get('license_expiry'),
                                                  '%Y-%m-%d').date() if request.form.get(  # Changed to .date()
            'license_expiry') else None

        driver.emergency_contact = request.form.get('emergency_contact', '').strip()
        driver.blood_group = request.form.get('blood_group', '').upper()
        # 'is_active' checkbox: 'on' if checked, None/empty string if not. Convert to boolean.
        driver.is_active = request.form.get('is_active', 'off') == 'on'

        db.session.commit()
        flash('Driver updated successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid date format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'An unexpected error occurred while updating driver: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- Soft Delete Driver Route ---
@admin.route(AMBULANCE_DELETE_DRIVER + '/<int:id>', methods=['POST'], endpoint='delete-driver')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def delete_driver(current_user, id):  # Added current_user parameter
    driver = Driver.query.get_or_404(id)
    try:
        # Prevent deletion if driver is assigned to any active ambulance
        assigned_ambulances = Ambulance.query.filter_by(driver_id=id, is_deleted=False).all()
        if assigned_ambulances:
            ambulance_numbers = ", ".join([a.vehicle_number for a in assigned_ambulances])
            flash(f'Cannot delete driver: Currently assigned to ambulances {ambulance_numbers}.', 'danger')
            return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

        driver.is_deleted = True
        driver.deleted_at = datetime.utcnow()  # Set the deletion timestamp
        driver.is_active = False  # Deactivate driver when marked as deleted
        db.session.commit()
        flash('Driver deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'Error deleting driver: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- Restore Driver Route ---
@admin.route(AMBULANCE_RESTORE_DRIVER + '/<int:id>', methods=['POST'], endpoint='restore-driver')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def restore_driver(current_user, id):  # Added current_user parameter
    driver = Driver.query.get_or_404(id)
    try:
        driver.is_deleted = False
        driver.deleted_at = None  # Clear deletion timestamp
        driver.is_active = True  # Reactivate driver when restored
        db.session.commit()
        flash('Driver restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'Error restoring driver: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- Toggle Driver Status Route ---
@admin.route(AMBULANCE_TOGGLE_STATUS_DRIVER + '/<int:id>', methods=['POST'], endpoint='toggle-driver-status')
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def toggle_driver_status(current_user, id):  # Added current_user parameter
    driver = Driver.query.get_or_404(id)
    try:
        driver.is_active = not driver.is_active  # Invert the current status
        db.session.commit()
        status_msg = "activated" if driver.is_active else "deactivated"
        flash(f'Driver {status_msg} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # Print full traceback to console for debugging
        flash(f'Error toggling driver status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- Get Driver Details for Modals/AJAX (GET request) ---
@admin.route('/get-driver-details/<int:id>', methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def get_driver_details(current_user, id):  # Added current_user parameter
    driver = Driver.query.get_or_404(id)
    return jsonify({
        'id': driver.id,
        'name': driver.name,
        'license_number': driver.license_number,
        'contact': driver.contact,
        'address': driver.address,
        'date_of_birth': driver.date_of_birth.strftime('%Y-%m-%d') if driver.date_of_birth else None,
        'gender': driver.gender,
        'license_expiry': driver.license_expiry.strftime('%Y-%m-%d') if driver.license_expiry else None,
        'emergency_contact': driver.emergency_contact,
        'blood_group': driver.blood_group,
        'is_active': driver.is_active
    })


# --- Check License Number Duplication (AJAX) ---
@admin.route('/check-license-number', methods=['POST'])
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Added token_required
def check_license_number(current_user):  # Added current_user parameter
    license_number = request.form.get('license_number', '').strip().upper()
    exclude_id = request.form.get('exclude_id')  # ID to exclude during edit checks

    query = Driver.query.filter(Driver.license_number.ilike(license_number), Driver.is_deleted == False)
    if exclude_id:
        query = query.filter(Driver.id != int(exclude_id))

    exists = query.first() is not None
    return jsonify({'exists': exists})


@admin.route(AMBULANCE_EXPORT_DRIVERS + '/<format>', methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Uncommented and applied token_required
def export_drivers(current_user, format):  # Added current_user parameter
    # Fetch all non-deleted drivers
    drivers = Driver.query.filter_by(is_deleted=False).order_by(Driver.name).all()

    # Prepare data for pandas DataFrame
    data = []
    for driver in drivers:
        data.append({
            'ID': driver.id,
            'Name': driver.name,
            'License Number': driver.license_number,
            'Contact': driver.contact,
            'Address': driver.address,
            'Date of Birth': driver.date_of_birth.strftime('%Y-%m-%d') if driver.date_of_birth else '',
            'Gender': driver.gender if driver.gender else '',
            'Emergency Contact': driver.emergency_contact if driver.emergency_contact else '',
            'Blood Group': driver.blood_group if driver.blood_group else '',
            'License Expiry': driver.license_expiry.strftime('%Y-%m-%d') if driver.license_expiry else '',
            'Is Active': 'Yes' if driver.is_active else 'No',
            'Created At': driver.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Updated At': driver.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ambulance_drivers_export_{current_time}.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ambulance Drivers')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ambulance_drivers_export_{current_time}.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()

        # Custom styles for table content
        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 8
        normal_style.leading = 9

        # Title
        title_text = "Ambulance Drivers Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        # Add header row
        header_row = [Paragraph(col, styles['h3']) for col in df.columns.tolist()]
        pdf_data.append(header_row)

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        # Calculate table dimensions and column widths
        PAGE_WIDTH, PAGE_HEIGHT = A4  # A4 is generally better for tables than letter
        LEFT_MARGIN = 0.5 * inch
        RIGHT_MARGIN = 0.5 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        # Assign approximate column widths. Adjust these percentages based on your data's typical length.
        # Ensure the sum of percentages is 1.0 (or close, within reason for rounding)
        # Or, calculate more dynamically if needed.
        # Example: 14 columns
        col_widths = [
            0.05 * AVAILABLE_WIDTH,  # ID
            0.15 * AVAILABLE_WIDTH,  # Name
            0.10 * AVAILABLE_WIDTH,  # License Number
            0.10 * AVAILABLE_WIDTH,  # Contact
            0.15 * AVAILABLE_WIDTH,  # Address
            0.08 * AVAILABLE_WIDTH,  # Date of Birth
            0.06 * AVAILABLE_WIDTH,  # Gender
            0.10 * AVAILABLE_WIDTH,  # Emergency Contact
            0.06 * AVAILABLE_WIDTH,  # Blood Group
            0.08 * AVAILABLE_WIDTH,  # License Expiry
            0.08 * AVAILABLE_WIDTH,  # Joining Date
            0.05 * AVAILABLE_WIDTH,  # Is Active
            0.10 * AVAILABLE_WIDTH,  # Created At
            0.10 * AVAILABLE_WIDTH,  # Updated At
            # 0.10 * AVAILABLE_WIDTH, # Deleted At (if included)
        ]
        # Sum of current col_widths: 1.21. Adjust to sum to 1.0, or let ReportLab scale if needed
        # Better: calculate based on number of columns
        num_columns = len(df.columns)
        if len(col_widths) != num_columns:  # Fallback for robustness
            col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Create table with calculated column widths
        table = Table(pdf_data, colWidths=col_widths)

        # Table Style
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90E2')),  # Blue header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),  # Light grey for data rows
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Finer grid lines
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ambulance_drivers_export_{current_time}.pdf'
        )

    flash('Invalid export format. Please choose csv, excel, or pdf.', 'danger')
    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)


# --- New: Sample Excel File Structure for Import ---
SAMPLE_DRIVERS_EXCEL_STRUCTURE = [
    {
        "Name": "John Doe",
        "License Number": "DL-12345",
        "Contact": "9876543210",
        "Address": "123 Main St, Anytown",
        "Date of Birth (YYYY-MM-DD)": "1985-01-15",
        "Gender": "Male",
        "Emergency Contact": "9988776655",
        "Blood Group": "A+",
        "License Expiry (YYYY-MM-DD)": "2028-12-31",
        "Joining Date (YYYY-MM-DD)": "2020-05-01"
    },
    {
        "Name": "Jane Smith",
        "License Number": "DL-67890",
        "Contact": "1234567890",
        "Address": "456 Oak Ave, Somewhere",
        "Date of Birth (YYYY-MM-DD)": "1990-07-22",
        "Gender": "Female",
        "Emergency Contact": "1122334455",
        "Blood Group": "B-",
        "License Expiry (YYYY-MM-DD)": "2027-03-20",
        "Joining Date (YYYY-MM-DD)": "2021-11-10"
    }
]


# --- New: Download Sample Import File for Drivers ---
@admin.route(AMBULANCE_IMPORT_DRIVERS_SAMPLE, methods=['GET'])
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Uncommented and applied token_required
def download_sample_drivers_import_file(current_user):  # Added current_user parameter
    df = pd.DataFrame(SAMPLE_DRIVERS_EXCEL_STRUCTURE)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Drivers Data')

        # Add instructions sheet
        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING AMBULANCE DRIVERS:",
            "",
            "1. Enter your driver data in the 'Drivers Data' sheet.",
            "2. Required columns: 'Name', 'License Number', 'Contact', 'Address'.",
            "3. Optional columns: 'Date of Birth (YYYY-MM-DD)', 'Gender', 'Emergency Contact', 'Blood Group', 'License Expiry (YYYY-MM-DD)', 'Joining Date (YYYY-MM-DD)'.",
            "4. Dates must be in YYYY-MM-DD format (e.g., 2023-01-01).",
            "5. 'License Number' is used to identify existing drivers for updates. Case-insensitive.",
            "6. Do not modify the column headers.",
            "7. Remove these instructions sheet before importing if you face issues (optional).",
            "8. Save the file as .xlsx format."
        ]
        for row_idx, line in enumerate(instructions):
            worksheet.write(row_idx, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_ambulance_drivers.xlsx'
    )


# --- New: Import Drivers Functionality (Excel) ---
@admin.route(AMBULANCE_IMPORT_DRIVERS, methods=['POST'], endpoint="import_drivers")
@token_required(allowed_roles=[UserRole.ADMIN.name])  # Uncommented and applied token_required
def import_drivers(current_user):  # Added current_user parameter
    if 'file' not in request.files:
        flash('No file selected for import.', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    if not allowed_file(file.filename):
        flash('Invalid file type. Only Excel (.xlsx, .xls) and CSV (.csv) files are allowed.', 'danger')
        return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

    try:
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            df = pd.read_csv(stream)
        else:  # Assume Excel
            df = pd.read_excel(file)

        # Normalize column names for robust matching (e.g., 'License Number' -> 'licensenumber')
        df.columns = df.columns.str.lower().str.replace('[^a-z0-9]+', '',
                                                        regex=True)  # Converts "License Number (YYYY-MM-DD)" to "licensenumberyyyymmdd"

        # Map to model attributes (case-insensitive and normalized)
        # Using a more robust mapping for flexible column names from user input
        column_map = {
            'name': 'name',
            'licensenumber': 'license_number',
            'contact': 'contact',
            'address': 'address',
            'dateofbirthyyyymmdd': 'date_of_birth',
            'gender': 'gender',
            'emergencycontact': 'emergency_contact',
            'bloodgroup': 'blood_group',
            'licenseexpiryyyyymmdd': 'license_expiry',
        }
        df.rename(columns=column_map, inplace=True)

        required_columns = ['name', 'license_number', 'contact', 'address']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing one or more required columns: {", ".join(missing)}. Please check the template.', 'danger')
            return redirect(ADMIN + AMBULANCE_DRIVER_LIST)

        success_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        # Iterate through rows and process each driver
        for row_idx, row_series in df.iterrows():
            row_data = row_series.to_dict()
            # Ensure required fields are not NaN/empty
            if not row_data.get('name') or pd.isna(row_data.get('name')) or \
                    not row_data.get('license_number') or pd.isna(row_data.get('license_number')) or \
                    not row_data.get('contact') or pd.isna(row_data.get('contact')) or \
                    not row_data.get('address') or pd.isna(row_data.get('address')):
                errors.append(
                    f"Row {row_idx + 2}: Missing essential data (Name, License Number, Contact, Address). Skipping.")
                skipped_count += 1
                continue

            try:
                license_number_val = str(row_data['license_number']).strip().upper()

                # Try to find existing driver (case-insensitive on license number)
                driver = Driver.query.filter(
                    Driver.license_number.ilike(license_number_val),
                    Driver.is_deleted == False
                ).first()

                # Prepare date fields
                date_of_birth = None
                if row_data.get('date_of_birth'):
                    try:
                        # Ensure conversion to date object
                        date_of_birth = pd.to_datetime(row_data['date_of_birth']).date()
                    except ValueError:
                        errors.append(
                            f"Row {row_idx + 2}: Invalid 'Date of Birth' format '{row_data['date_of_birth']}'. Expected YYYY-MM-DD.")
                        skipped_count += 1
                        continue

                license_expiry = None
                if row_data.get('license_expiry'):
                    try:
                        # Ensure conversion to date object
                        license_expiry = pd.to_datetime(row_data['license_expiry']).date()
                    except ValueError:
                        errors.append(
                            f"Row {row_idx + 2}: Invalid 'License Expiry' format '{row_data['license_expiry']}'. Expected YYYY-MM-DD.")
                        skipped_count += 1
                        continue

                if driver:
                    # Update existing driver
                    driver.name = str(row_data.get('name', driver.name)).strip()
                    driver.contact = str(row_data.get('contact', driver.contact)).strip()
                    driver.address = str(row_data.get('address', driver.address)).strip()
                    driver.date_of_birth = date_of_birth
                    driver.gender = str(row_data.get('gender', driver.gender)).strip() if row_data.get(
                        'gender') else driver.gender
                    driver.emergency_contact = str(
                        row_data.get('emergency_contact', driver.emergency_contact)).strip() if row_data.get(
                        'emergency_contact') else driver.emergency_contact
                    driver.blood_group = str(
                        row_data.get('blood_group', driver.blood_group)).strip().upper() if row_data.get(
                        'blood_group') else driver.blood_group
                    driver.license_expiry = license_expiry

                    # is_active and is_deleted status are typically managed via specific UI actions, not bulk import for existing records.
                    db.session.add(driver)
                    updated_count += 1
                else:
                    # Create new driver
                    new_driver = Driver(
                        name=str(row_data['name']).strip(),
                        license_number=license_number_val,
                        contact=str(row_data['contact']).strip(),
                        address=str(row_data['address']).strip(),
                        date_of_birth=date_of_birth,
                        gender=str(row_data.get('gender', '')).strip() if row_data.get('gender') else None,
                        emergency_contact=str(row_data.get('emergency_contact', '')).strip() if row_data.get(
                            'emergency_contact') else None,
                        blood_group=str(row_data.get('blood_group', '')).strip().upper() if row_data.get(
                            'blood_group') else None,
                        license_expiry=license_expiry,
                        is_active=True,
                        is_deleted=False
                    )
                    db.session.add(new_driver)
                    success_count += 1

                db.session.commit()  # Commit each row to ensure atomicity for that record
            except Exception as e:
                db.session.rollback()  # Rollback changes for the current record on error
                traceback.print_exc()  # Print full traceback for specific row error
                errors.append(
                    f"Row {row_idx + 2}: Error processing driver '{row_data.get('name', license_number_val)}' - {str(e)}")
                skipped_count += 1

        # Final flash message summarizing import
        if success_count > 0 or updated_count > 0:
            flash(f'Import completed! Added: {success_count}, Updated: {updated_count}, Skipped: {skipped_count}.',
                  'success')
        else:
            flash(f'Import completed with no new or updated records. Skipped: {skipped_count}.', 'info')

        if errors:
            flash('Some rows had errors during import. Please review the messages below:', 'warning')
            for error_msg in errors:
                flash(error_msg, 'warning')  # Flash individual errors

    except pd.errors.EmptyDataError:
        flash('The uploaded file is empty.', 'danger')
    except pd.errors.ParserError:
        flash('Could not parse the file. Please check its format.', 'danger')
    except Exception as e:
        db.session.rollback()  # Rollback any pending transactions in case of a general error
        traceback.print_exc()  # Print full traceback for general file processing error
        flash(f'An unexpected error occurred during import: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_DRIVER_LIST)
