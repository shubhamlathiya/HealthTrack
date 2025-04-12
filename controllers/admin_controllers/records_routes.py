from datetime import datetime

from flask import render_template, request, flash, redirect, make_response

from controllers.admin_controllers import admin
from controllers.constant.adminPathConstant import RECORDS_DEATH, RECORDS_BIRTH, RECORDS_ADD_BIRTH, ADMIN, \
    RECORDS_BIRTH_DELETE, RECORDS_BIRTH_EDIT, RECORDS_BIRTH_MEDICAL_VISIT, RECORDS_BIRTH_MEDICAL_VISIT_DELETE, \
    RESTORE_RECORDS_BIRTH, RESTORE_BIRTH_MEDICAL_VISIT
from models.childBirthRecordesModel import ChildCase, MedicalVisit
from models.doctorModel import Doctor
from utils.config import db
from fpdf import FPDF


@admin.route(RECORDS_DEATH, methods=['GET'], endpoint='records_death')
def records_death():
    return render_template("admin_templates/records/death_records.html")


@admin.route(RECORDS_BIRTH, methods=['GET'], endpoint='records_birth')
def records_birth():
    deleted_child_cases = ChildCase.query.filter_by(is_active=False).all()
    deleted_medical_visits = MedicalVisit.query.filter_by(is_active=False).all()

    cases = ChildCase.query.filter_by(is_active=1).order_by(ChildCase.created_at.desc()).all()

    doctors = Doctor.query.filter_by(is_active=1).order_by(Doctor.first_name).all()
    return render_template("admin_templates/records/birth_records.html",
                           cases=cases,
                           doctors=doctors,
                           deleted_child_cases=deleted_child_cases,
                           deleted_medical_visits=deleted_medical_visits)


@admin.route(RECORDS_ADD_BIRTH, methods=['GET', 'POST'])
def add_child_case():
    if request.method == 'POST':
        try:
            # Generate case number
            last_case = ChildCase.query.order_by(ChildCase.id.desc()).first()
            case_number = f"{int(last_case.id) + 1000 if last_case else 1000}"

            case = ChildCase(
                case_number=case_number,
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                gender=request.form['gender'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date(),
                address=request.form['address'],
                mother_name=request.form['mother_name'],
                father_name=request.form['father_name'],
                contact_number=request.form['contact_number'],
                case_notes=request.form.get('case_notes', ''),
                status=request.form.get('status', 'Active')
            )
            db.session.add(case)
            db.session.commit()
            flash('Child case added successfully!', 'success')
            return redirect(ADMIN + RECORDS_BIRTH)
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding child case: {str(e)}', 'danger')
            return redirect(ADMIN + RECORDS_ADD_BIRTH)

    return render_template("admin_templates/records/add_birth_records.html")


@admin.route(RECORDS_BIRTH_EDIT + '/<int:id>', methods=['POST'])
def edit_child_case(id):
    case = ChildCase.query.get_or_404(id)

    try:
        case.first_name = request.form['first_name']
        case.last_name = request.form['last_name']
        case.gender = request.form['gender']
        case.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        case.address = request.form['address']
        case.mother_name = request.form['mother_name']
        case.father_name = request.form['father_name']
        case.contact_number = request.form['contact_number']
        case.case_notes = request.form.get('case_notes', '')
        case.status = request.form.get('status', 'Active')
        db.session.commit()
        flash('Child case updated successfully!', 'success')
        return redirect(ADMIN + RECORDS_BIRTH)
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating child case: {str(e)}', 'danger')
        return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RECORDS_BIRTH_DELETE + '/<int:id>', methods=['POST'])
def delete_child_case(id):
    case = ChildCase.query.get_or_404(id)

    try:
        # First soft delete all related medical visits
        MedicalVisit.query.filter_by(child_case_id=id).update({
            'is_active': False,
            'deleted_at': datetime.utcnow()
        })

        # Then soft delete the child case
        case.is_active = False
        case.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Child case and all related medical data have been archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving child case: {str(e)}', 'danger')

    return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RECORDS_BIRTH_MEDICAL_VISIT + '/<int:case_id>/add-visit', methods=['POST'])
def add_medical_visit(case_id):
    try:
        print(request.form.get("visit_date"))
        visit = MedicalVisit(
            child_case_id=case_id,
            visit_date=datetime.strptime(request.form.get("visit_date"), '%Y-%m-%d').date(),
            visit_type=request.form.get('visit_type'),
            height=request.form.get('height'),
            weight=request.form.get('weight'),
            notes=request.form.get('notes'),
            doctor_id=request.form.get('doctor_id')
        )
        db.session.add(visit)
        db.session.commit()
        flash('Medical visit added successfully!', 'success')
        return redirect(ADMIN + RECORDS_BIRTH)
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding medical visit: {str(e)}', 'danger')
        return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RECORDS_BIRTH_MEDICAL_VISIT + '/<int:visit_id>/edit', methods=['POST'])
def edit_medical_visit(visit_id):
    try:
        visit = MedicalVisit.query.get_or_404(visit_id)

        # Validate required fields
        if not request.form.get("visit_date") or not request.form.get("visit_type"):
            flash('Visit date and type are required', 'danger')
            return redirect(ADMIN + RECORDS_BIRTH)

        visit.visit_date = datetime.strptime(request.form.get("visit_date"), '%Y-%m-%d').date()
        visit.visit_type = request.form.get('visit_type')
        visit.height = float(request.form.get('height')) if request.form.get('height') else None
        visit.weight = float(request.form.get('weight')) if request.form.get('weight') else None
        visit.notes = request.form.get('notes')
        visit.doctor_id = int(request.form.get('doctor_id')) if request.form.get('doctor_id') else None
        visit.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Medical visit updated successfully!', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid data format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating medical visit: {str(e)}', 'danger')

    return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RECORDS_BIRTH_MEDICAL_VISIT_DELETE + '/<int:visit_id>', methods=['POST'])
def delete_medical_visit(visit_id):
    visit = MedicalVisit.query.get_or_404(visit_id)
    try:
        # Soft delete the medical visit
        visit.is_active = False
        visit.deleted_at = datetime.utcnow()

        db.session.commit()
        flash('Medical visit has been archived successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error archiving medical visit: {str(e)}', 'danger')

    return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RECORDS_BIRTH + '/<int:id>/certificate', methods=['GET'])
def child_case_certificate(id):
    case = ChildCase.query.get_or_404(id)

    # Calculate age
    today = datetime.now().date()
    age = today.year - case.birth_date.year - ((today.month, today.day) < (case.birth_date.month, case.birth_date.day))

    # Create PDF
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'HOSPITAL NAME', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Hospital Address, City, State, Zip', 0, 1, 'C')
    pdf.cell(0, 10, 'Phone: (123) 456-7890 | Email: info@hospital.com', 0, 1, 'C')
    pdf.ln(10)

    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'CHILD BIRTH CERTIFICATE', 0, 1, 'C')
    pdf.ln(10)

    # Content
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'This is to certify that {case.first_name} {case.last_name},', 0, 1)
    pdf.cell(0, 10, f'child of {case.mother_name} (Mother) and {case.father_name} (Father),', 0, 1)
    pdf.cell(0, 10, f'was born on {case.birth_date.strftime("%B %d, %Y")} at our hospital.', 0, 1)
    pdf.ln(5)
    pdf.cell(0, 10, f'Current Age: {age} years', 0, 1)
    pdf.ln(10)

    # Footer
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, 'Certificate issued on: ' + datetime.now().strftime("%B %d, %Y"), 0, 1)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Authorized Signature', 0, 1, 'R')
    pdf.ln(15)
    pdf.cell(0, 10, '_________________________', 0, 1, 'R')
    pdf.cell(0, 10, 'Hospital Administrator', 0, 1, 'R')

    # Output
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers.set('Content-Disposition', 'attachment', filename=f'birth_certificate_{case.case_number}.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response


@admin.route(RESTORE_RECORDS_BIRTH + '/<int:id>', methods=['POST'])
def restore_child_case(id):
    case = ChildCase.query.get_or_404(id)
    try:
        # Restore related visits
        MedicalVisit.query.filter_by(child_case_id=id).update({
            'is_active': True,
            'deleted_at': None
        })

        ChildCase.query.filter_by(id=id).update({
            'is_active': True,
            'deleted_at': None
        })

        db.session.commit()
        flash('Child case and all related medical data have been restored!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring child case: {str(e)}', 'danger')

    return redirect(ADMIN + RECORDS_BIRTH)


@admin.route(RESTORE_BIRTH_MEDICAL_VISIT + '/<int:id>', methods=['POST'])
def restore_medical_visit(id):
    visit = MedicalVisit.query.filter_by(id=id, is_active=False).first_or_404()
    try:
        visit.is_active = True
        visit.deleted_at = None
        db.session.commit()
        flash('Medical visit restored successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error restoring medical visit: {str(e)}', 'danger')

    return redirect(ADMIN + RECORDS_BIRTH)
