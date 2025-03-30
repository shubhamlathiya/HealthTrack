from flask import render_template

from controllers.patients_controllers import patients


@patients.route('/dashboard' , methods=['GET'])
def dashboard():
    return render_template("patient/patient_dashboard_templets.html")