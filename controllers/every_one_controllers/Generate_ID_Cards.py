import base64

from flask import render_template, send_file

from controllers.every_one_controllers import idCard
from middleware.auth_middleware import token_required
from models.doctorModel import Doctor


def generate_barcode_image(code):
    import barcode
    from barcode.writer import ImageWriter
    import io

    # Ensure the code is numeric and 12 digits long for EAN13
    code = code.zfill(12)

    # Custom writer configuration to remove ALL text
    class NoTextWriter(ImageWriter):
        def _paint_text(self, xpos, ypos):
            # Override to completely skip text rendering
            pass

    writer = NoTextWriter()
    writer.set_options({
        'write_text': False,
        'quiet_zone': 2,
        'module_width': 0.2,
        'module_height': 15.0,
        'background': 'white',
        'foreground': 'black',
        'font_size': 0,
        'text_distance': 0,  # Remove space reserved for text
    })

    ean = barcode.get('ean13', code, writer=writer)

    # Generate the barcode image in-memory
    buffer = io.BytesIO()
    ean.write(buffer)
    buffer.seek(0)

    return buffer

@idCard.route("/patient", methods=["GET"], endpoint="idCard")
def patientCard():
    return render_template("id_card_templates/doctor_id_card.html")


@idCard.route("/doctor", methods=["GET"], endpoint="doctorIdCard")
@token_required
def doctorCard(current_user):
    doctors = Doctor.query.filter_by(user_id=current_user).first()

    if not doctors:
        return "Doctor record not found for this user.", 404

    # Generate barcode image buffer
    buffer = generate_barcode_image(str(doctors.id))

    # Encode image as base64 string
    barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template("id_card_templates/doctor_id_card.html",
                           doctors=doctors,
                           barcode_base64=barcode_base64)