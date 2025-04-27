from datetime import datetime

from flask import render_template, request, flash, redirect, make_response, jsonify

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import RECORDS_DEATH, ADMIN, \
    RECORDS_DEATH_DELETE, RECORDS_DEATH_EDIT, \
    RECORDS_ADD_DEATH, RECORDS_DEATH_CERTIFICATE, RECORDS_RESTORE_DEATH
from middleware.auth_middleware import token_required
from models.deathRecordeModel import DeathRecord
from models.doctorModel import Doctor
from utils.config import db
from fpdf import FPDF

from utils.email_utils import send_email_with_attachment


@admin.route(RECORDS_DEATH, methods=['GET'], endpoint='records_death')
@token_required
def records_death(current_user):
    records = DeathRecord.query.filter_by(is_deleted=0).order_by(DeathRecord.death_date.desc()).all()
    doctors = Doctor.query.filter_by(is_deleted=0).order_by(Doctor.first_name).all()
    deleted_records = DeathRecord.query.filter_by(is_deleted=1).order_by(DeathRecord.deleted_at.desc()).all()
    return render_template("admin_templates/records/death_records.html",
                           records=records,
                           doctors=doctors,
                           deleted_records=deleted_records,
                           ADMIN=ADMIN,
                           RECORDS_ADD_DEATH=RECORDS_ADD_DEATH,
                           RECORDS_DEATH_EDIT=RECORDS_DEATH_EDIT,
                           RECORDS_DEATH_DELETE=RECORDS_DEATH_DELETE,
                           RECORDS_RESTORE_DEATH=RECORDS_RESTORE_DEATH,
                           RECORDS_DEATH_CERTIFICATE=RECORDS_DEATH_CERTIFICATE
                           )


@admin.route(RECORDS_ADD_DEATH, methods=['GET', 'POST'])
@token_required
def add_death_record(current_user):
    doctors = Doctor.query.filter_by(is_deleted=0).order_by(Doctor.first_name).all()
    if request.method == 'POST':
        try:
            last_case = DeathRecord.query.order_by(DeathRecord.id.desc()).first()
            case_number = f"{int(last_case.id) + 1000 if last_case else 1000}"
            # Create new death record
            record = DeathRecord(
                case_number=case_number,
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                gender=request.form.get('gender'),
                birth_date=datetime.strptime(request.form.get('birth_date'), '%Y-%m-%d').date() if request.form.get(
                    'birth_date') else None,
                death_date=datetime.strptime(request.form.get('death_date'), '%Y-%m-%d').date(),
                death_time=datetime.strptime(request.form.get('death_time'), '%H:%M').time() if request.form.get(
                    'death_time') else None,
                address=request.form.get('address'),
                cause_of_death=request.form.get('cause_of_death'),
                email=request.form.get("email"),
                guardian_name=request.form.get('guardian_name'),
                relationship=request.form.get("relationship"),
                place_of_death=request.form.get("place_of_death"),
                contact_number=request.form.get('contact_number'),
                pronounced_by=request.form.get('pronounced_by'),
                notes=request.form.get('notes')
            )
            db.session.add(record)
            db.session.commit()
            flash('Death record added successfully!', 'success')
            return redirect(ADMIN + RECORDS_DEATH)
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding death record: {str(e)}', 'danger')
    return render_template('admin_templates/records/add_death_record.html', doctors=doctors,
                           ADMIN=ADMIN,
                           RECORDS_ADD_DEATH=RECORDS_ADD_DEATH,
                           )


@admin.route(RECORDS_DEATH_EDIT + '/<int:id>', methods=['POST'])
@token_required
def edit_death_record(current_user, id):
    record = DeathRecord.query.get_or_404(id)
    try:
        record.first_name = request.form.get('first_name')
        record.last_name = request.form.get('last_name')
        record.gender = request.form.get('gender')
        record.birth_date = datetime.strptime(request.form.get('birth_date'),
                                              '%Y-%m-%d').date() if request.form.get('birth_date') else None
        record.death_date = datetime.strptime(request.form.get('death_date'), '%Y-%m-%d').date()
        record.death_time = datetime.strptime(request.form.get('death_time'), '%H:%M').time() if request.form.get(
            'death_time') else None
        record.address = request.form.get('address')
        record.cause_of_death = request.form.get('cause_of_death')
        record.email = request.form.get("email")
        record.relationship = request.form.get("relationship")
        record.place_of_death = request.form.get("place_of_death")
        record.guardian_name = request.form.get('guardian_name')
        record.contact_number = request.form.get('contact_number')
        record.pronounced_by = request.form.get('pronounced_by')
        record.notes = request.form.get('notes')
        record.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Death record updated successfully!', 'success')
        return redirect(ADMIN + RECORDS_DEATH)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating death record: {str(e)}', 'danger')


@admin.route(RECORDS_DEATH_DELETE + '/<int:id>', methods=['POST'])
@token_required
def delete_death_record(current_user, id):
    record = DeathRecord.query.get_or_404(id)
    try:
        # Soft delete
        record.is_deleted = True
        record.deleted_at = datetime.utcnow()
        db.session.commit()
        flash('Death record has been archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving death record: {str(e)}', 'danger')
    return redirect(ADMIN + RECORDS_DEATH)


@admin.route(RECORDS_RESTORE_DEATH + '/<int:id>', methods=['POST'])
@token_required
def restore_death_record(current_user, id):
    record = DeathRecord.query.filter_by(id=id, is_deleted=True).first_or_404()
    try:
        record.is_deleted = False
        record.deleted_at = None
        db.session.commit()
        flash('Death record restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring death record: {str(e)}', 'danger')
    return redirect(ADMIN + RECORDS_DEATH)


def generate_death_certificate_pdf(record):
    """Generate PDF death certificate for a given death record."""
    pdf = FPDF()
    pdf.add_page()

    # Set document properties
    pdf.set_title(f"Death Certificate - {record.first_name} {record.last_name}")
    pdf.set_author("Hospital Management System")
    pdf.set_creator("Hospital Management System")

    # Header with hospital information
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'HOSPITAL NAME', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Hospital Address, City, State, Zip', 0, 1, 'C')
    pdf.cell(0, 10, 'Phone: (123) 456-7890 | Email: info@hospital.com', 0, 1, 'C')
    pdf.ln(15)

    # Certificate title with border
    pdf.set_font('Arial', 'B', 18)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 12, 'OFFICIAL DEATH CERTIFICATE', 0, 1, 'C', True)
    pdf.ln(10)

    # Deceased information section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DECEASED INFORMATION', 'B', 1)
    pdf.set_font('Arial', '', 12)

    # Create a table-like structure for deceased info
    col_width = 90
    row_height = 8
    line_height = 6

    # Row 1: Name and Gender
    pdf.cell(col_width, row_height, f"Full Name: {record.first_name} {record.last_name}", 0, 0)
    pdf.cell(col_width, row_height, f"Gender: {record.gender}", 0, 1)

    # Row 2: Birth Date and Age
    birth_date = record.birth_date.strftime('%B %d, %Y') if record.birth_date else 'N/A'
    pdf.cell(col_width, row_height, f"Date of Birth: {birth_date}", 0, 0)

    if record.birth_date and record.death_date:
        age = record.death_date.year - record.birth_date.year
        if (record.death_date.month, record.death_date.day) < (record.birth_date.month, record.birth_date.day):
            age -= 1
        pdf.cell(col_width, row_height, f"Age at Death: {age} years", 0, 1)
    else:
        pdf.cell(col_width, row_height, "Age at Death: N/A", 0, 1)

    # Row 3: Address
    pdf.cell(0, row_height, f"Address: {record.address or 'N/A'}", 0, 1)
    pdf.ln(5)

    # Death details section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DEATH DETAILS', 'B', 1)
    pdf.set_font('Arial', '', 12)

    # Row 1: Date and Time of Death
    death_date = record.death_date.strftime('%B %d, %Y') if record.death_date else 'N/A'
    death_time = record.death_time.strftime('%I:%M %p') if record.death_time else 'N/A'
    pdf.cell(col_width, row_height, f"Date of Death: {death_date}", 0, 0)
    pdf.cell(col_width, row_height, f"Time of Death: {death_time}", 0, 1)

    # Row 2: Case Number and Place of Death
    pdf.cell(col_width, row_height, f"Case Number: {record.case_number}", 0, 0)
    pdf.cell(col_width, row_height, f"Place of Death: {record.place_of_death or 'Hospital'}", 0, 1)
    pdf.ln(5)

    # Cause of Death with multi-cell for long text
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, row_height, "Primary Cause of Death:", 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, line_height, record.cause_of_death or 'Not specified', 0, 1)

    pdf.ln(5)

    # Pronouncing physician section
    if record.doctor:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'PRONOUNCED BY', 'B', 1)
        pdf.set_font('Arial', '', 12)

        # Doctor information
        pdf.cell(col_width, row_height, f"Dr. {record.doctor.first_name} {record.doctor.last_name}", 0, 0)
        # pdf.cell(col_width, row_height, f"License: {record.doctor.license_number or 'N/A'}", 0, 1)
        # pdf.cell(0, row_height, f"Specialty: {record.doctor.specialization or 'N/A'}", 0, 1)
        pdf.ln(5)

    # Next of kin section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'NEXT OF KIN', 'B', 1)
    pdf.set_font('Arial', '', 12)

    # Kin information
    pdf.cell(col_width, row_height, f"Name: {record.guardian_name or 'N/A'}", 0, 0)
    pdf.cell(col_width, row_height, f"Relationship: {record.relationship or 'N/A'}", 0, 1)
    pdf.cell(col_width, row_height, f"Contact: {record.contact_number or 'N/A'}", 0, 0)
    pdf.cell(col_width, row_height, f"Address: {record.address or 'N/A'}", 0, 1)
    pdf.ln(10)

    # Certification section
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Certificate generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', 0, 1, 'C')
    pdf.ln(10)

    # Signature lines with space for actual signatures
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Authorized Signatures', 0, 1, 'C')
    pdf.ln(8)

    # Create two signature areas
    pdf.cell(95, 10, '_________________________', 0, 0, 'C')
    pdf.cell(95, 10, '_________________________', 0, 1, 'C')
    pdf.cell(95, 5, 'Attending Physician', 0, 0, 'C')
    pdf.cell(95, 5, 'Hospital Administrator', 0, 1, 'C')
    pdf.ln(15)

    # Official stamp notice
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 8,
                   'NOTE: This document becomes valid only when accompanied by the official hospital seal and signatures. '
                   'Unauthorized duplication or alteration of this certificate is prohibited by law.',
                   0, 'C')

    # Add page border
    pdf.set_draw_color(150, 150, 150)
    pdf.rect(5, 5, 200, 287)

    return pdf


@admin.route(RECORDS_DEATH_CERTIFICATE + '/<int:id>', methods=['GET'])
def death_certificate(id):
    record = DeathRecord.query.get_or_404(id)
    pdf = generate_death_certificate_pdf(record)

    # Output for download
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'death_certificate_{record.case_number}.pdf')
    response.headers.set('Content-Type', 'application/pdf')

    # Update certificate issued status
    record.death_certificate_issued = True
    record.certificate_issue_date = datetime.utcnow()
    db.session.commit()

    return response


@admin.route(RECORDS_DEATH_CERTIFICATE + '/send-email/<int:id>', methods=['GET'])
def send_death_certificate_email(id):
    record = DeathRecord.query.get_or_404(id)

    # Get email from request
    recipient_email = record.email
    if not recipient_email:
        return jsonify({"success": False, "message": "Email address is required"}), 400

    # Generate PDF
    pdf = generate_death_certificate_pdf(record)
    pdf_data = pdf.output(dest='S').encode('latin1')

    # Prepare email content
    subject = f"Death Certificate for {record.first_name} {record.last_name}"
    body_html = render_template("email_templates/templates/death_certificate_mail.html",
                                record=record)

    # Send email with attachment
    filename = f"death_certificate_{record.case_number}.pdf"
    success = send_email_with_attachment(subject, recipient_email, body_html, pdf_data, filename)

    if success:
        # Update certificate issued status
        record.death_certificate_issued = True
        record.certificate_issue_date = datetime.utcnow()
        db.session.commit()

        flash("Death certificate has been sent via email successfully!", 'success')
    else:
        flash("Failed to send email with death certificate", 'danger')
    return redirect(ADMIN + RECORDS_DEATH)
