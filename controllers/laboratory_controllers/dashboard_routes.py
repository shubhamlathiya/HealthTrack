from flask import render_template


from controllers.laboratory_controllers import laboratory


@laboratory.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template("laboratory_templates/laboratory_dashboard_templets.html")
