import io
from datetime import datetime, timedelta

import pandas as pd
from flask import render_template, request, redirect, flash, jsonify, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import AMBULANCE_LIST, ADMIN, AMBULANCE_ADD, AMBULANCE_EDIT, \
    AMBULANCE_DELETE, AMBULANCE_RESTORE, AMBULANCE_TOGGLE_STATUS, AMBULANCE_EXPORT, AMBULANCE_IMPORT, \
    AMBULANCE_IMPORT_SAMPLE
from models.ambulanceModel import Ambulance, Driver
from utils.config import db
from utils.util_fincation import allowed_file


@admin.route(AMBULANCE_LIST, methods=['GET'], endpoint='ambulance-list')
def ambulance_list():
    ambulances = Ambulance.query.filter_by(is_deleted=0).order_by(Ambulance.vehicle_name).all()
    drivers = Driver.query.filter_by(is_active=True, is_deleted=0).all()
    deleted_ambulances = Ambulance.query.filter_by(is_deleted=1).all()

    vehicle_types = db.session.query(Ambulance.vehicle_type.distinct()).filter_by(is_deleted=False).all()
    vehicle_types = [t[0] for t in vehicle_types]

    return render_template("admin_templates/ambulance/ambulance-list.html",
                           ambulances=ambulances,
                           current_year=datetime.today().year,
                           drivers=drivers,
                           deleted_ambulances=deleted_ambulances,
                           vehicle_types=vehicle_types,
                           datetime=datetime,
                           timedelta=timedelta,
                           ADMIN=ADMIN,
                           AMBULANCE_ADD=AMBULANCE_ADD,
                           AMBULANCE_EDIT=AMBULANCE_EDIT,
                           AMBULANCE_DELETE=AMBULANCE_DELETE,
                           AMBULANCE_RESTORE=AMBULANCE_RESTORE,
                           AMBULANCE_TOGGLE_STATUS=AMBULANCE_TOGGLE_STATUS,
                           AMBULANCE_EXPORT=AMBULANCE_EXPORT,
                           AMBULANCE_IMPORT=AMBULANCE_IMPORT,
                           AMBULANCE_IMPORT_SAMPLE=AMBULANCE_IMPORT_SAMPLE
                           )


@admin.route(AMBULANCE_ADD, methods=['POST'], endpoint='add-ambulance')
def ambulance_operations():
    # Validate required fields
    required_fields = {
        'vehicle_number': 'Vehicle Number',
        'vehicle_name': 'Vehicle Name',
        'year_made': 'Year Made',
        'vehicle_type': 'Vehicle Type',
        'base_rate': 'Base Rate',
        # 'per_km_rate' is removed as it's not in the Ambulance model
    }

    missing_fields = [field_name for field, field_name in required_fields.items() if not request.form.get(field)]
    if missing_fields:
        flash(f'Missing required fields: {", ".join(missing_fields)}', 'danger')
        return redirect(ADMIN + AMBULANCE_LIST)

    try:
        # Check for duplicate vehicle number
        vehicle_number = request.form.get('vehicle_number').strip().upper()
        if Ambulance.query.filter(Ambulance.vehicle_number.ilike(vehicle_number),
                                  Ambulance.is_deleted == False).first():
            flash('Ambulance with this vehicle number already exists', 'danger')
            return redirect(ADMIN + AMBULANCE_LIST)

        insurance_expiry_str = request.form.get('insurance_expiry')
        insurance_expiry = datetime.strptime(insurance_expiry_str, '%Y-%m-%d').date() if insurance_expiry_str else None

        # Create new ambulance
        new_ambulance = Ambulance(
            vehicle_number=vehicle_number,
            vehicle_name=request.form.get('vehicle_name').strip(),
            year_made=int(request.form.get('year_made')),
            vehicle_type=request.form.get('vehicle_type'),
            base_rate=float(request.form.get('base_rate')),
            # per_km_rate is removed
            driver_id=request.form.get('driver_id') or None,
            is_available=request.form.get('is_available', 'off') == 'on',
            facilities=request.form.get('facilities', ''),
            registration_number=request.form.get('registration_number', ''),
            insurance_number=request.form.get('insurance_number', ''),
            insurance_expiry=insurance_expiry
        )

        db.session.add(new_ambulance)
        db.session.commit()
        flash('Ambulance added successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid input format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding ambulance: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_LIST)


@admin.route(AMBULANCE_EDIT + '/<int:id>', methods=['POST'], endpoint='edit-ambulance')
def edit_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)

    try:
        # Check for duplicate vehicle number (excluding current record)
        vehicle_number = request.form.get('vehicle_number').strip().upper()
        existing = Ambulance.query.filter(
            Ambulance.vehicle_number.ilike(vehicle_number),
            Ambulance.id != id,
            Ambulance.is_deleted == False
        ).first()

        if existing:
            flash('Ambulance with this vehicle number already exists', 'danger')
            return redirect(ADMIN + AMBULANCE_LIST)

        insurance_expiry_str = request.form.get('insurance_expiry')
        insurance_expiry = datetime.strptime(insurance_expiry_str, '%Y-%m-%d').date() if insurance_expiry_str else None

        # Update ambulance details
        ambulance.vehicle_number = vehicle_number
        ambulance.vehicle_name = request.form.get('vehicle_name').strip()
        ambulance.year_made = int(request.form.get('year_made'))
        ambulance.vehicle_type = request.form.get('vehicle_type')
        ambulance.base_rate = float(request.form.get('base_rate'))
        # per_km_rate is removed
        ambulance.driver_id = request.form.get('driver_id') or None
        ambulance.is_available = request.form.get('is_available', 'off') == 'on'
        ambulance.is_active = request.form.get('is_active', 'off') == 'on'
        ambulance.facilities = request.form.get('facilities', '')
        ambulance.registration_number = request.form.get('registration_number', '')
        ambulance.insurance_number = request.form.get('insurance_number', '')
        ambulance.insurance_expiry = insurance_expiry

        db.session.commit()
        flash('Ambulance updated successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid input format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating ambulance: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_LIST)


@admin.route(AMBULANCE_DELETE + '/<int:id>', methods=['POST'], endpoint='delete-ambulance')
def delete_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        # Check if ambulance is assigned to any active calls
        # This assumes 'calls' relationship is defined in Ambulance model or you query AmbulanceCall directly
        if hasattr(ambulance, 'calls'):
            active_calls = [call for call in ambulance.calls if call.status in ['Pending', 'Dispatched', 'In Progress']]
            if active_calls:
                flash('Cannot delete ambulance assigned to active calls', 'danger')
                return redirect(ADMIN + AMBULANCE_LIST)

        ambulance.deleted_at = datetime.utcnow()
        ambulance.is_deleted = True
        ambulance.is_available = False
        ambulance.is_active = False
        db.session.commit()
        flash('Ambulance deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ambulance: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_LIST)


@admin.route(AMBULANCE_RESTORE + '/<int:id>', methods=['POST'], endpoint='restore-ambulance')
def restore_ambulance(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        ambulance.deleted_at = None
        ambulance.is_deleted = False
        ambulance.is_active = True
        db.session.commit()
        flash('Ambulance restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring ambulance: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_LIST)


@admin.route(AMBULANCE_TOGGLE_STATUS + '/<int:id>', methods=['POST'], endpoint='toggle-ambulance-status')
def toggle_ambulance_status(id):
    ambulance = Ambulance.query.get_or_404(id)
    try:
        ambulance.is_active = not ambulance.is_active
        if not ambulance.is_active:
            ambulance.is_available = False
        db.session.commit()
        status = "activated" if ambulance.is_active else "deactivated"
        flash(f'Ambulance {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling ambulance status: {str(e)}', 'danger')
    return redirect(ADMIN + AMBULANCE_LIST)


@admin.route('/get-ambulance-details/<int:id>', methods=['GET'])
def get_ambulance_details(id):
    ambulance = Ambulance.query.get_or_404(id)
    return jsonify({
        'id': ambulance.id,
        'vehicle_number': ambulance.vehicle_number,
        'vehicle_name': ambulance.vehicle_name,
        'year_made': ambulance.year_made,
        'vehicle_type': ambulance.vehicle_type,
        'base_rate': ambulance.base_rate,
        'driver_id': ambulance.driver_id,
        'is_available': ambulance.is_available,
        'facilities': ambulance.facilities,
        'registration_number': ambulance.registration_number,
        'insurance_number': ambulance.insurance_number,
        'insurance_expiry': ambulance.insurance_expiry.strftime('%Y-%m-%d') if ambulance.insurance_expiry else None,
        'is_active': ambulance.is_active
    })


@admin.route(AMBULANCE_EXPORT + '/<format>', methods=['GET'])
def export_ambulances(format):
    ambulances = Ambulance.query.filter_by(is_deleted=False).order_by(Ambulance.vehicle_name).all()

    data = []
    for ambulance in ambulances:
        driver_name = ambulance.driver.name if ambulance.driver else 'N/A'
        data.append({
            'ID': ambulance.id,
            'Vehicle Number': ambulance.vehicle_number,
            'Vehicle Name': ambulance.vehicle_name,
            'Year Made': ambulance.year_made,
            'Vehicle Type': ambulance.vehicle_type,
            'Base Rate': ambulance.base_rate,
            'Assigned Driver': driver_name,
            'Registration Number': ambulance.registration_number if ambulance.registration_number else '',
            'Insurance Number': ambulance.insurance_number if ambulance.insurance_number else '',
            'Insurance Expiry': ambulance.insurance_expiry.strftime('%Y-%m-%d') if ambulance.insurance_expiry else '',
            'Facilities': ambulance.facilities if ambulance.facilities else '',
            'Is Available': 'Yes' if ambulance.is_available else 'No',
            'Is Active': 'Yes' if ambulance.is_active else 'No',
            'Created At': ambulance.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Updated At': ambulance.updated_at.strftime('%Y-%m-%d %H:%M:%S')
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
            download_name=f'ambulances_export_{current_time}.csv'
        )

    elif format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Ambulances')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ambulances_export_{current_time}.xlsx'
        )

    elif format == 'pdf':
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()

        normal_style = styles['Normal']
        normal_style.fontName = 'Helvetica'
        normal_style.fontSize = 7
        normal_style.leading = 8

        title_text = "Ambulances Report"
        title = Paragraph(title_text, styles['Title'])

        pdf_data = []
        header_row = [Paragraph(col, styles['h3']) for col in df.columns.tolist()]
        pdf_data.append(header_row)

        for index, row in df.iterrows():
            row_data = []
            for col_name in df.columns:
                cell_content = str(row[col_name])
                row_data.append(Paragraph(cell_content, normal_style))
            pdf_data.append(row_data)

        PAGE_WIDTH, PAGE_HEIGHT = A4
        LEFT_MARGIN = 0.5 * inch
        RIGHT_MARGIN = 0.5 * inch
        AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

        num_columns = len(df.columns)
        col_widths = [
            0.04 * AVAILABLE_WIDTH,
            0.10 * AVAILABLE_WIDTH,
            0.12 * AVAILABLE_WIDTH,
            0.06 * AVAILABLE_WIDTH,
            0.08 * AVAILABLE_WIDTH,
            0.07 * AVAILABLE_WIDTH,
            0.08 * AVAILABLE_WIDTH,
            0.10 * AVAILABLE_WIDTH,
            0.10 * AVAILABLE_WIDTH,
            0.08 * AVAILABLE_WIDTH,
            0.12 * AVAILABLE_WIDTH,
            0.05 * AVAILABLE_WIDTH,
            0.05 * AVAILABLE_WIDTH,
            0.08 * AVAILABLE_WIDTH,
            0.08 * AVAILABLE_WIDTH,
        ]

        if len(col_widths) != num_columns:
            col_widths = [AVAILABLE_WIDTH / num_columns] * num_columns

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
                                topMargin=0.75 * inch, bottomMargin=0.75 * inch)

        elements = []
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        table = Table(pdf_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'ambulances_export_{current_time}.pdf'
        )

    flash('Invalid export format. Please choose csv, excel, or pdf.', 'danger')
    return redirect(ADMIN + AMBULANCE_LIST)


SAMPLE_AMBULANCES_EXCEL_STRUCTURE = [
    {
        "Vehicle Number": "AMB001",
        "Vehicle Name": "LifeSaver 1",
        "Year Made": 2020,
        "Vehicle Type": "Advanced",
        "Base Rate": 500.00,
        "Driver License Number (Optional)": "DL-12345",
        "Registration Number": "GJ05AB1234",
        "Insurance Number": "INS-AMB-001",
        "Insurance Expiry (YYYY-MM-DD)": "2026-06-30",
        "Facilities": "Oxygen, Defibrillator, Basic First Aid Kit",
        "Is Available (Yes/No)": "Yes"
    },
    {
        "Vehicle Number": "AMB002",
        "Vehicle Name": "Rapid Response",
        "Year Made": 2018,
        "Vehicle Type": "Basic",
        "Base Rate": 300.00,
        "Driver License Number (Optional)": "",
        "Registration Number": "GJ06CD5678",
        "Insurance Number": "INS-AMB-002",
        "Insurance Expiry (YYYY-MM-DD)": "2025-12-31",
        "Facilities": "Basic First Aid Kit",
        "Is Available (Yes/No)": "No"
    }
]


@admin.route(AMBULANCE_IMPORT_SAMPLE, methods=['GET'])
def download_sample_ambulances_import_file():
    df = pd.DataFrame(SAMPLE_AMBULANCES_EXCEL_STRUCTURE)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ambulances Data')

        workbook = writer.book
        worksheet = workbook.add_worksheet('Instructions')
        instructions = [
            "INSTRUCTIONS FOR IMPORTING AMBULANCES:",
            "",
            "1. Enter your ambulance data in the 'Ambulances Data' sheet.",
            "2. Required columns: 'Vehicle Number', 'Vehicle Name', 'Year Made', 'Vehicle Type', 'Base Rate'.",
            "3. Optional columns: 'Driver License Number (Optional)', 'Registration Number', 'Insurance Number', 'Insurance Expiry (YYYY-MM-DD)', 'Facilities', 'Is Available (Yes/No)'.",
            "4. Dates must be in YYYY-MM-DD format (e.g., 2023-01-01).",
            "5. 'Vehicle Number' is used to identify existing ambulances for updates. Case-insensitive.",
            "6. 'Driver License Number (Optional)' links to an existing driver. If the driver is not found, the ambulance will be imported/updated without a driver.",
            "7. 'Is Available (Yes/No)' should be 'Yes' or 'No'. Defaults to 'Yes' if empty.",
            "8. Do not modify the column headers.",
            "9. Remove this instructions sheet before importing if you face issues (optional).",
            "10. Save the file as .xlsx format."
        ]
        for row_idx, line in enumerate(instructions):
            worksheet.write(row_idx, 0, line)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='sample_import_ambulances.xlsx'
    )


@admin.route(AMBULANCE_IMPORT, methods=['POST'], endpoint="import_ambulances")
def import_ambulances():
    if 'file' not in request.files:
        flash('No file selected for import.', 'danger')
        return redirect(ADMIN + AMBULANCE_LIST)

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(ADMIN + AMBULANCE_LIST)

    if not allowed_file(file.filename):
        flash('Invalid file type. Only Excel (.xlsx, .xls) and CSV (.csv) files are allowed.', 'danger')
        return redirect(ADMIN + AMBULANCE_LIST)

    try:
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            df = pd.read_csv(stream)
        else:
            df = pd.read_excel(file)

        df.columns = df.columns.str.lower().str.replace('[^a-z0-9]+', '', regex=True)

        column_map = {
            'vehiclenumber': 'vehicle_number',
            'vehiclename': 'vehicle_name',
            'yearmade': 'year_made',
            'vehicletype': 'vehicle_type',
            'baserate': 'base_rate',
            'driverlicensenumberoptional': 'driver_license_number',
            'registrationnumber': 'registration_number',
            'insurancenumber': 'insurance_number',
            'insuranceexpiryyyyymmdd': 'insurance_expiry',
            'facilities': 'facilities',
            'isavailableyesno': 'is_available_str'
        }
        df.rename(columns=column_map, inplace=True)

        required_columns = ['vehicle_number', 'vehicle_name', 'year_made', 'vehicle_type', 'base_rate']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            flash(f'Missing one or more required columns: {", ".join(missing)}. Please check the template.', 'danger')
            return redirect(ADMIN + AMBULANCE_LIST)

        success_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for row_idx, row_series in df.iterrows():
            row_data = row_series.to_dict()

            if not row_data.get('vehicle_number') or pd.isna(row_data.get('vehicle_number')) or \
                    not row_data.get('vehicle_name') or pd.isna(row_data.get('vehicle_name')) or \
                    not row_data.get('year_made') or pd.isna(row_data.get('year_made')) or \
                    not row_data.get('vehicle_type') or pd.isna(row_data.get('vehicle_type')) or \
                    not row_data.get('base_rate') or pd.isna(row_data.get('base_rate')):
                errors.append(
                    f"Row {row_idx + 2}: Missing essential data (Vehicle Number, Name, Year, Type, Rate). Skipping.")
                skipped_count += 1
                continue

            try:
                vehicle_number_val = str(row_data['vehicle_number']).strip().upper()

                ambulance = Ambulance.query.filter(
                    Ambulance.vehicle_number.ilike(vehicle_number_val),
                    Ambulance.is_deleted == False
                ).first()

                driver_id = None
                driver_license_number = str(row_data.get('driver_license_number', '')).strip().upper()
                if driver_license_number:
                    driver = Driver.query.filter(
                        Driver.license_number.ilike(driver_license_number),
                        Driver.is_deleted == False,
                        Driver.is_active == True
                    ).first()
                    if driver:
                        driver_id = driver.id
                    else:
                        errors.append(
                            f"Row {row_idx + 2}: Driver with license '{driver_license_number}' not found or inactive. Ambulance will be imported/updated without a driver.")

                insurance_expiry = None
                if row_data.get('insurance_expiry'):
                    try:
                        insurance_expiry = pd.to_datetime(row_data['insurance_expiry']).date()
                    except ValueError:
                        errors.append(
                            f"Row {row_idx + 2}: Invalid 'Insurance Expiry' format '{row_data['insurance_expiry']}'. Expected YYYY-MM-DD.")

                is_available = True
                if 'is_available_str' in row_data and pd.notna(row_data['is_available_str']):
                    is_available_str_lower = str(row_data['is_available_str']).strip().lower()
                    if is_available_str_lower in ['no', 'false', '0']:
                        is_available = False
                    elif is_available_str_lower in ['yes', 'true', '1']:
                        is_available = True
                    else:
                        errors.append(
                            f"Row {row_idx + 2}: Invalid 'Is Available' value '{row_data['is_available_str']}'. Defaulting to 'Yes'.")

                if ambulance:
                    ambulance.vehicle_name = str(row_data.get('vehicle_name', ambulance.vehicle_name)).strip()
                    ambulance.year_made = int(row_data.get('year_made', ambulance.year_made))
                    ambulance.vehicle_type = str(row_data.get('vehicle_type', ambulance.vehicle_type)).strip()
                    ambulance.base_rate = float(row_data.get('base_rate', ambulance.base_rate))
                    ambulance.driver_id = driver_id
                    ambulance.registration_number = str(
                        row_data.get('registration_number', ambulance.registration_number)).strip()
                    ambulance.insurance_number = str(
                        row_data.get('insurance_number', ambulance.insurance_number)).strip()
                    ambulance.insurance_expiry = insurance_expiry
                    ambulance.facilities = str(row_data.get('facilities', ambulance.facilities)).strip()
                    ambulance.is_available = is_available

                    db.session.add(ambulance)
                    updated_count += 1
                else:
                    new_ambulance = Ambulance(
                        vehicle_number=vehicle_number_val,
                        vehicle_name=str(row_data['vehicle_name']).strip(),
                        year_made=int(row_data['year_made']),
                        vehicle_type=str(row_data['vehicle_type']).strip(),
                        base_rate=float(row_data['base_rate']),
                        driver_id=driver_id,
                        registration_number=str(row_data.get('registration_number', '')).strip(),
                        insurance_number=str(row_data.get('insurance_number', '')).strip(),
                        insurance_expiry=insurance_expiry,
                        facilities=str(row_data.get('facilities', '')).strip(),
                        is_available=is_available,
                        is_active=True,
                        is_deleted=False
                    )
                    db.session.add(new_ambulance)
                    success_count += 1

                db.session.commit()
            except ValueError as ve:
                db.session.rollback()
                errors.append(
                    f"Row {row_idx + 2}: Data conversion error for '{row_data.get('vehicle_number', 'N/A')}' - {str(ve)}")
                skipped_count += 1
            except Exception as e:
                db.session.rollback()
                errors.append(
                    f"Row {row_idx + 2}: Error processing ambulance '{row_data.get('vehicle_number', 'N/A')}' - {str(e)}")
                skipped_count += 1

        if success_count > 0 or updated_count > 0:
            flash(f'Import completed! Added: {success_count}, Updated: {updated_count}, Skipped: {skipped_count}.',
                  'success')
        else:
            flash(f'Import completed with no new or updated records. Skipped: {skipped_count}.', 'info')

        if errors:
            flash('Some rows had errors during import. Please review the messages below:', 'warning')
            for error_msg in errors:
                flash(error_msg, 'warning')

    except pd.errors.EmptyDataError:
        flash('The uploaded file is empty.', 'danger')
    except pd.errors.ParserError:
        flash('Could not parse the file. Please check its format.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'An unexpected error occurred during import: {str(e)}', 'danger')

    return redirect(ADMIN + AMBULANCE_LIST)
